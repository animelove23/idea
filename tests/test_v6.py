import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from annotation.v6.build_examples import examples
from decomposition.config import APIConfig
from decomposition.run_v6 import export, main
from decomposition.v6.pipeline import DecomposerV6, V6Failure, prompt
from decomposition.v6.schema import FOLD, fold_document, summary


def response(payload, finish="stop"):
    return {"choices": [{"finish_reason": finish, "message": {
        "content": payload if isinstance(payload, str) else json.dumps(payload)}}]}


class V6Tests(unittest.TestCase):
    def test_many_fine_categories_fold_into_four_main_types(self):
        self.assertEqual(set(FOLD.values()), {"entity", "relation", "attribute", "other"})
        for category in ["action", "relation", "spatial", "location"]:
            self.assertEqual(FOLD[category], "relation")
        for category in ["color", "material", "counting", "shape", "state"]:
            self.assertEqual(FOLD[category], "attribute")
        for category in ["human", "animal", "food", "object", "body_part"]:
            self.assertEqual(FOLD[category], "entity")

    def test_examples_are_complete_local_contracts_not_semantic_accuracy(self):
        for example in examples():
            doc = fold_document(example["output"], example["text"])
            self.assertEqual(doc["status"], "ready", doc)
            self.assertTrue(all(example["text"][s["start"]:s["end"]] == f["source"]
                                for f in doc["facts"] for s in f["source_matches"]))

    def test_other_is_retained_but_not_main(self):
        e = examples()[-1]
        doc = fold_document(e["output"], e["text"])
        other = [f for f in doc["facts"] if f["type"] == "other"]
        self.assertEqual(len(other), 2)
        self.assertTrue(all(not f["in_main"] for f in other))
        self.assertEqual(summary([doc])["other_rate"], 2/5)

    def test_speculation_and_negation_do_not_trigger_other(self):
        for index in [4, 5, 7]:
            e = examples()[index]
            doc = fold_document(e["output"], e["text"])
            for fact in doc["facts"]:
                if fact["category"] != "other":
                    self.assertTrue(fact["in_main"])
                    self.assertEqual(fact["verification"], "pending")

    def test_quantity_units_are_preserved_after_folding(self):
        e = examples()[3]
        doc = fold_document(e["output"], e["text"])
        counts = [f for f in doc["facts"] if f["category"] == "counting"]
        self.assertTrue(all(f["type"] == "attribute" for f in counts))
        self.assertIn("two pairs", counts[0]["fact"])
        self.assertIn("several", counts[1]["fact"])

    def test_no_entity_table_is_required_or_generated(self):
        e = examples()[5]
        doc = fold_document(e["output"], e["text"])
        self.assertNotIn("entities", doc)
        self.assertTrue(all("subject" not in f and "predicate" not in f for f in doc["facts"]))

    def test_invalid_row_is_not_hidden_in_other(self):
        e = copy.deepcopy(examples()[0])
        e["output"]["elements"][0]["category"] = "nonsense"
        doc = fold_document(e["output"], e["text"])
        self.assertEqual(doc["status"], "needs_review")
        self.assertEqual(len(doc["invalid_elements"]), 1)
        self.assertEqual(len(doc["facts"]), 7)
        self.assertFalse(any(f["type"] == "other" for f in doc["facts"]))

    def test_non_string_categories_are_quarantined(self):
        for bad in [[], {}, 1, None]:
            e = copy.deepcopy(examples()[0])
            e["output"]["elements"][0]["category"] = bad
            self.assertEqual(len(fold_document(e["output"], e["text"])["invalid_elements"]), 1)

    def test_model_cannot_override_main_type_or_verification(self):
        for field, value in [("type", "other"), ("in_main", False), ("verification", "supported")]:
            e = copy.deepcopy(examples()[0])
            e["output"]["elements"][0][field] = value
            self.assertEqual(len(fold_document(e["output"], e["text"])["invalid_elements"]), 1)

    def test_unmatched_source_keeps_candidate_and_review_status(self):
        e = copy.deepcopy(examples()[0])
        e["output"]["elements"][0]["source"] = "There is a man."
        doc = fold_document(e["output"], e["text"])
        self.assertEqual(len(doc["facts"]), 8)
        self.assertEqual(doc["status"], "needs_review")
        self.assertEqual(doc["facts"][0]["source_status"], "unmatched")

    def test_source_does_not_match_inside_another_word(self):
        payload = {"elements": [dict(category="object", fact="There is a suitcase.", source="it",
                                     assertion="asserted", polarity="positive")]}
        doc = fold_document(payload, "A suitcase is blue.")
        self.assertEqual(doc["facts"][0]["source_matches"], [])

    def test_repeated_source_keeps_all_occurrences_without_merging(self):
        item = dict(category="object", fact="There is a cup.", source="a cup", assertion="asserted", polarity="positive")
        doc = fold_document({"elements": [item, copy.deepcopy(item)]}, "There is a cup beside a cup.")
        self.assertEqual(len(doc["facts"]), 2)
        self.assertEqual(len(doc["facts"][0]["source_matches"]), 2)
        self.assertEqual(doc["status"], "needs_review")

    def test_only_unique_case_repair_is_applied(self):
        e = copy.deepcopy(examples()[0])
        e["output"]["elements"][0]["source"] = "a woman"
        doc = fold_document(e["output"], e["text"])
        self.assertEqual(doc["facts"][0]["source"], "A woman")
        self.assertEqual(len(doc["local_repairs"]), 1)

    def test_no_facts_for_nonempty_caption_requires_review(self):
        doc = fold_document({"elements": []}, "A man stands.")
        self.assertEqual(doc["status"], "needs_review")
        self.assertIsNone(summary([doc])["other_rate"])

    def test_other_requires_reason_and_does_not_become_visual_truth(self):
        e = copy.deepcopy(examples()[-1])
        del e["output"]["elements"][-1]["reason"]
        doc = fold_document(e["output"], e["text"])
        self.assertEqual(len(doc["invalid_elements"]), 1)
        self.assertTrue(all(f["verification"] == "pending" for f in doc["facts"]))

    def test_one_request_no_thinking_no_metadata_and_no_frozen_anchors(self):
        e = examples()[0]; calls = []
        def transport(body):
            calls.append(copy.deepcopy(body))
            return response(e["output"])
        doc, audit = DecomposerV6(APIConfig("test", "placeholder"), transport=transport,
                                  frozen_prompt="rules").decompose(e["text"])
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["thinking"], {"type": "disabled"})
        self.assertEqual(calls[0]["temperature"], 0)
        self.assertEqual(json.loads(calls[0]["messages"][-1]["content"]), {"text": e["text"]})
        self.assertEqual(doc["status"], "ready")
        self.assertEqual(audit["api_calls"], 1)

    def test_malformed_output_retries_at_most_once(self):
        calls = []
        def transport(body):
            calls.append(body)
            return response("broken JSON")
        with self.assertRaises(V6Failure) as caught:
            DecomposerV6(APIConfig("test", "placeholder"), transport=transport,
                         frozen_prompt="rules").decompose("A cat.")
        self.assertEqual(len(calls), 2)
        self.assertEqual(caught.exception.audit["api_calls"], 2)

    def test_local_source_problem_does_not_trigger_semantic_rewrite(self):
        e = copy.deepcopy(examples()[0]); e["output"]["elements"][0]["source"] = "wrong"
        client = DecomposerV6(APIConfig("test", "placeholder"), transport=lambda b: response(e["output"]),
                              frozen_prompt="rules")
        doc, audit = client.decompose(e["text"])
        self.assertEqual(audit["api_calls"], 1)
        self.assertEqual(doc["status"], "needs_review")

    def test_incomplete_output_never_silently_passes(self):
        client = DecomposerV6(APIConfig("test", "placeholder"), transport=lambda b: response({"elements": []}, "length"),
                              frozen_prompt="rules")
        with self.assertRaises(V6Failure):
            client.decompose("A cat.")

    def test_auth_error_is_not_retried(self):
        def transport(body):
            raise HTTPError("https://example.test", 401, "unauthorized", {}, None)
        with self.assertRaises(V6Failure) as caught:
            DecomposerV6(APIConfig("test", "placeholder"), transport=transport,
                         frozen_prompt="rules").decompose("A cat.")
        self.assertEqual(caught.exception.audit["api_calls"], 1)

    def test_empty_caption_makes_no_request(self):
        def transport(body):
            self.fail("Unexpected network call")
        doc, audit = DecomposerV6(APIConfig("test", "placeholder"), transport=transport,
                                  frozen_prompt="rules").decompose("")
        self.assertEqual(doc["status"], "empty")
        self.assertEqual(audit["api_calls"], 0)

    def test_exports_expose_other_review_and_method_denominators(self):
        e = examples()[-1]; doc = fold_document(e["output"], e["text"], "test")
        saved = [{"sample_id": "test", "status": "ready", "document": doc,
                  "caption": {"sample_id": "test", "caption": e["text"], "method": "vanilla", "decode": "greedy"}}]
        saved.append({"sample_id": "failed", "status": "failed", "caption": {
            "sample_id": "failed", "caption": "A cat.", "method": "steer", "decode": "greedy"}})
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory); export(output, saved)
            stats = json.loads((output / "summary.json").read_text())
            self.assertEqual(stats["total_inputs"], 2)
            self.assertEqual(stats["failed"], 1)
            self.assertEqual(stats["by_type"]["other"], 2)
            self.assertEqual(len(stats["by_method_decode"]), 2)
            self.assertIn("other", (output / "other.csv").read_text())

    def test_prepare_and_resume_never_load_api_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root / "input.jsonl"
            source.write_text(json.dumps({"sample_id": "one", "image_id": "1", "caption": "A cat.",
                                          "method": "test", "decode": "greedy"}) + "\n", encoding="utf-8")
            args = ["--input", str(source), "--output", str(root / "run"), "--prepare-only"]
            with patch("decomposition.run_v6.load_api_config", side_effect=AssertionError("key read")):
                self.assertEqual(main(args), 0)
                self.assertEqual(main(args + ["--resume"]), 0)
            with self.assertRaises(ValueError):
                main(args + ["--resume", "--shots", "0"])

    def test_prompt_and_frozen_examples_use_only_fine_labels(self):
        self.assertIn("CATEGORY_MAP", prompt(0))
        self.assertNotIn("INPUT:", prompt(0))
        self.assertEqual(prompt(8).count("\nINPUT:"), 8)


if __name__ == "__main__":
    unittest.main()
