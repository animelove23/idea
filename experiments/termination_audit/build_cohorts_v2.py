#!/usr/bin/env python3
"""Freeze outcome-blind P and provenance-validated M00-matched M cohorts."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.termination_audit.provenance import code_provenance, source_record

PAPER_PROMPT = "Please help me describe the image in detail"
SUCCESS_STATUSES = {"ok", "short_nonempty", "eos_at_step1", "empty_after_decode"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--greedy-500-jsonl", type=Path, required=True)
    parser.add_argument("--beam-jsonl", type=Path, required=True)
    parser.add_argument("--m00-jsonl", type=Path)
    parser.add_argument("--m00-config", type=Path)
    parser.add_argument("--m00-summary", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=1994)
    parser.add_argument("--prevalence-size", type=int, default=100)
    parser.add_argument("--mechanism-per-class", type=int, default=32)
    parser.add_argument("--control-pool-size", type=int, default=128)
    return parser.parse_args()


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def write_frozen_json(path: Path, value: Any) -> str:
    payload = canonical_bytes(value)
    if path.exists():
        if path.read_bytes() == payload:
            return "reused_identical"
        raise FileExistsError(f"refusing to replace frozen artifact: {path}")
    path.write_bytes(payload)
    return "created"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON") from exc
            if "image_id" not in row or "caption" not in row:
                raise ValueError(f"{path}:{line_number}: missing image_id/caption")
            rows.append(row)
    return rows


def require_unique(rows: list[dict[str, Any]], label: str) -> None:
    ids = [int(row["image_id"]) for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{label} contains duplicate image IDs")


def row_source(path: Path, rows: list[dict[str, Any]], role: str) -> dict[str, Any]:
    record = source_record(path, role)
    record["rows"] = len(rows)
    return record


def select_prevalence(rows: list[dict[str, Any]], size: int, seed: int) -> list[int]:
    ids = np.asarray([int(row["image_id"]) for row in rows], dtype=np.int64)
    if len(ids) != 500:
        raise ValueError(f"expected frozen 500-image source, got {len(ids)}")
    if size > len(ids):
        raise ValueError("prevalence size exceeds source")
    return [int(value) for value in np.random.default_rng(seed).choice(ids, size, replace=False)]


def outcome_ids(rows: list[dict[str, Any]]) -> tuple[list[int], list[int]]:
    collapse = [int(row["image_id"]) for row in rows if not str(row["caption"]).strip()]
    noncollapse = [int(row["image_id"]) for row in rows if str(row["caption"]).strip()]
    return collapse, noncollapse


def validate_m00_provenance(
    candidate_path: Path,
    m00_path: Path,
    config_path: Path,
    summary_path: Path,
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    expected_method = {"vsv": False, "sla": False}
    if config.get("schema_version") != 2 or summary.get("schema_version") != 2:
        raise ValueError("M00 artifacts must use schema_version 2")
    if config.get("method") != expected_method:
        raise ValueError(f"M00 method mismatch: {config.get('method')}")
    if config.get("prompt") != PAPER_PROMPT:
        raise ValueError("M00 prompt does not match paper prompt")
    generation = config.get("generation", {})
    if generation.get("do_sample") is not False or generation.get("num_beams") != 1:
        raise ValueError("M00 generation must be deterministic greedy")
    if generation.get("max_new_tokens") != 512:
        raise ValueError("M00 max_new_tokens must equal 512")
    if config.get("candidate_manifest", {}).get("sha256") != source_record(
        candidate_path
    )["sha256"]:
        raise ValueError("M00 candidate-manifest hash mismatch")
    checkpoint_path = Path(str(config.get("checkpoint_path", ""))).resolve()
    if not checkpoint_path.is_dir():
        raise FileNotFoundError(f"M00 checkpoint path is unavailable: {checkpoint_path}")
    if summary.get("execution_status") != "DONE":
        raise ValueError("M00 summary is not DONE")
    if summary.get("run_id") != config.get("run_id"):
        raise ValueError("M00 config/summary run_id mismatch")
    if summary.get("target_records") != len(rows) or summary.get("written_records") != len(rows):
        raise ValueError("M00 target/written counts do not match JSONL")
    if summary.get("exception_records") != 0 or summary.get("missing_record_count") != 0:
        raise ValueError("M00 contains exception or missing records")
    if summary.get("result_file", {}).get("sha256") != source_record(m00_path)["sha256"]:
        raise ValueError("M00 JSONL hash does not match summary")
    if summary.get("config_file", {}).get("sha256") != source_record(config_path)["sha256"]:
        raise ValueError("M00 config hash does not match summary")
    statuses = {str(row.get("record_status")) for row in rows}
    if not statuses.issubset(SUCCESS_STATUSES):
        raise ValueError(f"M00 contains invalid statuses: {sorted(statuses - SUCCESS_STATUSES)}")
    row_ids = [int(row["image_id"]) for row in rows]
    candidate_ids = [int(value) for value in json.loads(candidate_path.read_text(encoding="utf-8"))["image_ids"]]
    if row_ids != candidate_ids:
        raise ValueError("M00 image IDs/order do not match the frozen candidate manifest")
    return {
        "jsonl": row_source(m00_path, rows, "m00_jsonl"),
        "config": source_record(config_path, "m00_config"),
        "summary": source_record(summary_path, "m00_summary"),
        "run_id": config["run_id"],
        "checkpoint_path": str(checkpoint_path),
    }


def decile_assignments(lengths: dict[int, int]) -> tuple[dict[int, int], list[float]]:
    values = np.asarray(list(lengths.values()), dtype=np.float64)
    edges = [float(value) for value in np.quantile(values, np.linspace(0, 1, 11))]
    interior = np.asarray(edges[1:-1])
    return (
        {key: int(np.searchsorted(interior, value, side="right")) for key, value in lengths.items()},
        edges,
    )


def match_pairs(
    collapse_ids: list[int], control_ids: list[int], rows: list[dict[str, Any]]
) -> tuple[list[dict[str, int]], dict[str, Any]]:
    captions = {int(row["image_id"]): str(row["caption"]) for row in rows}
    required = collapse_ids + control_ids
    missing = sorted(set(required) - set(captions))
    if missing:
        raise ValueError(f"M00 missing candidate IDs: {missing[:10]}")
    lengths = {image_id: len(captions[image_id].strip().split()) for image_id in required}
    deciles, edges = decile_assignments(lengths)
    available = set(control_ids)
    pairs: list[dict[str, int]] = []
    for collapse_id in collapse_ids:
        choices = [value for value in available if deciles[value] == deciles[collapse_id]]
        if not choices:
            raise ValueError(
                f"no same-decile control for collapse {collapse_id} in decile {deciles[collapse_id]}"
            )
        control_id = min(choices, key=lambda value: (abs(lengths[value] - lengths[collapse_id]), value))
        available.remove(control_id)
        pairs.append(
            {
                "collapse_image_id": collapse_id,
                "control_image_id": control_id,
                "collapse_m00_words": lengths[collapse_id],
                "control_m00_words": lengths[control_id],
                "length_decile": deciles[collapse_id],
            }
        )
    gaps = [abs(pair["collapse_m00_words"] - pair["control_m00_words"]) for pair in pairs]
    return pairs, {"decile_edges": edges, "mean_abs_match_gap_words": float(np.mean(gaps))}


def main() -> None:
    args = parse_args()
    supplied = [args.m00_jsonl, args.m00_config, args.m00_summary]
    if any(value is not None for value in supplied) and not all(value is not None for value in supplied):
        raise ValueError("--m00-jsonl, --m00-config, and --m00-summary must be supplied together")
    if args.control_pool_size < args.mechanism_per_class:
        raise ValueError("control pool must be at least mechanism-per-class")

    greedy_rows = read_jsonl(args.greedy_500_jsonl)
    beam_rows = read_jsonl(args.beam_jsonl)
    require_unique(greedy_rows, "greedy-500")
    require_unique(beam_rows, "beam")
    builder = code_provenance(
        [Path(__file__).resolve(), PROJECT_ROOT / "experiments/termination_audit/provenance.py"]
    )
    sources = {
        "greedy_500": row_source(args.greedy_500_jsonl, greedy_rows, "greedy_500"),
        "beam": row_source(args.beam_jsonl, beam_rows, "beam"),
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)

    prevalence_ids = select_prevalence(greedy_rows, args.prevalence_size, args.seed)
    prevalence = {
        "schema_version": 2,
        "cohort": "P",
        "seed": args.seed,
        "selection": "uniform_without_replacement_from_frozen_500_ID_source; outcome_blind",
        "image_ids": prevalence_ids,
        "image_ids_sha256": canonical_hash(prevalence_ids),
        "sources": sources,
        "builder": builder,
    }
    prevalence_path = args.output_dir / f"cohort_prevalence_{args.prevalence_size}_v2.json"
    prevalence_action = write_frozen_json(prevalence_path, prevalence)

    collapse_all, noncollapse_all = outcome_ids(beam_rows)
    collapse_ids = collapse_all[: args.mechanism_per_class]
    control_ids = noncollapse_all[: args.control_pool_size]
    if len(collapse_ids) != args.mechanism_per_class or len(control_ids) != args.control_pool_size:
        raise ValueError("insufficient collapse/control candidates")
    candidate_ids = collapse_ids + control_ids
    candidate = {
        "schema_version": 2,
        "cohort": "M00-baseline-candidates",
        "selection": "first collapse and noncollapse IDs in frozen beam artifact; M00-length blind",
        "collapse_image_ids": collapse_ids,
        "control_candidate_image_ids": control_ids,
        "image_ids": candidate_ids,
        "image_ids_sha256": canonical_hash(candidate_ids),
        "sources": sources,
        "builder": builder,
    }
    candidate_path = args.output_dir / "cohort_m00_candidates_v2.json"
    candidate_action = write_frozen_json(candidate_path, candidate)

    result: dict[str, Any] = {
        "schema_version": 2,
        "prevalence_path": str(prevalence_path),
        "prevalence_count": len(prevalence_ids),
        "candidate_path": str(candidate_path),
        "candidate_count": len(candidate_ids),
        "mechanism_ready": False,
    }
    runtime_actions = {
        "prevalence": prevalence_action,
        "candidate": candidate_action,
    }

    if all(value is not None for value in supplied):
        assert args.m00_jsonl and args.m00_config and args.m00_summary
        m00_rows = read_jsonl(args.m00_jsonl)
        require_unique(m00_rows, "M00")
        m00_source = validate_m00_provenance(
            candidate_path,
            args.m00_jsonl,
            args.m00_config,
            args.m00_summary,
            m00_rows,
        )
        pairs, diagnostics = match_pairs(collapse_ids, control_ids, m00_rows)
        mechanism_ids = [pair["collapse_image_id"] for pair in pairs] + [
            pair["control_image_id"] for pair in pairs
        ]
        mechanism = {
            "schema_version": 2,
            "cohort": "M",
            "selection": "collapse cases plus same-decile M00 greedy-length controls",
            "pairs": pairs,
            "image_ids": mechanism_ids,
            "image_ids_sha256": canonical_hash(mechanism_ids),
            "sources": {**sources, "m00": m00_source},
            "diagnostics": diagnostics,
            "builder": builder,
        }
        mechanism_path = args.output_dir / f"cohort_mechanism_{2 * args.mechanism_per_class}_v2.json"
        runtime_actions["mechanism"] = write_frozen_json(mechanism_path, mechanism)
        result.update(
            {
                "mechanism_ready": True,
                "mechanism_path": str(mechanism_path),
                "mechanism_count": len(mechanism_ids),
                **diagnostics,
            }
        )

    summary_name = "cohort_build_summary_v2.json" if result["mechanism_ready"] else "cohort_candidate_summary_v2.json"
    summary_path = args.output_dir / summary_name
    write_frozen_json(summary_path, result)
    print(json.dumps({**result, "runtime_actions": runtime_actions}, indent=2))


if __name__ == "__main__":
    main()
