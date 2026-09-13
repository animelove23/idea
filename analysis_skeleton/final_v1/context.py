"""Recover literal caption context without exposing visual references or alignment.

Both public builders return ``{'context': ..., 'audit': ...}``. Only ``context``
belongs in the model's ``entity_context`` input. Audit includes source identity
and hashes and remains local. No quote or offset is invented on lookup failure.
"""
import copy
import hashlib
import json
import re
from pathlib import Path

VERSION = "literal_caption_context_v1"
ROLE = ("Original caption language only, used to resolve the intended referent and "
        "word meaning. It is not visual evidence; judge only the requested statement.")
_REFERENTIAL = re.compile(
    r"\b(other|another|one|it|its|they|them|their|he|him|his|she|her|these|those|this|that)\b", re.I)


def _hash(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def identity():
    return {"context_version": VERSION,
            "context_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "sentence_policy": "previous_and_current_regex_sentence; referential_full_caption"}


def _sentence_spans(text):
    """Literal offsets, including paragraph boundaries; deliberately no NLP/LLM."""
    ends = [m.end() for m in re.finditer(r"[.!?]+(?:[\"']?)(?=\s|$)|\n\s*\n", text)]
    ends.append(len(text))
    spans = []
    start = 0
    for end in sorted(set(ends)):
        while start < end and text[start].isspace():
            start += 1
        trimmed = end
        while trimmed > start and text[trimmed - 1].isspace():
            trimmed -= 1
        if trimmed > start:
            spans.append((start, trimmed))
        start = end
    return spans


def _resolve_spans(text, specs, fallback_quote=None):
    accepted = []
    rejected = 0
    for spec in specs or []:
        if not isinstance(spec, dict):
            rejected += 1
            continue
        start, end = spec.get("start"), spec.get("end")
        quote = spec.get("quote", fallback_quote)
        if (type(start) is int and type(end) is int and 0 <= start < end <= len(text)
                and (quote is None or text[start:end] == quote)):
            accepted.append({"start": start, "end": end, "quote": text[start:end]})
        else:
            rejected += 1
    recovered = False
    if not accepted and isinstance(fallback_quote, str) and fallback_quote:
        accepted = [{"start": m.start(), "end": m.end(), "quote": m.group()}
                    for m in re.finditer(re.escape(fallback_quote), text)]
        recovered = bool(accepted)
    accepted = list({(s["start"], s["end"]): s for s in accepted}.values())
    accepted.sort(key=lambda s: (s["start"], s["end"]))
    status = "missing" if not accepted else ("ambiguous" if len(accepted) > 1 else "resolved")
    return accepted, {"source_status": status, "rejected_span_count": rejected,
                      "quote_search_recovery": recovered}


def _build(text, specs, fallback_quote=None, origin=None):
    spans, detail = _resolve_spans(text, specs, fallback_quote)
    sentence_spans = _sentence_spans(text)
    selected = []
    for span in spans:
        hits = [i for i, (start, end) in enumerate(sentence_spans)
                if start < span["end"] and end > span["start"]]
        if hits:
            lo, hi = max(0, hits[0] - 1), hits[-1]
            selected.append((sentence_spans[lo][0], sentence_spans[hi][1]))
    referential = any(_REFERENTIAL.search(text[start:end]) for start, end in selected)
    # A missing source still exposes the real caption, with an explicit failure
    # status and no claimed mention span. This preserves evidence, not certainty.
    full = referential or not selected
    if full:
        windows = [{"start": 0, "end": len(text), "quote": text}] if text else []
    else:
        merged = []
        for start, end in sorted(set(selected)):
            if merged and start <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))
            else:
                merged.append((start, end))
        windows = [{"start": start, "end": end, "quote": text[start:end]} for start, end in merged]
    context = {"source_window": "\n".join(w["quote"] for w in windows),
               "source_windows": windows, "mention_spans": spans,
               "source_status": detail["source_status"], "context_role": ROLE,
               "context_scope": "full_caption" if full else "previous_and_current_sentences"}
    audit = {**identity(), **detail, "caption_sha256": _hash(text),
             "context_sha256": _hash(json.dumps(context, ensure_ascii=False, sort_keys=True)),
             "full_caption_reason": "referential_language" if referential else ("missing_source" if full else None),
             **(origin or {})}
    return {"context": context, "audit": audit}


def legacy_context(row):
    """Read the original fact and caption afresh; never copy reference fields."""
    path = Path(row["source_pair_file"])
    origin = {"source_pair_file": str(path), "source_fact_id": row["source_fact_id"]}
    try:
        raw = path.read_bytes()
        pair = json.loads(raw.decode("utf-8-sig"))
        doc = pair[row["side"]]
        text = doc["text"]
        if not isinstance(text, str):
            raise TypeError("caption_text_required")
        candidates = [f for f in doc["facts"] if f.get("id") == row["source_fact_id"]]
        origin["source_pair_sha256"] = hashlib.sha256(raw).hexdigest()
        if len(candidates) != 1:
            out = _build(text, [], origin=origin)
            out["audit"]["lookup_status"] = "missing_fact" if not candidates else "ambiguous_fact_id"
            return out
        fact = candidates[0]
        out = _build(text, fact.get("source_matches", []), fact.get("source"), origin)
        out["audit"]["lookup_status"] = "found"
        return out
    except (OSError, ValueError, KeyError, TypeError) as exc:
        out = _build("", [], origin=origin)
        out["audit"].update(lookup_status="source_unavailable", error_type=type(exc).__name__)
        return out


def document_context(doc, entity, fact):
    """Use the queried fact's evidence; an attribute never silently falls back
    to the entity's first mention. Entity existence can use all entity mentions.
    """
    text = doc.get("text", "")
    if not isinstance(text, str):
        raise TypeError("caption_text_required")
    is_attribute = fact.get("type") == "attribute"
    specs = fact.get("source_spans", [])
    if not specs and not is_attribute:
        specs = entity.get("mentions", [])
    out = _build(text, specs, origin={"fact_id": fact.get("id"),
                                    "entity_id": entity.get("id"),
                                    "source_selection": "attribute_fact" if is_attribute else "entity_fact"})
    return out


def enrich_legacy(row):
    """Return only the query payload, with literal context replacing the fragment."""
    payload = copy.deepcopy(row["input"])
    payload["entity_context"] = legacy_context(row)["context"]
    return payload


def build_context(doc, entity=None, fact=None):
    """Pipeline-facing context builder; audits are available via document_context."""
    return document_context(doc, entity or {}, fact or {})["context"]
