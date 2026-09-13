"""Current category-folding decomposer CLI. Historical v4/v5 entry points stay isolated."""
import argparse
import json
from collections import defaultdict
from pathlib import Path

from .caption_parser import caption_row, load_sources
from .config import API_CONFIG_PATH, load_api_config
from .storage import digest, output_lock, write_csv, write_json, write_jsonl
from .v6 import VERSION
from .v6.pipeline import DecomposerV6, V6Failure, prompt
from .v6.schema import summary


def export(output, saved, parser=None):
    docs = [r["document"] for r in saved if "document" in r]
    write_jsonl(output / "results.jsonl", saved)
    write_jsonl(output / "samples.jsonl", docs)
    write_jsonl(output / "ready_samples.jsonl", [d for d in docs if d["status"] in {"ready", "empty"}])
    rows = [{"sample_id": d["id"], "document_status": d["status"], **f} for d in docs for f in d["facts"]]
    fields = ["sample_id", "document_status", "id", "type", "category", "fact", "source", "assertion", "polarity",
              "in_main", "reason", "source_matches", "source_status", "verification"]
    for name, subset in [("facts", rows), ("main_facts", [r for r in rows if r["in_main"]]),
                         ("other", [r for r in rows if not r["in_main"]])]:
        write_csv(output / f"{name}.csv", fields, subset)
    caption_rows = []
    groups = defaultdict(list)
    for r in saved:
        if parser:
            pos, n = parser.parse(r["caption"]["caption"])
        else:
            from .source_document import source_sentences
            pos, n = None, len(source_sentences(r["caption"]["caption"]))
        row = {**caption_row(r["caption"], n, pos), "semantic_status": r["status"], "pos_available": parser is not None}
        caption_rows.append(row)
        groups[(r["caption"].get("method"), r["caption"].get("decode"))].append(r)
    fields = list(dict.fromkeys(k for row in caption_rows for k in row)) or ["sample_id", "caption", "semantic_status"]
    write_csv(output / "captions.csv", fields, caption_rows)
    aggregate = summary(docs)
    aggregate.update(total_inputs=len(saved), failed=sum(r["status"] == "failed" for r in saved),
                     prepared=sum(r["status"] == "prepared" for r in saved),
                     api_calls=sum(r.get("audit", {}).get("api_calls", 0) for r in saved))
    aggregate["by_method_decode"] = [{"method": method, "decode": decode, "total_inputs": len(rs),
                                     "failed": sum(r["status"] == "failed" for r in rs),
                                     **summary(r["document"] for r in rs if "document" in r)}
                                    for (method, decode), rs in groups.items()]
    write_json(output / "summary.json", aggregate)


def main(argv=None):
    p = argparse.ArgumentParser(description="v6: fine semantic elements -> entity/relation/attribute/other")
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--shots", type=int, choices=[0, 8], default=8)
    p.add_argument("--method"); p.add_argument("--decode"); p.add_argument("--limit", type=int)
    p.add_argument("--prepare-only", action="store_true"); p.add_argument("--resume", action="store_true")
    p.add_argument("--api-config", type=Path, default=API_CONFIG_PATH)
    p.add_argument("--spacy-model", help="Optional caption-only POS; omission leaves POS unavailable, never zero")
    a = p.parse_args(argv)
    if a.limit is not None and a.limit < 1:
        p.error("--limit must be positive")
    records, failures = load_sources([{"path": str(a.input.resolve()), "method": a.method, "decode": a.decode}], a.limit)
    parser = None
    if a.spacy_model:
        from .pos_parser import SpacyParser
        parser = SpacyParser(a.spacy_model)
    rules = prompt(a.shots)
    config = None if a.prepare_only else load_api_config(a.api_config)
    code_paths = list(Path(__file__).with_name("v6").glob("*")) + [Path(__file__),
                  Path(__file__).with_name("semantic_decomposer.py"), Path(__file__).with_name("config.py"),
                  Path(__file__).with_name("caption_parser.py"), Path(__file__).with_name("storage.py"),
                  Path(__file__).with_name("source_document.py"), Path(__file__).with_name("pos_parser.py")]
    manifest = {"version": VERSION, "mode": "prepare" if a.prepare_only else "execute", "shots": a.shots,
                "prompt": rules, "input_digest": digest(records), "input_failure_digest": digest(failures),
                "code": {str(path.relative_to(Path(__file__).parent)): digest(path.read_text(encoding="utf-8"))
                         for path in code_paths if path.is_file()},
                "model": config.model if config else None, "base_url": config.base_url if config else None,
                "max_tokens": config.max_tokens if config else None,
                "thinking": "disabled", "temperature": 0, "max_requests_per_caption": 2,
                "pos": parser.identity if parser else None}
    with output_lock(a.output):
        path = a.output / "manifest.json"
        if path.exists():
            if not a.resume or json.loads(path.read_text(encoding="utf-8")) != manifest:
                raise ValueError("Use a new output directory or --resume with identical input/config/code")
        else:
            if any(f.name != ".run.lock" for f in a.output.iterdir()):
                raise ValueError("Output directory must be empty")
            write_json(path, manifest)
        (a.output / "checkpoints").mkdir(exist_ok=True)
        write_json(a.output / "input_failures.json", failures)
        client = DecomposerV6(config, frozen_prompt=rules) if config else None
        saved = []
        for record in records:
            ck = a.output / "checkpoints" / (digest(record["sample_id"]) + ".json")
            if ck.exists():
                result = json.loads(ck.read_text(encoding="utf-8"))
                if result.get("caption") != record:
                    raise ValueError("Checkpoint/input mismatch")
            else:
                result = {"sample_id": record["sample_id"], "caption": record}
                if client is None:
                    result.update(status="prepared", request={"text": record["caption"]})
                else:
                    try:
                        doc, audit = client.decompose(record["caption"])
                        doc["id"] = record["sample_id"]
                        result.update(status=doc["status"], document=doc, audit=audit)
                    except V6Failure as exc:
                        result.update(status="failed", error=str(exc), audit=exc.audit)
                write_json(ck, result)
            saved.append(result)
            print(record["sample_id"], result["status"], flush=True)
        export(a.output, saved, parser)
        return int(bool(failures) or any(r["status"] in {"failed", "needs_review"} for r in saved))


if __name__ == "__main__":
    raise SystemExit(main())
