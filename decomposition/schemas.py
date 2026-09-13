"""Entity-anchored schema; structural/source validity is not image truth."""
import math
import re
from .config import FACT_TYPES

POS_TAGS = ("NOUN", "ADJ", "VERB", "ADP", "NUM")
CAPTION_COLUMNS = ["sample_id", "image_id", "method", "decode", "caption", "char_len", "word_len", "token_len", "sentence_num", "empty", "eos_step", "source_file", "source_line", "generation_status", "semantic_status", *[f"{tag}_count" for tag in POS_TAGS]]
FACT_COLUMNS = ["sample_id", "fact_id", "type", "subject", "predicate", "object", "target", "value", "assertion", "source", "verification"]
ENTITY_COLUMNS = ["sample_id", "entity_id", "mention", "canonical"]
BASE = {"id", "type", "predicate", "assertion", "source", "verification"}
COUNT_PREDICATES = {"count", "count_eq", "count_gte", "count_gt", "count_lte", "count_lt"}

class ValidationError(ValueError):
    pass

def require(condition, message):
    if not condition:
        raise ValidationError(message)

def nonempty(value):
    return isinstance(value, str) and bool(value.strip())

def symbol(value):
    return isinstance(value, str) and bool(re.fullmatch(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)*", value))

def validate_document(payload, *, expected_text=None, expected_id=None, decomposition=True):
    require(isinstance(payload, dict) and set(payload) == {"id", "text", "entities", "facts"}, "sample needs exactly id, text, entities, facts")
    require(nonempty(payload["id"]) and isinstance(payload["text"], str), "id must be nonempty and text must be original caption")
    require(expected_text is None or payload["text"] == expected_text, "text must equal unmodified input caption")
    require(expected_id is None or payload["id"] == expected_id, "id must equal input id")
    require(isinstance(payload["entities"], list) and isinstance(payload["facts"], list), "entities/facts must be lists")
    entities = set()
    for e in payload["entities"]:
        require(isinstance(e, dict) and set(e) == {"id", "mention", "canonical"}, "entity needs id, mention, canonical")
        require(isinstance(e["id"], str) and bool(re.fullmatch(r"e[1-9][0-9]*", e["id"])) and e["id"] not in entities, "unique local entity ids e1/e2 required")
        entities.add(e["id"])
        require(nonempty(e["mention"]) and e["mention"] in payload["text"], "mention must be a verbatim substring, including case")
        require(symbol(e["canonical"]), "canonical must be lower_case class")
    ids = set()
    for f in payload["facts"]:
        require(isinstance(f, dict) and BASE.issubset(f), "fact needs id/type/predicate/assertion/source/verification")
        require(isinstance(f["id"], str) and bool(re.fullmatch(r"f[1-9][0-9]*", f["id"])) and f["id"] not in ids, "unique fact ids f1/f2 required")
        ids.add(f["id"])
        kind = f["type"]
        require(isinstance(kind, str) and kind in FACT_TYPES, "unsupported fact type")
        required = BASE | ({"target", "value"} if kind == "count" else {"subject"})
        if kind == "attribute": required |= {"value"}
        if kind == "relation": required |= {"object"}
        allowed = required | ({"object"} if kind == "action" else set())
        require(required.issubset(f) and set(f).issubset(allowed), f"{kind} requires fields {sorted(required)}; action alone allows optional object")
        for key in ("subject", "object"):
            if key in f:
                require(isinstance(f[key], str) and f[key] in entities, f"{key} must reference an existing entity")
        require(symbol(f["predicate"]), "predicate must be lower_case")
        require(isinstance(f["assertion"], str) and f["assertion"] in {"asserted", "speculative"}, "assertion must be asserted/speculative")
        states = {"pending"} if decomposition else {"pending", "supported", "hallucinated", "uncertain"}
        require(isinstance(f["verification"], str) and f["verification"] in states, "decomposition verification must be pending")
        require(nonempty(f["source"]) and f["source"] in payload["text"], "source must be a verbatim substring")
        if "value" in f:
            v = f["value"]
            require(nonempty(v) or (type(v) in {int, float} and math.isfinite(v)), "value must be nonempty text or finite number")
        if kind == "object":
            require(f["predicate"] == "exists", "object predicate must be exists")
        if kind == "action":
            require(f["predicate"] not in {"holds", "wears", "holding", "wearing"}, "holding/wearing are relation, not action")
        if kind == "count":
            require(f["predicate"] in COUNT_PREDICATES, "invalid count comparator")
            t = f["target"]
            if isinstance(t, list):
                require(bool(t) and all(isinstance(e, str) and e in entities for e in t), "target members must reference existing entities")
                require(len(set(t)) == len(t), "count target members must be distinct")
            else:
                require(symbol(t) and not re.fullmatch(r"e[0-9]+", t), "count target is a canonical class or an entity-id list")
            if type(f["value"]) in {int, float}:
                require(f["value"] >= 0 and int(f["value"]) == f["value"], "count value must be a nonnegative integer")
            else:
                require(f["predicate"] == "count", "vague counts use count without a numeric comparator")
    require(bool(payload["text"].strip()) or not (payload["facts"] or payload["entities"]), "empty text cannot have entities/facts")
    return payload

def validate_facts(payload):
    return validate_document(payload)["facts"]
