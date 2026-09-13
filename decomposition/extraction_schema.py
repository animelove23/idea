"""Validate source accounting separately from the minimal public fact schema."""
import re
from .config import FACT_TYPES
from .schemas import ValidationError

ASSERTIONS = {"assertive", "qualified"}
EXCLUSION_REASONS = {"subjective", "nonvisual_analysis", "scene_only", "instruction"}
MODAL = re.compile(r"\b(appears?|seems?|may|might|could|likely|possibly|apparently|probably|perhaps)\b", re.I)


def check_text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(label + " must be a nonempty string")


def check_sources(ids, sentences):
    if not isinstance(ids, list) or not ids or any(not isinstance(i, str) or i not in sentences for i in ids) or len(set(ids)) != len(ids):
        raise ValidationError("source_sentences must contain unique known sentence IDs")


def validate_candidate(item, sentences):
    if not isinstance(item, dict) or set(item) != {"type", "fact", "source_sentences", "assertion"}:
        raise ValidationError("candidate must have type, fact, source_sentences, assertion")
    check_text(item["fact"], "fact")
    if item["type"] not in FACT_TYPES or item["assertion"] not in ASSERTIONS:
        raise ValidationError("invalid fact type or assertion")
    check_sources(item["source_sentences"], sentences)
    if item["assertion"] == "qualified" and not MODAL.search(item["fact"]):
        raise ValidationError("qualified fact must retain its uncertainty operator")
    if item["assertion"] == "assertive" and MODAL.search(item["fact"]):
        raise ValidationError("uncertain fact must be marked qualified")
    return item


def validate_extraction(payload, sentences):
    lookup = {s["sentence_id"]: s["text"] for s in sentences}
    if not isinstance(payload, dict) or set(payload) != {"sentences"} or not isinstance(payload["sentences"], list):
        raise ValidationError("response must contain only sentences: list")
    seen, candidates = set(), []
    for row in payload["sentences"]:
        fields = {"sentence_id", "scope", "excluded", *FACT_TYPES}
        if not isinstance(row, dict) or set(row) != fields:
            raise ValidationError("each sentence needs sentence_id, scope, excluded, and all five type lists")
        sid = row["sentence_id"]
        if not isinstance(sid, str) or sid not in lookup or sid in seen:
            raise ValidationError("unknown or repeated sentence_id")
        seen.add(sid)
        if row["scope"] not in {"descriptive", "analytical", "mixed"}:
            raise ValidationError("invalid sentence scope")
        if not isinstance(row["excluded"], list):
            raise ValidationError("excluded must be a list")
        for ex in row["excluded"]:
            if not isinstance(ex, dict) or set(ex) != {"text", "reason"}:
                raise ValidationError("exclusion requires text and reason")
            check_text(ex["text"], "excluded text")
            if ex["text"] not in lookup[sid] or ex["reason"] not in EXCLUSION_REASONS:
                raise ValidationError("exclusion must quote original sentence with an allowed reason")
        local = []
        for kind in FACT_TYPES:
            if not isinstance(row[kind], list):
                raise ValidationError("all five categories must be lists")
            for item in row[kind]:
                if not isinstance(item, dict) or set(item) != {"fact", "assertion", "source_sentences"}:
                    raise ValidationError("fact entry needs fact, assertion, source_sentences")
                candidate = validate_candidate({"type": kind, **item}, lookup)
                if sid not in candidate["source_sentences"]:
                    raise ValidationError("fact must include its containing sentence as a source")
                local.append(candidate)
        if row["scope"] == "analytical" and local:
            raise ValidationError("analytical sentence cannot emit facts")
        if row["scope"] == "analytical" and not row["excluded"]:
            raise ValidationError("analytical sentence needs exclusion evidence")
        candidates.extend(local)
    if seen != set(lookup):
        raise ValidationError("every original sentence must be accounted for, including the last sentence")
    from .protocol import enforce_policy
    enforce_policy(candidates, sentences)
    return candidates
