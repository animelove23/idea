"""Deterministic category folding; partial failures are retained, never relabeled other."""
import copy
import json
import re
from collections import Counter
from pathlib import Path

from . import VERSION

CATEGORY_MAP = json.loads(Path(__file__).with_name("categories.json").read_text(encoding="utf-8"))
FOLD = {fine: coarse for coarse, fine_categories in CATEGORY_MAP.items() for fine in fine_categories}
MAIN_TYPES = ("entity", "relation", "attribute")
OTHER_REASONS = {"ambiguous", "scope", "subjective"}


class ProtocolError(ValueError):
    pass


def source_matches(text, quote):
    """Return every match; a repeated excerpt never silently picks its first instance."""
    pattern = (r"(?<!\w)" if quote[0].isalnum() else "") + re.escape(quote)
    pattern += r"(?!\w)" if quote[-1].isalnum() else ""
    matches = list(re.finditer(pattern, text))
    repair = None
    if not matches:
        insensitive = list(re.finditer(pattern, text, re.IGNORECASE))
        if len(insensitive) == 1:
            matches = insensitive
            repair = {"rule": "unique_case_match", "old": quote,
                      "new": text[matches[0].start():matches[0].end()]}
    return [{"start": m.start(), "end": m.end()} for m in matches], repair


def fold_document(payload, text, sample_id="caption"):
    if not isinstance(payload, dict) or set(payload) != {"elements"} or not isinstance(payload["elements"], list):
        raise ProtocolError("Return exactly an object with an elements array")
    facts, invalid, warnings, repairs = [], [], [], []
    required = {"category", "fact", "source", "assertion", "polarity"}
    for index, raw in enumerate(payload["elements"]):
        errors = []
        if not isinstance(raw, dict):
            invalid.append({"index": index, "raw": copy.deepcopy(raw), "errors": ["element must be an object"]})
            continue
        if not required <= set(raw) or set(raw) - (required | {"reason"}):
            errors.append("fields must be category/fact/source/assertion/polarity and optional other reason")
        for field in required:
            if not isinstance(raw.get(field), str) or not raw[field].strip():
                errors.append(f"{field} must be a nonempty string")
        category = raw.get("category")
        if not isinstance(category, str) or category not in FOLD:
            errors.append("unknown category")
        if raw.get("assertion") not in ("asserted", "speculative"):
            errors.append("invalid assertion")
        if raw.get("polarity") not in ("positive", "negative"):
            errors.append("invalid polarity")
        if category == "other":
            if raw.get("reason") not in tuple(OTHER_REASONS):
                errors.append("other requires ambiguous/scope/subjective reason")
        elif "reason" in raw:
            errors.append("reason is only for other")
        if errors:
            invalid.append({"index": index, "raw": copy.deepcopy(raw), "errors": errors})
            continue
        fact = copy.deepcopy(raw)
        matches, repair = source_matches(text, fact["source"])
        if repair:
            fact["source"] = repair["new"]
            repairs.append({"index": index, **repair})
        status = "verified" if len(matches) == 1 else "ambiguous" if matches else "unmatched"
        fact.update(id=f"f{len(facts)+1}", type=FOLD[category], in_main=FOLD[category] in MAIN_TYPES,
                    source_matches=matches, source_status=status, verification="pending")
        if status != "verified":
            warnings.append({"fact_id": fact["id"], "rule": "source_" + status})
        # No automatic semantic deduplication or completion; equal text can concern different instances.
        facts.append(fact)
    if text.strip() and not facts and not invalid:
        warnings.append({"rule": "empty_extraction", "message": "Nonempty caption returned no elements; review coverage"})
    return {"version": VERSION, "id": sample_id, "text": text, "facts": facts,
            "invalid_elements": invalid, "warnings": warnings, "local_repairs": repairs,
            "status": "needs_review" if invalid or warnings else "ready" if text.strip() else "empty"}


def summary(documents):
    """Routing coverage only, not accuracy or calibrated confidence."""
    docs = list(documents)
    facts = [f for d in docs for f in d["facts"]]
    counts = Counter(f["type"] for f in facts)
    total = len(facts)
    return {"documents": len(docs), "elements": total,
            "by_type": {k: counts[k] for k in (*MAIN_TYPES, "other")},
            "by_category": dict(Counter(f["category"] for f in facts)),
            "other_reasons": dict(Counter(f["reason"] for f in facts if f["type"] == "other")),
            "other_rate": counts["other"] / total if total else None,
            "main_retained_rate": sum(counts[k] for k in MAIN_TYPES) / total if total else None,
            "invalid_elements": sum(len(d["invalid_elements"]) for d in docs),
            "unverified_sources": sum(f["source_status"] != "verified" for f in facts),
            "documents_needing_review": sum(d["status"] == "needs_review" for d in docs),
            "note": "Rates describe routing among extracted elements, NOT caption coverage, accuracy or visual truth."}
