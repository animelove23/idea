"""Input adapters for raw caption JSONL and CSV; never consume CHAIR labels."""

import csv
import json
from pathlib import Path


def normalize_caption(row, *, method=None, decode=None, source_file="", source_line=0):
    if not isinstance(row, dict):
        raise ValueError("Input row must be an object")
    caption = row.get("caption")
    if not isinstance(caption, str):
        raise ValueError("caption must be a string (missing/null is not an empty caption)")
    image_id = row.get("image_id")
    if type(image_id) not in (str, int) or not str(image_id).strip():
        raise ValueError("image_id must be a nonempty string or integer")
    labels = {}
    for key, override in (("method", method), ("decode", decode)):
        value = row.get(key) or override
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Provide {key} in row, CLI, or manifest")
        if override and row.get(key) and override != row[key]:
            raise ValueError(f"Conflicting {key} in row and input configuration")
        labels[key] = value
    sample_id = row.get("sample_id", f"{image_id}_{labels['method']}_{labels['decode']}")
    if not isinstance(sample_id, str) or not sample_id.strip():
        raise ValueError("sample_id must be a nonempty string")
    record = {"sample_id": sample_id, "image_id": image_id, **labels, "caption": caption}
    for key in ("token_len", "eos_step"):
        value = row.get(key)
        if value == "" or value is None:
            value = None
        elif isinstance(value, str) and value.isdecimal():
            value = int(value)
        if value is not None and (type(value) is not int or value < 0):
            raise ValueError(f"{key} must be a nonnegative integer or null")
        record[key] = value
    record.update(source_file=source_file, source_line=source_line)
    return record


def load_sources(sources, limit=None):
    """limit is per source; preserve invalid rows as explicit failures."""
    records, failures, seen = [], [], set()
    for source in sources:
        path = Path(source["path"]).resolve()
        if path.suffix.lower() not in {".csv", ".jsonl"}:
            raise ValueError(f"Only raw .jsonl or .csv inputs supported: {path}")
        with path.open(encoding="utf-8-sig", newline="") as stream:
            rows = enumerate(csv.DictReader(stream), 2) if path.suffix.lower() == ".csv" else enumerate(stream, 1)
            count = 0
            for line, raw in rows:
                if isinstance(raw, str) and not raw.strip():
                    continue
                if limit is not None and count >= limit:
                    break
                count += 1
                try:
                    row = json.loads(raw) if isinstance(raw, str) else raw
                    record = normalize_caption(row, method=source.get("method"), decode=source.get("decode"), source_file=str(path), source_line=line)
                except (ValueError, TypeError) as exc:
                    failures.append({"stage": "input", "source_file": str(path), "source_line": line, "error": str(exc)})
                    continue
                if record["sample_id"] in seen:
                    raise ValueError(f"Duplicate sample_id: {record['sample_id']}; assign unique IDs before running")
                seen.add(record["sample_id"])
                records.append(record)
    return records, failures


def caption_row(record, sentence_num, pos_counts=None):
    from .schemas import POS_TAGS
    from .quality import repetitive_caption
    caption = record["caption"]
    return {**record, "char_len": len(caption), "word_len": len(caption.split()),
            "sentence_num": sentence_num, "empty": not caption.strip(),
            "generation_status": "empty" if not caption.strip() else "degenerate_repetition" if repetitive_caption(caption) else "normal",
            "semantic_status": "pending",
            **{f"{tag}_count": (pos_counts or {}).get(f"{tag}_count") for tag in POS_TAGS}}
