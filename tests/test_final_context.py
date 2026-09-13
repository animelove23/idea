import json
import tempfile
import unittest
from pathlib import Path

from analysis_skeleton.final_v1.context import document_context, legacy_context


class FinalContextTests(unittest.TestCase):
    def legacy(self, text, source, spans=None, **extras):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        path = Path(self.tmp.name) / "pair.json"
        if spans is None:
            start = text.index(source)
            spans = [{"start": start, "end": start + len(source)}]
        path.write_text(json.dumps({"original": {"text": text, "facts": [
            {"id": "f1", "source": source, "source_matches": spans}]}}), encoding="utf-8")
        return legacy_context({"source_pair_file": str(path), "side": "original", "source_fact_id": "f1",
                               "reference_label": "NEVER_SEND", "image_review_notes": "SECRET_NOTE", **extras})

    def test_menu_recovers_screen_sentence_not_restaurant_assumption(self):
        text = "A hand holds a smartphone. The screen displays a menu and search bar. A tree is behind it."
        got = self.legacy(text, "a menu")
        self.assertEqual(got["context"]["source_window"],
                         "A hand holds a smartphone. The screen displays a menu and search bar.")
        self.assertEqual(got["context"]["source_status"], "resolved")

    def test_referential_other_keeps_full_caption(self):
        text = "Two people are seated. A sign is on the wall. A door is closed. The other man wears blue."
        got = self.legacy(text, "The other man")
        self.assertEqual(got["context"]["source_window"], text)
        self.assertEqual(got["audit"]["full_caption_reason"], "referential_language")

    def test_attribute_uses_its_evidence_not_first_entity_mention(self):
        text = "A dog rests. A tree is behind the fence. The dog has wet fur."
        q = "wet fur"; start = text.index(q)
        got = document_context({"text": text}, {"id": "e1", "mentions": [{"start": 2, "end": 5, "quote": "dog"}]},
                               {"id": "a1", "type": "attribute", "source_spans": [{"start": start, "end": start+len(q), "quote": q}]})
        self.assertIn("wet fur", got["context"]["source_window"])
        self.assertNotIn("A dog rests", got["context"]["source_window"])

    def test_duplicate_source_preserves_all_spans_and_ambiguity(self):
        text = "A cup rests here. A cup rests there."
        spans = [{"start": i, "end": i+5} for i in [0, text.index("A cup", 1)]]
        got = self.legacy(text, "A cup", spans)
        self.assertEqual(len(got["context"]["mention_spans"]), 2)
        self.assertEqual(got["context"]["source_status"], "ambiguous")

    def test_invalid_offsets_do_not_invent_quote(self):
        got = self.legacy("A dog rests.", "cat", [{"start": 2, "end": 5}])
        self.assertEqual(got["context"]["mention_spans"], [])
        self.assertEqual(got["context"]["source_status"], "missing")
        self.assertEqual(got["context"]["source_window"], "A dog rests.")

    def test_attribute_missing_evidence_does_not_use_entity_quote(self):
        got = document_context({"text": "A dog rests."}, {"id": "e", "mentions": [{"start": 2, "end": 5}]},
                               {"id": "a", "type": "attribute", "source_spans": []})
        self.assertEqual(got["context"]["source_status"], "missing")
        self.assertEqual(got["context"]["mention_spans"], [])

    def test_only_context_is_model_input_no_answers_or_identity(self):
        got = self.legacy("A dog rests.", "A dog")
        wire = json.dumps(got["context"])
        for secret in ["NEVER_SEND", "SECRET_NOTE", "source_pair_file", '"side"', '"fact_id"', "original"]:
            self.assertNotIn(secret, wire)
        self.assertEqual(len(got["audit"]["caption_sha256"]), 64)
        self.assertEqual(len(got["audit"]["source_pair_sha256"]), 64)

    def test_legacy_missing_file_preserves_explicit_status(self):
        got = legacy_context({"source_pair_file": "nonexistent_final_context_pair.json", "side": "original", "source_fact_id": "f1"})
        self.assertEqual(got["audit"]["lookup_status"], "source_unavailable")
        self.assertEqual(got["context"]["source_status"], "missing")


if __name__ == "__main__":
    unittest.main()
