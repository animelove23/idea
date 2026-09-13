import copy
import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from decomposition.config import APIConfig
from decomposition.v6.schema import fold_document
from evaluation.alignment import align_entities, align_facts, PairAligner
from evaluation.common import ContractError, JsonStage, StageFailure, document_context
from evaluation.coverage import CoverageAudit, apply_coverage
from evaluation.run import prepare, execute
from evaluation.verifier import PendingVerifier, pending_claims


def doc(color="white"):
    text = f"A {color} cup is on a table."
    elements = [
        dict(category="object", fact="There is a cup.", source="cup"),
        dict(category="object", fact="There is a table.", source="table"),
        dict(category="color", fact=f"The cup is {color}.", source=f"{color} cup"),
        dict(category="spatial", fact="The cup is on the table.", source=text)]
    return fold_document({"elements": [{**e, "assertion": "asserted", "polarity": "positive"} for e in elements]}, text, color)


def entity_response():
    return {"original_entities": [{"id": "o1", "mention": "cup", "fact_ids": ["f1", "f3", "f4"], "description": "cup"},
                                  {"id": "o2", "mention": "table", "fact_ids": ["f2", "f4"], "description": "table"}],
            "steer_entities": [{"id": "s1", "mention": "cup", "fact_ids": ["f1", "f3", "f4"], "description": "cup"},
                               {"id": "s2", "mention": "table", "fact_ids": ["f2", "f4"], "description": "table"}],
            "entity_alignment": [{"original_entity_ids": ["o1"], "steer_entity_ids": ["s1"], "status": "matched", "reason": "same cup by table"},
                                 {"original_entity_ids": ["o2"], "steer_entity_ids": ["s2"], "status": "matched", "reason": "same supporting table"}]}


def fact_response(modified=False):
    def bindings(prefix):
        return [{"fact_id": "f1", "entity_ids": [prefix+"1"], "slot": "existence"},
                {"fact_id": "f2", "entity_ids": [prefix+"2"], "slot": "existence"},
                {"fact_id": "f3", "entity_ids": [prefix+"1"], "slot": "color"},
                {"fact_id": "f4", "entity_ids": [prefix+"1", prefix+"2"], "slot": "on"}]
    return {"original_bindings": bindings("o"), "steer_bindings": bindings("s"),
            "fact_alignment": [{"original_fact_ids": [f"f{i}"], "steer_fact_ids": [f"f{i}"],
                                "status": "modified" if modified and i == 3 else "retained",
                                "reason": "value_changed" if modified and i == 3 else "same_fact", "evidence": []} for i in range(1, 5)]}


class EvaluationTests(unittest.TestCase):
    def test_coverage_adds_only_missing_atomic_attribute(self):
        original = doc(); original["facts"] = [f for f in original["facts"] if f["id"] != "f3"]
        before = copy.deepcopy(original)
        added = dict(category="color", fact="The cup is white.", source="white cup", assertion="asserted", polarity="positive")
        result = apply_coverage(original, {"added_elements": [added]})
        self.assertEqual(original, before)
        self.assertEqual(result["augmented_document"]["facts"][:-1], before["facts"])
        self.assertEqual(result["added_facts"][0]["id"], "cov_f1")
        self.assertTrue(result["added_facts"][0]["added_by_coverage"])
        self.assertNotIn("entities", result["augmented_document"])

    def test_coverage_cannot_replace_delete_or_merge_existing_facts(self):
        for key in ["facts", "patches", "entities"]:
            with self.assertRaises(ContractError): apply_coverage(doc(), {"added_elements": [], key: []})

    def test_no_additions_keeps_document_byte_semantics(self):
        original = doc()
        self.assertEqual(apply_coverage(original, {"added_elements": []})["augmented_document"], original)

    def test_bad_addition_retained_as_rejection_not_existing_fact_change(self):
        addition = dict(category="color", fact="The cup is blue.", source="blue", assertion="asserted", polarity="positive")
        original = doc(); result = apply_coverage(original, {"added_elements": [addition]})
        self.assertEqual(result["status"], "needs_review")
        self.assertEqual(result["augmented_document"], original)
        self.assertEqual(len(result["rejected_additions"]), 1)

    def test_exact_duplicate_addition_rejected_without_deleting_original(self):
        original = doc(); fact = original["facts"][2]
        addition = {k: fact[k] for k in ["category", "fact", "source", "assertion", "polarity"]}
        result = apply_coverage(original, {"added_elements": [addition]})
        self.assertEqual(result["added_facts"], [])
        self.assertEqual(result["augmented_document"], original)

    def test_coverage_id_collision_avoided(self):
        original = doc(); original["facts"][0]["id"] = "cov_f1"
        original["facts"] = [f for f in original["facts"] if f["id"] != "f3"]
        new = dict(category="color", fact="The cup is white.", source="white", assertion="asserted", polarity="positive")
        self.assertEqual(apply_coverage(original, {"added_elements": [new]})["added_facts"][0]["id"], "cov_f2")

    def test_coverage_receives_only_one_caption_and_runs_once(self):
        class Fake:
            def __init__(self): self.calls = []
            def run(self, name, payload):
                self.calls.append((name, payload))
                return {"added_elements": []}, {"api_calls": 1}
        fake = Fake(); CoverageAudit(fake).run(doc())
        self.assertEqual(len(fake.calls), 1)
        self.assertEqual(set(fake.calls[0][1]), {"text", "facts"})

    def test_shared_global_entity_ids_generated_by_program(self):
        sidecar = align_entities(entity_response(), doc(), doc("blue"))
        self.assertEqual(sidecar["global_mapping"]["original"]["o1"], sidecar["global_mapping"]["steer"]["s1"])
        self.assertNotEqual(sidecar["global_mapping"]["original"]["o1"], sidecar["global_mapping"]["steer"]["s2"])

    def test_uncertain_entities_are_not_force_matched(self):
        response = entity_response(); response["entity_alignment"][0]["status"] = "ambiguous"
        sidecar = align_entities(response, doc(), doc())
        self.assertIsNone(sidecar["global_mapping"]["original"]["o1"])
        result = align_facts(fact_response(), doc(), doc(), sidecar)
        self.assertTrue(all(row["status"] == "ambiguous" for row in result["fact_alignment"] if "f3" in row["original_fact_ids"]))

    def test_duplicate_entity_record_is_not_a_second_match(self):
        response = entity_response(); response["entity_alignment"].append(copy.deepcopy(response["entity_alignment"][0]))
        result=align_entities(response,doc(),doc())
        self.assertEqual(len(result['entity_alignment']),2)
        self.assertEqual(result['resolution_notes'][0]['rule'],'duplicate_entity_correspondence')

    def test_same_slot_color_change_is_modified(self):
        original, steer = doc(), doc("blue"); sidecar = align_entities(entity_response(), original, steer)
        result = align_facts(fact_response(True), original, steer, sidecar)
        self.assertEqual(result["status"], "ready")
        self.assertEqual(Counter(r["status"] for r in result["fact_alignment"]), {"retained": 3, "modified": 1})

    def test_wrong_free_form_slot_does_not_override_explicit_color_category(self):
        original, steer = doc(), doc("blue"); sidecar = align_entities(entity_response(), original, steer)
        response = fact_response(True); response["steer_bindings"][2]["slot"] = "age"
        result = align_facts(response, original, steer, sidecar)
        self.assertEqual(result["status"], "ready")
        self.assertTrue(any(r["status"] == "modified" for r in result["fact_alignment"]))

    def test_retained_does_not_allow_changed_polarity(self):
        original, steer = doc(), doc(); steer["facts"][2]["polarity"] = "negative"
        result = align_facts(fact_response(), original, steer, align_entities(entity_response(), original, steer))
        self.assertEqual(result["status"], "needs_review")

    def test_extraction_gap_is_ambiguous_with_opposite_evidence(self):
        original, steer = doc(), doc(); steer["facts"] = [f for f in steer["facts"] if f["id"] != "f3"]
        ent = entity_response(); ent["steer_entities"][0]["fact_ids"].remove("f3")
        sidecar = align_entities(ent, original, steer)
        response = fact_response(); response["steer_bindings"].pop(2)
        response["fact_alignment"][2] = {"original_fact_ids": ["f3"], "steer_fact_ids": [], "status": "ambiguous", "reason": "extraction_gap", "evidence": [{"side": "steer", "quote": "white cup"}]}
        result = align_facts(response, original, steer, sidecar)
        self.assertEqual(result["status"], "ready")
        self.assertEqual(next(r for r in result['fact_alignment'] if 'f3' in r['original_fact_ids'])['reason'], "extraction_gap")
        self.assertFalse(any(r["status"] == "removed" for r in result["fact_alignment"]))

    def test_gap_without_opposite_quote_is_rejected(self):
        response = fact_response(); response["fact_alignment"][2].update(status="ambiguous", reason="extraction_gap")
        result = align_facts(response, doc(), doc(), align_entities(entity_response(), doc(), doc()))
        self.assertEqual(result["status"], "needs_review")

    def test_every_fact_assigned_once_even_when_model_omits_rows(self):
        response = fact_response(); response["fact_alignment"].pop(2)
        result = align_facts(response, doc(), doc(), align_entities(entity_response(), doc(), doc()))
        for side in ["original", "steer"]:
            counts = Counter(f for r in result["fact_alignment"] for f in r[side+"_fact_ids"])
            self.assertEqual(counts, {"f1": 1, "f2": 1, "f3": 1, "f4": 1})
        self.assertTrue(all(r["status"] == "ambiguous" for r in result["fact_alignment"] if "f3" in r["original_fact_ids"]))

    def test_duplicate_alignment_does_not_count_twice(self):
        response = fact_response(); response["fact_alignment"].append(copy.deepcopy(response["fact_alignment"][0]))
        result = align_facts(response, doc(), doc(), align_entities(entity_response(), doc(), doc()))
        self.assertEqual(sum("f1" in r["original_fact_ids"] for r in result["fact_alignment"]), 1)
        self.assertEqual(result["status"], "ready")
        self.assertTrue(any(n['rule']=='duplicate_output_record' for n in result['resolution_notes']))

    def test_removed_added_only_for_one_sided_facts(self):
        response = fact_response(); response["fact_alignment"][2:3] = [
            {"original_fact_ids": ["f3"], "steer_fact_ids": [], "status": "removed", "reason": "not_expressed", "evidence": []},
            {"original_fact_ids": [], "steer_fact_ids": ["f3"], "status": "added", "reason": "not_expressed", "evidence": []}]
        result = align_facts(response, doc(), doc("blue"), align_entities(entity_response(), doc(), doc("blue")))
        self.assertEqual({r["status"] for r in result["fact_alignment"]}, {"retained", "removed", "added"})

    def test_truth_and_method_metadata_never_enter_alignment_payload(self):
        a, b = doc(), doc(); a.update(image="private.png", method="VISTA", hallucination_score=1)
        for f in a["facts"]: f.update(verification="supported", evidence="image evidence")
        self.assertEqual(document_context(a), document_context(b))

    def test_verifier_is_only_pending_and_modified_claims_stay_separate(self):
        result = pending_claims("pair", doc(), doc("blue"))
        self.assertEqual(len(result), 8)
        self.assertTrue(all(r["label"] == "pending" and r["evidence"] is None for r in result))
        self.assertEqual(len({r["claim_id"] for r in result}), 8)

    def test_model_json_stage_has_no_retry_and_thinking_disabled(self):
        calls = []
        def transport(body):
            calls.append(copy.deepcopy(body))
            return {"choices": [{"finish_reason": "stop", "message": {"content": "broken"}}]}
        stage = JsonStage(APIConfig("test", "placeholder"), transport)
        with self.assertRaises(StageFailure): stage.run("coverage", document_context(doc()))
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["thinking"], {"type": "disabled"})
        self.assertIn("json", calls[0]["messages"][0]["content"].lower())

    def test_http_failure_records_status_without_response_body_or_key(self):
        from urllib.error import HTTPError
        def transport(body):
            raise HTTPError("https://api.deepseek.com/chat/completions", 400, "sensitive body", {}, None)
        stage = JsonStage(APIConfig("test", "SECRET_SENTINEL"), transport)
        with self.assertRaises(StageFailure) as captured:
            stage.run("coverage", document_context(doc()))
        audit = captured.exception.audit
        self.assertEqual(audit["http_status"], 400)
        self.assertNotIn("SECRET_SENTINEL", json.dumps(audit))
        self.assertNotIn("sensitive body", json.dumps(audit))

    def test_durable_pipeline_exports_all_stages_and_resume_never_reaudits(self):
        class Fake:
            def __init__(self): self.calls = []
            def run(self, name, payload):
                self.calls.append(name)
                value = {"added_elements": []} if name == "coverage" else entity_response() if name == "entities" else fact_response(True)
                return value, {"api_calls": 1, "raw_content": json.dumps(value)}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); input_path = root / "input.jsonl"; out = root / "run"
            pair = {"pair_id": "pair", "original": doc(), "steer": doc("blue")}
            input_path.write_text(json.dumps(pair)+"\n", encoding="utf-8")
            prepare(input_path, out)
            fake = Fake(); execute(out, fake); execute(out, fake)
            self.assertEqual(fake.calls, ["coverage", "coverage", "entities", "alignment_core"])
            for name in ["coverage.jsonl", "entity_alignment.jsonl", "alignment.jsonl", "verification_pending.jsonl", "TEST_REPORT.md"]:
                self.assertTrue((out/name).is_file())
            stats = json.loads((out / "summary.json").read_text())
            self.assertEqual(stats["alignment_rows_main"]["modified"], 1)
            self.assertEqual(stats["api_calls"], 4)


if __name__ == "__main__": unittest.main()
