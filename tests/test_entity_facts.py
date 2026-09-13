"""Schema boundary and end-to-end regressions; no live API or gold accuracy claims."""
import copy
import csv
import json
import tempfile
import unittest
from pathlib import Path
from urllib.error import HTTPError

from decomposition.caption_parser import normalize_caption
from decomposition.config import APIConfig, load_prompt
from decomposition.entity_normalizer import normalize_document
from decomposition.fact_builder import build_facts
from decomposition.run_decomposition import run_pipeline
from decomposition.schemas import ValidationError, validate_document
from decomposition.semantic_decomposer import DeepSeekDecomposer, DecompositionError, ReviewRequired, build_messages


def tennis():
    d = json.loads(Path("annotation/v4/entity_examples/practice_01.json").read_text(encoding="utf-8"))
    return {**d, "id": "caption"}


def response(doc):
    return {"choices": [{"finish_reason": "stop", "message": {"content": json.dumps(doc)}}]}


class SchemaTests(unittest.TestCase):
    def test_user_example(self):
        d = tennis()
        self.assertEqual(validate_document(d), d)
        self.assertEqual((len(d["entities"]), len(d["facts"])), (4, 9))

    def test_all_examples(self):
        for p in Path("annotation/v4/entity_examples").glob("practice_*.json"):
            with self.subTest(p=p):
                validate_document(json.loads(p.read_text(encoding="utf-8")))

    def test_reject_old_fact_text_schema(self):
        with self.assertRaises(ValidationError):
            validate_document({"facts": [{"id": "f1", "type": "object", "fact": "person exists"}]})

    def test_original_text_id(self):
        for kwargs in ({"expected_text": "Changed caption"}, {"expected_id": "other"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValidationError):
                validate_document(tennis(), **kwargs)

    def test_sources_and_mentions_must_be_verbatim(self):
        for collection, field, value in [("entities", "mention", "a tennis player"), ("facts", "source", "person playing tennis")]:
            d = tennis(); d[collection][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValidationError):
                validate_document(d)

    def test_dangling_references_rejected(self):
        for field in ("subject", "object"):
            d = tennis(); d["facts"][6][field] = "e99"
            with self.subTest(field=field), self.assertRaises(ValidationError):
                validate_document(d)

    def test_unique_local_ids(self):
        for collection in ("entities", "facts"):
            d = tennis(); d[collection][1]["id"] = d[collection][0]["id"]
            with self.subTest(collection=collection), self.assertRaises(ValidationError):
                validate_document(d)

    def test_type_specific_fields(self):
        mutations = [(0, "value", "white"), (4, "object", "e1"), (6, "value", "white"), (8, "value", "soon")]
        for i, field, value in mutations:
            d = tennis(); d["facts"][i][field] = value
            with self.subTest(i=i), self.assertRaises(ValidationError): validate_document(d)

    def test_relation_requires_both_ends_action_object_optional(self):
        d = tennis(); del d["facts"][8]["object"]
        validate_document(d)
        del d["facts"][6]["object"]
        with self.assertRaises(ValidationError): validate_document(d)

    def test_exists_only_object(self):
        d = tennis(); d["facts"][0]["predicate"] = "color"
        with self.assertRaises(ValidationError): validate_document(d)

    def test_holding_wearing_not_actions(self):
        for i in (6, 7):
            d = tennis(); d["facts"][i]["type"] = "action"
            with self.subTest(i=i), self.assertRaises(ValidationError): validate_document(d)

    def test_decomposition_cannot_verify(self):
        for status in ("supported", "hallucinated", "uncertain"):
            d = tennis(); d["facts"][0]["verification"] = status
            with self.subTest(status=status), self.assertRaises(ValidationError): validate_document(d)
            validate_document(d, decomposition=False)

    def test_no_extra_alignment_fields(self):
        d = tennis(); d["facts"][0]["change"] = "removed"
        with self.assertRaises(ValidationError): validate_document(d)

    def test_count_class_and_set(self):
        for target in ("person", ["e1"]):
            d = tennis()
            d["facts"].append({"id":"f10", "type":"count", "target":target, "predicate":"count_gte", "value":2,
                               "assertion":"asserted", "source":"A tennis player", "verification":"pending"})
            # This verifies structure only; deliberately does not certify source entailment.
            validate_document(d)
            rows = build_facts({"sample_id":"s", "caption":d["text"]}, d)
            if isinstance(target, list): self.assertEqual(json.loads(rows[-1]["target"]), target)

    def test_vague_count_not_quantized(self):
        d = json.loads(Path("annotation/v4/entity_examples/practice_03.json").read_text(encoding="utf-8"))
        validate_document(d)
        self.assertEqual(d["facts"][2]["value"], "several")
        d["facts"][2]["predicate"] = "count_gte"
        with self.assertRaises(ValidationError): validate_document(d)

    def test_count_invalid_targets_and_values(self):
        base = {"id":"f10", "type":"count", "target":"person", "predicate":"count", "value":2,
                "assertion":"asserted", "source":"A tennis player", "verification":"pending"}
        for key, value in [("target", "e1"), ("target", []), ("target", ["e99"]), ("target", ["e1","e1"]),
                           ("value", True), ("value", -1), ("value", 1.5), ("value", float("nan")), ("value", {})]:
            d = tennis(); f = {**base, key:value}; d["facts"].append(f)
            with self.subTest(key=key,value=value), self.assertRaises(ValidationError): validate_document(d)

    def test_count_does_not_allow_subject(self):
        d = json.loads(Path("annotation/v4/entity_examples/practice_03.json").read_text(encoding="utf-8"))
        d["facts"][2]["subject"] = "e1"
        with self.assertRaises(ValidationError): validate_document(d)

    def test_empty_document(self):
        validate_document({"id":"x", "text":"", "entities":[], "facts":[]})
        d = tennis(); d["text"] = ""
        with self.assertRaises(ValidationError): validate_document(d)


class PreservationTests(unittest.TestCase):
    def test_same_class_instances_preserved(self):
        d = json.loads(Path("annotation/v4/entity_examples/practice_02.json").read_text(encoding="utf-8"))
        result, changes = normalize_document(d)
        self.assertEqual(result, d); self.assertFalse(changes)
        self.assertEqual(len([f for f in result["facts"] if f["type"] == "object"]), 2)

    def test_exact_duplicates_only(self):
        d = tennis(); d["facts"].append({**d["facts"][0], "id":"f10", "source":d["text"]})
        result, changes = normalize_document(d)
        self.assertEqual(len(result["facts"]), 9)
        self.assertEqual(changes[0]["removed_id"], "f10")
        self.assertEqual(len(d["facts"]), 10)  # caller original never mutated

    def test_speculation_preserved(self):
        d = tennis(); d["facts"].append({**d["facts"][8], "id":"f10", "assertion":"speculative"})
        result, changes = normalize_document(d)
        self.assertEqual(len(result["facts"]), 10); self.assertFalse(changes)

    def test_contradictions_preserved(self):
        d = tennis(); d["facts"].append({**d["facts"][4], "id":"f10", "value":"black"})
        result, changes = normalize_document(d)
        self.assertEqual(len(result["facts"]), 10); self.assertFalse(changes)


class PipelineTests(unittest.TestCase):
    def config(self, **kwargs): return APIConfig(model="test", api_key="local-test-placeholder", **kwargs)

    def test_input_blinding(self):
        m = build_messages("A man.", load_prompt())
        self.assertEqual(json.loads(m[1]["content"]), {"id":"caption", "text":"A man."})

    def test_model_kept_nonthinking_and_no_self_review(self):
        calls = []
        def transport(body): calls.append(copy.deepcopy(body)); return response(tennis())
        d, audit = DeepSeekDecomposer(self.config(), transport=transport).decompose(tennis()["text"])
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["thinking"], {"type":"disabled"})
        self.assertEqual(calls[0]["temperature"], 0)
        self.assertEqual(d, tennis()); self.assertEqual(audit["api_calls"], 1)

    def test_enabled_thinking_rejected(self):
        with self.assertRaises(ValueError): self.config(thinking="enabled")

    def test_reference_error_bounded_repair(self):
        bad = tennis(); bad["facts"][6]["object"] = "e99"
        replies = iter([response(bad), response(tennis())]); calls = []
        def transport(body): calls.append(copy.deepcopy(body)); return next(replies)
        d, audit = DeepSeekDecomposer(self.config(retries=1), transport=transport, sleep=lambda _:None).decompose(tennis()["text"])
        self.assertEqual(len(calls), 2)
        self.assertIn("existing entity", calls[1]["messages"][-1]["content"])
        self.assertEqual(audit["api_calls"], 2)

    def test_invalid_response_quarantined(self):
        client = DeepSeekDecomposer(self.config(retries=1), transport=lambda _:response({"facts":[]}), sleep=lambda _:None)
        with self.assertRaises(ReviewRequired) as caught: client.decompose("A man.")
        self.assertEqual(len(caught.exception.attempts), 2)

    def test_http_auth_not_retried(self):
        calls = []
        def transport(body): calls.append(1); raise HTTPError("https://example.invalid", 401, "auth", {}, None)
        client = DeepSeekDecomposer(self.config(), transport=transport, sleep=lambda _:None)
        with self.assertRaises(DecompositionError): client.decompose("A man.")
        self.assertEqual(len(calls), 1)

    def test_cache_and_bypass(self):
        calls = []
        def transport(body): calls.append(1); return response(tennis())
        with tempfile.TemporaryDirectory() as tmp:
            c = DeepSeekDecomposer(self.config(), transport=transport, cache_dir=tmp)
            c.decompose(tennis()["text"])
            _, a = c.decompose(tennis()["text"])
            self.assertTrue(a["cache_hit"]); self.assertEqual(a["api_calls"], 0)
            DeepSeekDecomposer(self.config(), transport=transport, cache_dir=tmp, bypass_cache=True).decompose(tennis()["text"])
        self.assertEqual(len(calls), 2)

    def test_empty_and_repetition_no_api(self):
        def forbidden(_): self.fail("No API expected")
        c = DeepSeekDecomposer(self.config(), transport=forbidden)
        d, a = c.decompose(""); validate_document(d); self.assertEqual(a["api_calls"], 0)
        with self.assertRaises(ReviewRequired): c.decompose("Palm " * 20)

    def test_export_and_resume(self):
        class Parser:
            def parse(self, text): return {}, 1
        r = normalize_caption({"image_id":1, "method":"vanilla", "decode":"greedy", "caption":tennis()["text"]})
        calls = []
        def transport(body): calls.append(1); return response(tennis())
        c = DeepSeekDecomposer(self.config(), transport=transport)
        with tempfile.TemporaryDirectory() as tmp:
            args = dict(manifest={"fingerprint":"test"}, prompt=load_prompt())
            stats = run_pipeline([r], [], Parser(), c, tmp, **args)
            self.assertEqual((stats["decomposed"], stats["entities"], stats["facts"]), (1,4,9))
            doc = json.loads((Path(tmp)/"samples.jsonl").read_text(encoding="utf-8"))
            validate_document(doc, expected_id=r["sample_id"], expected_text=r["caption"])
            with (Path(tmp)/"entities.csv").open(encoding="utf-8", newline="") as f:
                self.assertEqual(len(list(csv.DictReader(f))), 4)
            with (Path(tmp)/"facts.csv").open(encoding="utf-8", newline="") as f:
                rows = list(csv.DictReader(f))
                self.assertTrue(all(row["verification"] == "pending" for row in rows))
                self.assertNotIn("truth", rows[0]); self.assertEqual(rows[6]["object"], "e2")
            run_pipeline([r], [], Parser(), c, tmp, resume=True, **args)
            self.assertEqual(len(calls), 1)


if __name__ == "__main__": unittest.main()
