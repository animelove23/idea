"""Narrow schema: local failures remain auditable; never repair semantics."""
import copy
import re

SLOTS = {"color", "material", "size", "shape", "state"}
STATES = {"open", "closed", "wet", "dry", "broken", "intact"}
STATUSES = {"retained", "removed", "added", "modified", "unresolved"}
LABELS = {"supported", "hallucinated", "uncertain"}


def quote_span(text, spec):
    if not isinstance(spec, dict) or not isinstance(spec.get("quote"), str) or not spec["quote"]:
        raise ValueError("source requires quote and zero-based occurrence")
    q, occurrence = spec["quote"], spec.get("occurrence")
    if type(occurrence) is not int or occurrence < 0:
        raise ValueError("source occurrence must be a nonnegative integer")
    pattern = (r"(?<!\w)" if q[0].isalnum() else "") + re.escape(q) + (r"(?!\w)" if q[-1].isalnum() else "")
    matches = list(re.finditer(pattern, text))
    if occurrence >= len(matches):
        raise ValueError("source not found at requested occurrence")
    m = matches[occurrence]
    return {"quote": q, "occurrence": occurrence, "start": m.start(), "end": m.end()}


def normalize_document(raw, text, caption_id="caption"):
    if not isinstance(raw, dict) or any(not isinstance(raw.get(k), list) for k in ("entities", "attributes", "excluded")):
        raise ValueError("entities, attributes, excluded arrays required")
    doc = {"caption_id": caption_id, "text": text, "entities": [], "facts": [], "excluded": [], "issues": []}
    all_ids = [x.get("id") for group in ("entities", "attributes") for x in raw[group] if isinstance(x, dict)]
    duplicate = {i for i in all_ids if all_ids.count(i) > 1}
    names = {}
    for row in raw["entities"]:
        try:
            if not isinstance(row, dict) or not isinstance(row.get("id"), str) or row["id"] in duplicate:
                raise ValueError("invalid/duplicate entity ID")
            if not isinstance(row.get("name"), str) or not row["name"].strip():
                raise ValueError("entity name required")
            if not isinstance(row.get("mentions"), list) or not row["mentions"]:
                raise ValueError("entity mentions required")
            mentions = [quote_span(text, q) for q in row["mentions"]]
            e = {"id": row["id"], "name": row["name"].strip(), "mentions": mentions}
            names[e["id"]] = e["name"]
            doc["entities"].append(e)
            doc["facts"].append({"id": "entity_" + e["id"], "type": "entity", "entity_id": e["id"],
                                 "slot": "existence", "value": e["name"], "source_spans": mentions,
                                 "value_spans": mentions})
        except (ValueError, KeyError, TypeError) as exc:
            doc["issues"].append({"kind": "entity_invalid", "raw": row, "reason": str(exc)})
    fact_ids = {f["id"] for f in doc["facts"]}
    semantic_keys = set()
    for row in raw["attributes"]:
        try:
            if not isinstance(row, dict) or not isinstance(row.get("id"), str) or row["id"] in duplicate or row["id"] in fact_ids:
                raise ValueError("invalid/duplicate attribute ID")
            if row.get("entity_id") not in names or row.get("slot") not in SLOTS:
                raise ValueError("unknown entity or slot")
            if not isinstance(row.get("value"), str) or not row["value"].strip():
                raise ValueError("attribute value required")
            if row["slot"] == "state" and row["value"] not in STATES:
                raise ValueError("state outside frozen six-value vocabulary")
            sources = [quote_span(text, q) for q in row["evidence"]]
            if not sources:
                raise ValueError("attribute evidence required")
            value_spans = [quote_span(text, q) for q in row["value_quotes"]]
            if not value_spans or any(not any(s["start"] <= v["start"] and v["end"] <= s["end"] for s in sources) for v in value_spans):
                raise ValueError("attribute values must occur within evidence")
            key = (row["entity_id"], row["slot"], row["value"].casefold())
            if key in semantic_keys:
                raise ValueError("duplicate same-entity slot/value; review rather than silently dedup")
            semantic_keys.add(key)
            fact_ids.add(row["id"])
            doc["facts"].append({"id": row["id"], "type": "attribute", "entity_id": row["entity_id"],
                                 "slot": row["slot"], "value": row["value"], "source_spans": sources, "value_spans": value_spans})
        except (ValueError, KeyError, TypeError) as exc:
            doc["issues"].append({"kind": "attribute_invalid", "raw": row, "reason": str(exc)})
    for row in raw["excluded"]:
        try:
            if row.get("reason") not in {"action", "relation", "count", "subjective", "nonasserted", "scope_unclear", "discourse"}:
                raise ValueError("unknown exclusion reason")
            doc["excluded"].append({"source": quote_span(text, row["source"]), "reason": row["reason"]})
        except (ValueError, KeyError, TypeError, AttributeError) as exc:
            doc["issues"].append({"kind": "excluded_invalid", "raw": row, "reason": str(exc)})
    doc["status"] = "needs_review" if doc["issues"] else "ready"
    return doc


def model_document(doc):
    """Only text and linguistic facts, with issues explicitly visible; no experimental labels/POS/images."""
    return copy.deepcopy({k: doc[k] for k in ("text", "entities", "facts", "issues")})
