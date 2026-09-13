"""Run with python -m decomposition.run_decomposition --help."""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from .caption_parser import caption_row, load_sources
from .config import API_CONFIG_PATH, SCHEMA_VERSION, PROMPT_VERSION, load_api_config, load_prompt
from .fact_builder import build_facts
from .pos_parser import SpacyParser
from .semantic_decomposer import DeepSeekDecomposer, DecompositionError, ReviewRequired, build_messages
from .storage import RunStore, digest, output_lock


def run_pipeline(records, input_failures, parser, decomposer, output, *, manifest,
                 prompt, prepare_only=False, resume=False, progress=None, retry_review=False):
    """Injected parser/client support deterministic tests without a live API."""
    output = Path(output)
    with output_lock(output):
        store = RunStore(output, manifest, resume)
        try:
            for index, record in enumerate(records, 1):
                previous = store.load(record["sample_id"])
                if previous and (previous["status"] == "success" or
                                 (previous["status"] == "needs_review" and not retry_review) or
                                 (prepare_only and previous["status"] == "prepared")):
                    if progress:
                        progress(index, len(records), record["sample_id"], "cached")
                    continue
                saved = {"status": "pending", "caption": caption_row(record, None), "facts": []}
                stage = "pos"
                try:
                    pos_counts, sentence_num = parser.parse(record["caption"])
                    saved.update(caption=caption_row(record, sentence_num, pos_counts),
                                 request=build_messages(record["caption"], prompt))
                    store.save(saved)
                    if prepare_only:
                        saved["status"] = "prepared"
                    else:
                        stage = "decomposition"
                        payload, audit = decomposer.decompose(record["caption"])
                        saved["facts"] = build_facts(record, payload)
                        saved.update(status="success", audit=audit, document={**payload, "id": record["sample_id"]})
                        saved["caption"]["semantic_status"] = audit["semantic_status"]
                except ReviewRequired as exc:
                    saved.update(status="needs_review", audit=exc.audit,
                                 error={"stage": "semantic_quality", "error": str(exc)})
                    saved["caption"]["semantic_status"] = exc.audit.get("semantic_status", "needs_review")
                except (DecompositionError, ValueError, RuntimeError) as exc:
                    saved.update(status="failed", error={"stage": stage, "error": str(exc)})
                    saved["caption"]["semantic_status"] = "failed"
                    if isinstance(exc, DecompositionError):
                        saved["error"]["attempts"] = exc.attempts
                        if hasattr(exc, "audit"):
                            saved["audit"] = exc.audit
                store.save(saved)
                if progress:
                    progress(index, len(records), record["sample_id"], saved["status"])
                if saved["status"] == "failed" and saved["error"]["error"] in {"API HTTP 400", "API HTTP 401", "API HTTP 403", "API HTTP 404"}:
                    break  # Configuration/auth failures affect every remaining sample.
        finally:
            summary = store.export(records, input_failures)
    return summary


def argument_parser():
    parser = argparse.ArgumentParser(description="Entity-anchored five-type facts and independent caption POS counts")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--manifest", type=Path, help="JSON with inputs: [{path, method, decode}]; paths relative to manifest")
    source.add_argument("--input", type=Path, help="Raw caption JSONL or CSV")
    parser.add_argument("--method", help="Single-input method label")
    parser.add_argument("--decode", help="Single-input decoding label")
    parser.add_argument("--output", type=Path, default=Path("outputs/decomposition"))
    parser.add_argument("--limit", type=int, help="Maximum input rows PER FILE; use small pilot first")
    parser.add_argument("--prepare-only", action="store_true", help="Build caption statistics and requests without calling API")
    parser.add_argument("--shots", type=int, choices=[0, 8], default=8, help="Frozen eight-shot examples by default; 0 uses identical rules without examples")
    parser.add_argument("--resume", action="store_true", help="Reuse matching successes; retry failed/pending samples")
    parser.add_argument("--retry-review", action="store_true", help="With --resume, explicitly re-run quarantined semantic cases")
    parser.add_argument("--cache-dir", type=Path, default=Path("outputs/decomposer_cache"))
    parser.add_argument("--bypass-cache", action="store_true", help="Independent repeatability run; do not read/write shared cache")
    parser.add_argument("--spacy-model", default="en_core_web_md")
    parser.add_argument("--api-config", type=Path, default=API_CONFIG_PATH, help="Local JSON API configuration; ignored in prepare-only mode")
    parser.add_argument("--model", help="Override the model in the API configuration")
    parser.add_argument("--base-url", help="Override HTTPS API base URL")
    parser.add_argument("--max-tokens", type=int, help="Override maximum API output tokens")
    parser.add_argument("--timeout", type=float, help="Override request timeout in seconds")
    parser.add_argument("--retries", type=int, help="Override extra attempts after first request")
    parser.add_argument("--thinking", choices=["disabled"], help="Thinking is always disabled; enabled is prohibited")
    return parser


def main(argv=None):
    cli = argument_parser()
    args = cli.parse_args(argv)
    if args.limit is not None and args.limit < 1:
        cli.error("--limit must be positive")
    if args.retry_review and not args.resume:
        cli.error("--retry-review requires --resume")
    try:
        if args.manifest:
            if args.method or args.decode:
                raise ValueError("Use method/decode inside manifest, not CLI overrides")
            manifest_path = args.manifest.resolve()
            data = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
            if not isinstance(data, dict) or not isinstance(data.get("inputs"), list) or not data["inputs"]:
                raise ValueError("Manifest must contain a nonempty inputs list")
            sources = []
            for source in data["inputs"]:
                if not isinstance(source, dict) or not isinstance(source.get("path"), str):
                    raise ValueError("Each manifest input requires a path string")
                sources.append({**source, "path": str((manifest_path.parent / source["path"]).resolve())})
        else:
            sources = [{"path": str(args.input.resolve()), "method": args.method, "decode": args.decode}]
        records, failures = load_sources(sources, args.limit)
        if not records and not failures:
            raise ValueError("No caption rows found")
        prompt = load_prompt("extract", shots=args.shots)
        decomposer = None
        config = None
        if not args.prepare_only:
            config = load_api_config(args.api_config, model=args.model, base_url=args.base_url,
                                     timeout=args.timeout, max_tokens=args.max_tokens, retries=args.retries, thinking=args.thinking)
            decomposer = DeepSeekDecomposer(config, prompt,
                                           cache_dir=args.cache_dir, bypass_cache=args.bypass_cache)
        parser = SpacyParser(args.spacy_model)
        code_hashes = {path.name: digest(path.read_text(encoding="utf-8")) for path in sorted(Path(__file__).parent.glob("*.py"))}
        protocol = {"schema_version": SCHEMA_VERSION, "prompt_sha256": digest(prompt),
                    "prompt_version": PROMPT_VERSION, "shots": args.shots,
                    "code_hashes": code_hashes, "pos_parser": parser.identity,
                    "mode": "prepare" if args.prepare_only else "deepseek",
                    "independent_passes": 1, "pipeline": "entity-anchored-extraction+reference-validation+exact-dedup",
                    "agreement_policy": "instance identities preserved; exact structural dedup only; verification pending",
                    "model": config.model if config else None, "base_url": config.base_url if config else None,
                    "thinking": config.thinking if config else None,
                    "temperature": 0 if config else None,
                    "max_tokens": config.max_tokens if config else None}
        manifest = {"fingerprint": digest({"protocol": protocol, "records": records, "input_failures": failures}),
                    "created_at": datetime.now(timezone.utc).isoformat(), "protocol": protocol,
                    "sources": sources, "limit_per_file": args.limit, "input_records": len(records),
                    "input_failures": len(failures), "word_len_definition": "len(caption.split())",
                    "token_len_definition": "source-provided VLM generated token count; absent remains null",
                    "eos_step_definition": "source-provided only; absent remains null",
                    "prompt_frozen": True}
        manifest["cache_bypassed"] = args.bypass_cache
        def progress(index, total, sample_id, status):
            print(f"[{index}/{total}] {sample_id}: {status}", flush=True)
        result = run_pipeline(records, failures, parser, decomposer, args.output, manifest=manifest,
                              prompt=prompt, prepare_only=args.prepare_only, resume=args.resume, progress=progress,
                              retry_review=args.retry_review)
        print(json.dumps(result, ensure_ascii=False))
        return 1 if result["failed"] or result["needs_review"] or (result["pending"] and not args.prepare_only) else 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
