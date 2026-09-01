#!/usr/bin/env python3
"""Freeze outcome-blind prevalence IDs and M00-matched mechanism IDs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--greedy-500-jsonl", type=Path, required=True)
    parser.add_argument("--beam-jsonl", type=Path, required=True)
    parser.add_argument("--m00-jsonl", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=1994)
    parser.add_argument("--prevalence-size", type=int, default=100)
    parser.add_argument("--mechanism-per-class", type=int, default=32)
    parser.add_argument("--control-pool-size", type=int, default=128)
    return parser.parse_args()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
        seen: set[int] = set()
        duplicates: set[int] = set()
        for image_id in ids:
            if image_id in seen:
                duplicates.add(image_id)
            seen.add(image_id)
        raise ValueError(f"{label} duplicate image IDs: {sorted(duplicates)[:10]}")


def source_record(path: Path, rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "path": str(path.resolve()),
        "rows": len(rows),
        "sha256": file_sha256(path),
    }


def word_count(caption: str) -> int:
    return len(caption.strip().split())


def select_prevalence(
    greedy_rows: list[dict[str, Any]], size: int, seed: int
) -> list[int]:
    ids = np.asarray([int(row["image_id"]) for row in greedy_rows], dtype=np.int64)
    if len(ids) != 500:
        raise ValueError(f"expected frozen 500-image source, got {len(ids)} rows")
    if size > len(ids):
        raise ValueError(f"prevalence size {size} exceeds source size {len(ids)}")
    rng = np.random.default_rng(seed)
    return [int(value) for value in rng.choice(ids, size=size, replace=False)]


def outcome_ids(beam_rows: list[dict[str, Any]]) -> tuple[list[int], list[int]]:
    collapse = [
        int(row["image_id"]) for row in beam_rows if not str(row["caption"]).strip()
    ]
    noncollapse = [
        int(row["image_id"]) for row in beam_rows if str(row["caption"]).strip()
    ]
    return collapse, noncollapse


def build_candidate_manifest(
    beam_rows: list[dict[str, Any]],
    per_class: int,
    control_pool_size: int,
    sources: dict[str, Any],
) -> dict[str, Any]:
    collapse, noncollapse = outcome_ids(beam_rows)
    if len(collapse) < per_class or len(noncollapse) < control_pool_size:
        raise ValueError(
            f"insufficient candidates: collapse={len(collapse)}, noncollapse={len(noncollapse)}"
        )
    collapse_ids = collapse[:per_class]
    control_candidate_ids = noncollapse[:control_pool_size]
    image_ids = collapse_ids + control_candidate_ids
    return {
        "cohort": "M00-baseline-candidates",
        "selection": (
            "first collapse IDs and first noncollapse control candidates in frozen beam artifact; "
            "selection does not use M00 caption length"
        ),
        "collapse_image_ids": collapse_ids,
        "control_candidate_image_ids": control_candidate_ids,
        "image_ids": image_ids,
        "image_ids_sha256": canonical_hash(image_ids),
        "sources": sources,
    }


def decile_assignments(lengths: dict[int, int]) -> tuple[dict[int, int], list[float]]:
    values = np.asarray(list(lengths.values()), dtype=np.float64)
    edges = [float(value) for value in np.quantile(values, np.linspace(0, 1, 11))]
    interior = np.asarray(edges[1:-1])
    assignments = {
        image_id: int(np.searchsorted(interior, length, side="right"))
        for image_id, length in lengths.items()
    }
    return assignments, edges


def match_mechanism(
    candidate: dict[str, Any], m00_rows: list[dict[str, Any]], per_class: int
) -> tuple[list[dict[str, int]], dict[str, Any]]:
    ok_rows = [row for row in m00_rows if row.get("record_status", "ok") == "ok"]
    lengths = {
        int(row["image_id"]): word_count(str(row["caption"])) for row in ok_rows
    }
    required_ids = [int(value) for value in candidate["image_ids"]]
    missing = sorted(set(required_ids) - set(lengths))
    if missing:
        raise ValueError(f"M00 baseline missing {len(missing)} candidate IDs: {missing[:10]}")
    restricted_lengths = {image_id: lengths[image_id] for image_id in required_ids}
    deciles, edges = decile_assignments(restricted_lengths)
    available = {int(value) for value in candidate["control_candidate_image_ids"]}
    pairs: list[dict[str, int]] = []
    for collapse_id in [int(value) for value in candidate["collapse_image_ids"][:per_class]]:
        same_decile = [
            control_id
            for control_id in available
            if deciles[control_id] == deciles[collapse_id]
        ]
        if not same_decile:
            raise ValueError(
                f"no remaining same-decile control for collapse image {collapse_id} "
                f"(decile {deciles[collapse_id]})"
            )
        control_id = min(
            same_decile,
            key=lambda value: (abs(lengths[value] - lengths[collapse_id]), value),
        )
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
    diagnostics = {
        "decile_edges": edges,
        "mean_abs_match_gap_words": float(
            np.mean(
                [
                    abs(pair["collapse_m00_words"] - pair["control_m00_words"])
                    for pair in pairs
                ]
            )
        ),
    }
    return pairs, diagnostics


def main() -> None:
    args = parse_args()
    if args.control_pool_size < args.mechanism_per_class:
        raise ValueError("control pool must be at least mechanism-per-class")
    greedy_rows = read_jsonl(args.greedy_500_jsonl)
    beam_rows = read_jsonl(args.beam_jsonl)
    require_unique(greedy_rows, "greedy-500")
    require_unique(beam_rows, "beam")
    sources = {
        "greedy_500": source_record(args.greedy_500_jsonl, greedy_rows),
        "beam": source_record(args.beam_jsonl, beam_rows),
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)

    prevalence_ids = select_prevalence(greedy_rows, args.prevalence_size, args.seed)
    prevalence = {
        "cohort": "P",
        "seed": args.seed,
        "selection": "uniform_without_replacement_from_frozen_500_ID_source; outcome_blind",
        "image_ids": prevalence_ids,
        "image_ids_sha256": canonical_hash(prevalence_ids),
        "sources": sources,
    }
    prevalence_path = args.output_dir / f"cohort_prevalence_{args.prevalence_size}.json"
    prevalence_action = write_frozen_json(prevalence_path, prevalence)

    candidate = build_candidate_manifest(
        beam_rows, args.mechanism_per_class, args.control_pool_size, sources
    )
    candidate_path = args.output_dir / "cohort_m00_candidates.json"
    candidate_action = write_frozen_json(candidate_path, candidate)

    result: dict[str, Any] = {
        "prevalence_path": str(prevalence_path),
        "prevalence_action": prevalence_action,
        "prevalence_count": len(prevalence_ids),
        "candidate_path": str(candidate_path),
        "candidate_action": candidate_action,
        "candidate_count": len(candidate["image_ids"]),
        "mechanism_ready": False,
    }

    if args.m00_jsonl is not None:
        m00_rows = read_jsonl(args.m00_jsonl)
        require_unique(m00_rows, "M00")
        sources["m00"] = source_record(args.m00_jsonl, m00_rows)
        pairs, diagnostics = match_mechanism(
            candidate, m00_rows, args.mechanism_per_class
        )
        mechanism_ids = [pair["collapse_image_id"] for pair in pairs] + [
            pair["control_image_id"] for pair in pairs
        ]
        mechanism = {
            "cohort": "M",
            "selection": (
                "collapse cases from frozen beam artifact; controls deterministically matched "
                "within M00-baseline word-length deciles"
            ),
            "pairs": pairs,
            "image_ids": mechanism_ids,
            "image_ids_sha256": canonical_hash(mechanism_ids),
            "sources": sources,
            "diagnostics": diagnostics,
        }
        mechanism_path = args.output_dir / f"cohort_mechanism_{2 * args.mechanism_per_class}.json"
        mechanism_action = write_frozen_json(mechanism_path, mechanism)
        result.update(
            {
                "mechanism_ready": True,
                "mechanism_path": str(mechanism_path),
                "mechanism_action": mechanism_action,
                "mechanism_count": len(mechanism_ids),
                **diagnostics,
            }
        )

    summary_name = "cohort_build_summary.json" if args.m00_jsonl else "cohort_candidate_summary.json"
    summary_path = args.output_dir / summary_name
    write_frozen_json(summary_path, result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
