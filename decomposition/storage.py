"""Atomic per-sample checkpoints and derived, replaceable export tables."""

import csv
import hashlib
import json
import os
from contextlib import contextmanager
from pathlib import Path

from .caption_parser import caption_row
from .schemas import CAPTION_COLUMNS, FACT_COLUMNS, ENTITY_COLUMNS


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def atomic_write(path, writer):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="") as stream:
            writer(stream)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def write_json(path, value):
    atomic_write(path, lambda stream: json.dump(value, stream, ensure_ascii=False, indent=2))


def write_jsonl(path, rows):
    def writer(stream):
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    atomic_write(path, writer)


def write_csv(path, fields, rows):
    def writer(stream):
        output = csv.DictWriter(stream, fieldnames=fields, extrasaction="raise")
        output.writeheader()
        for row in rows:
            output.writerow({key: json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value
                             for key, value in row.items()})
    atomic_write(path, writer)


@contextmanager
def output_lock(directory):
    directory.mkdir(parents=True, exist_ok=True)
    lock = directory / ".run.lock"
    try:
        stream = lock.open("x", encoding="utf-8")
    except FileExistsError as exc:
        raise ValueError(f"Output directory is locked: {lock}. If a prior process crashed, confirm it has stopped before removing the lock.") from exc
    try:
        with stream:
            stream.write(str(os.getpid()))
        yield
    finally:
        lock.unlink(missing_ok=True)


class RunStore:
    def __init__(self, directory, manifest, resume=False):
        self.directory = Path(directory)
        run_path = self.directory / "run_manifest.json"
        existing = [p for p in self.directory.iterdir() if p.name != ".run.lock"]
        if resume:
            if not run_path.exists():
                raise ValueError("--resume requires an existing run_manifest.json")
            previous = json.loads(run_path.read_text(encoding="utf-8"))
            if previous["fingerprint"] != manifest["fingerprint"]:
                raise ValueError("Inputs, limit, mode, prompt, code or model changed; use a new output directory")
        elif existing:
            raise ValueError("Output directory is not empty; use --resume or a new directory")
        else:
            write_json(run_path, manifest)
        self.checkpoints = self.directory / "checkpoints"
        self.checkpoints.mkdir(exist_ok=True)

    def path(self, sample_id):
        return self.checkpoints / (digest(sample_id) + ".json")

    def load(self, sample_id):
        path = self.path(sample_id)
        if not path.exists():
            return None
        value = json.loads(path.read_text(encoding="utf-8"))
        if value["caption"]["sample_id"] != sample_id:
            raise ValueError("Checkpoint sample ID mismatch")
        return value

    def save(self, value):
        write_json(self.path(value["caption"]["sample_id"]), value)

    def export(self, records, input_failures):
        captions, decomposed, facts, failures, requests = [], [], [], list(input_failures), []
        documents, entities = [], []
        reviews, statuses, audits = [], [], []
        pending = 0
        for record in records:
            saved = self.load(record["sample_id"])
            if saved and "audit" in saved:
                audits.append({"sample_id": record["sample_id"], "status": saved["status"], **saved["audit"]})
            captions.append(saved["caption"] if saved else caption_row(record, None))
            statuses.append({"sample_id": record["sample_id"], "status": saved["status"] if saved else "pending",
                             "reason": saved.get("error", {}).get("error", "") if saved else "",
                             "accepted_fact_count": len(saved["facts"]) if saved and saved["status"] == "success" else None})
            if saved and saved["status"] == "success":
                decomposed.append(saved)
                facts.extend(saved["facts"])
                documents.append(saved["document"])
                entities.extend({"sample_id": record["sample_id"], "entity_id": e["id"],
                                 "mention": e["mention"], "canonical": e["canonical"]}
                                for e in saved["document"]["entities"])
            elif saved and saved["status"] == "failed":
                failures.append({"sample_id": record["sample_id"], **saved["error"]})
            elif saved and saved["status"] == "needs_review":
                reviews.append(saved)
            else:
                pending += 1
            if saved and saved.get("request") is not None:
                requests.append({"sample_id": record["sample_id"], "status": saved["status"], "messages": saved["request"]})
        write_csv(self.directory / "captions.csv", CAPTION_COLUMNS, captions)
        write_csv(self.directory / "facts.csv", FACT_COLUMNS, facts)
        write_csv(self.directory / "entities.csv", ENTITY_COLUMNS, entities)
        write_jsonl(self.directory / "samples.jsonl", documents)
        write_jsonl(self.directory / "decomposed.jsonl", decomposed)
        write_jsonl(self.directory / "failed_samples.jsonl", failures)
        write_jsonl(self.directory / "review_samples.jsonl", reviews)
        write_csv(self.directory / "caption_status.csv", ["sample_id", "status", "reason", "accepted_fact_count"], statuses)
        write_jsonl(self.directory / "requests.jsonl", requests)
        write_jsonl(self.directory / "audit.jsonl", audits)
        summary = {"captions": len(captions), "decomposed": len(decomposed), "facts": len(facts), "entities": len(entities),
                   "failed": len(failures), "needs_review": len(reviews), "pending": pending}
        summary["api_calls"] = sum(a.get("api_calls", 0) for a in audits)
        summary["cache_hits"] = sum(a.get("cache_hit", False) for a in audits)
        write_json(self.directory / "summary.json", summary)
        return summary
