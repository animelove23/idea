"""Shared deterministic I/O, provenance and run boundaries."""
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from decomposition.storage import write_json, write_jsonl, write_csv, digest


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def new_run(path, module, inputs=(), config=None, code=()):
    out = Path(path)
    if out.exists() and any(out.iterdir()):
        raise ValueError("New experiment requires an empty output directory")
    out.mkdir(parents=True, exist_ok=True)
    files = [Path(__file__), *map(Path, code)]
    frozen = out / "frozen_code"
    frozen.mkdir(exist_ok=True)
    for number, source in enumerate(files):
        shutil.copyfile(source, frozen / f"{number:02d}_{source.name}")
    manifest = {"module": module, "created_utc": datetime.now(timezone.utc).isoformat(),
                "inputs": {str(Path(p).resolve()): sha(p) for p in inputs},
                "code": {str(p.resolve()): sha(p) for p in files},
                "config": config or {}, "reference_status": "not_human_gold"}
    write_json(out / "manifest.json", manifest)
    return out


def check_frozen(out):
    manifest = read_json(Path(out) / "manifest.json")
    for group in ("inputs", "code"):
        for name, expected in manifest[group].items():
            if sha(name) != expected:
                raise ValueError(f"Frozen {group} changed: {name}")
    return manifest


def ratio(a, b):
    return a / b if b else None


def report(out, title, metrics, notes=()):
    write_json(Path(out) / "metrics.json", metrics)
    lines = [f"# {title}", "", "本报告区分工程完整性、候选参考符合度和真实语义准确率。", "",
             "```json", json.dumps(metrics, ensure_ascii=False, indent=2), "```", ""]
    lines.extend(f"- {note}" for note in notes)
    (Path(out) / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
