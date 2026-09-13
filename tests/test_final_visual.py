import copy
import json
import tempfile
import unittest
from pathlib import Path

from analysis_skeleton.common import read_jsonl, write_jsonl
from analysis_skeleton.final_v1.visual import FinalVisualStage, prepare_shots, validate


class FinalVisualContractTests(unittest.TestCase):
    def setUp(self):
        self.shots = prepare_shots()
        self.entity = copy.deepcopy(self.shots[0]["output"])
        self.attribute = copy.deepcopy(self.shots[3]["output"])

    def test_original_shot_inputs_order_and_labels_are_preserved(self):
        old = read_jsonl("analysis_skeleton/shots/verify.jsonl")
        self.assertEqual(len(self.shots), 6)
        for before, after in zip(old, self.shots):
            self.assertEqual(before["example_id"], after["example_id"])
            self.assertEqual(before["input"], after["input"])
            self.assertEqual(before["output"]["label"], validate(after["output"], after["semantic_type"])["label"])

    def test_matching_entity_does_not_bypass_qualifier_contradiction(self):
        raw = {**self.entity, "proposition_status": "contradicted", "visible_cues": "Two horses are visible; the statement specifies three."}
        result = validate(raw, "entity")
        self.assertEqual(result["base_evidence_label"], "supported")
        self.assertEqual(result["label"], "hallucinated")
        self.assertEqual(result["evidence"], raw)
        self.assertFalse(result["bbox_verified"])

    def test_unresolved_whole_statement_is_always_uncertain(self):
        for shot in self.shots:
            raw = {**shot["output"], "proposition_status": "unresolved"}
            self.assertEqual(validate(raw, shot["semantic_type"])["label"], "uncertain")

    def test_blur_and_occlusion_block_both_definite_proposition_verdicts(self):
        for limit in ("blur", "occlusion", "category_boundary", "ambiguous_identity"):
            for status in ("supported", "contradicted"):
                raw = {**self.entity, "limitation": limit, "region_status": "limited", "proposition_status": status}
                self.assertEqual(validate(raw, "entity")["label"], "uncertain")

    def test_inspected_absence_and_alternative_can_contradict(self):
        for state, box in (("not_found", None), ("alternative", [10, 10, 100, 100])):
            raw = {**self.entity, "candidate_status": state, "bbox": box, "proposition_status": "contradicted"}
            self.assertEqual(validate(raw, "entity")["label"], "hallucinated")
            raw["proposition_status"] = "supported"
            result = validate(raw, "entity")
            self.assertEqual(result["label"], "uncertain")
            self.assertTrue(result["proposition_support_blocked"])

    def test_unresolved_attribute_cannot_be_supported_as_complete_statement(self):
        raw = {**self.attribute, "attribute_status": "unresolved", "proposition_status": "supported"}
        result = validate(raw, "attribute")
        self.assertEqual(result["label"], "uncertain")
        self.assertTrue(result["proposition_support_blocked"])

    def test_supported_attribute_cannot_bypass_unresolved_subject(self):
        raw = {**self.attribute, "candidate_status": "unresolved", "limitation": "ambiguous_identity", "proposition_status": "supported"}
        result = validate(raw, "attribute")
        self.assertEqual(result["label"], "uncertain")
        self.assertTrue(result["attribute_support_blocked_by_referent"])

    def test_nonmatching_property_na_uses_original_compiler_and_retains_raw(self):
        raw = {**self.attribute, "candidate_status": "not_found", "bbox": None, "attribute_status": "not_applicable", "proposition_status": "contradicted"}
        before = copy.deepcopy(raw)
        result = validate(raw, "attribute")
        self.assertEqual(result["label"], "hallucinated")
        self.assertEqual(result["evidence"], before)
        self.assertEqual(raw, before)
        self.assertIn("compiler_note", result)

    def test_reject_model_label_unknown_missing_invalid_fields(self):
        invalid = [None, {**self.entity, "label": "supported"}, {**self.entity, "reference_label": "supported"},
                   {**self.entity, "proposition_status": []}, {**self.entity, "proposition_status": "hallucinated"},
                   {**self.entity, "bbox": [0, 0, 1001, 1000]}, {**self.entity, "bbox": None}]
        missing = copy.deepcopy(self.entity)
        del missing["proposition_status"]
        invalid.append(missing)
        for raw in invalid:
            with self.assertRaises(ValueError):
                validate(raw, "entity")

    def test_input_change_or_test_example_injection_rejected(self):
        original = read_jsonl("analysis_skeleton/shots/verify.jsonl")
        original[0]["input"]["statement"] = "Injected test question."
        with self.assertRaises(ValueError):
            prepare_shots(original)

    def test_one_flash_call_six_images_and_no_reference_fields(self):
        bodies = []
        def fake_transport(body):
            bodies.append(body)
            return {"id": "fake-final-visual", "model": "deepseek-flash", "choices": [{"finish_reason": "stop", "message": {"content": json.dumps(self.entity)}}]}
        with tempfile.TemporaryDirectory() as directory:
            shots_path = Path(directory) / "shots.jsonl"
            write_jsonl(shots_path, self.shots)
            stage = FinalVisualStage(shots_path, transport=fake_transport)
            payload = {**self.shots[0]["input"], "claim_type": "entity", "reference_label": "DO_NOT_SEND"}
            raw, audit = stage.run(payload)
            self.assertEqual(len(bodies), 1)
            body = bodies[0]
            self.assertEqual(body["model"], "deepseek-flash")
            self.assertEqual(body["temperature"], 0)
            self.assertEqual(body["thinking"], {"type": "disabled"})
            self.assertEqual(len(body["messages"]), 14)
            self.assertEqual(sum(m["role"] == "assistant" for m in body["messages"]), 6)
            self.assertEqual(sum(len([part for part in m["content"] if part["type"] == "image_url"]) for m in body["messages"] if m["role"] == "user"), 7)
            self.assertNotIn("DO_NOT_SEND", json.dumps(body))
            self.assertTrue(all('"label"' not in m["content"] for m in body["messages"] if m["role"] == "assistant"))
            self.assertEqual(audit["api_calls"], 1)
            self.assertEqual(raw, self.entity)
            self.assertIn("decision_code_sha", stage.identity)


if __name__ == "__main__":
    unittest.main()
