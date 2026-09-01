#!/usr/bin/env python3
"""Build deterministic prevalence and mechanism cohorts for termination audit."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--greedy-jsonl", type=Path, required=True)
    parser.add_argument("--beam-jsonl", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=1994)
    parser.add_argument("--prevalence-size", type=int, default=100)
    parser.add_argument("--mechanism-per-class", type=int, default=32)
    return parser.parse_args()


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
        duplicates = sorted({image_id for image_id in ids if ids.count(image_id) > 1})
        raise ValueError(f"{label} has duplicate image IDs: {duplicates[:10]}")


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def word_count(caption: str) -> int:
    return len(caption.strip().split())


def build_prevalence(
    greedy_rows: list[dict[str, Any]], size: int, seed: int
) -> list[int]:
    ids = np.array([int(row["image_id"]) for row in greedy_rows], dtype=np.int64)
    if size > len(ids):
        raise ValueError(f"prevalence size {size} exceeds {len(ids)} available IDs")
    rng = np.random.default_rng(seed)
    chosen = rng.choice(ids, size=size, replace=False)
    return [int(image_id) for image_id in chosen]


def build_mechanism(
    greedy_rows: list[dict[str, Any]],
    beam_rows: list[dict[str, Any]],
    per_class: int,
) -> tuple[list[dict[str, int]], dict[str, Any]]:
    greedy_lengths = {
        int(row["image_id"]): word_count(str(row["caption"])) for row in greedy_rows
    }
    collapse_ids = [
        int(row["image_id"]) for row in beam_rows if not str(row["caption"]).strip()
    ]
    noncollapse_ids = [
        int(row["image_id"]) for row in beam_rows if str(row["caption"]).strip()
    ]
    collapse_ids = [image_id for image_id in collapse_ids if image_id in greedy_lengths]
    noncollapse_ids = [image_id for image_id in noncollapse_ids if image_id in greedy_lengths]
    if len(collapse_ids) < per_class or len(noncollapse_ids) < per_class:
        raise ValueError(
            f"need {per_class} per class, found {len(collapse_ids)} collapse and "
            f"{len(noncollapse_ids)} non-collapse"
        )

    selected_collapse = collapse_ids[:per_class]
    available_controls = set(noncollapse_ids)
    pairs: list[dict[str, int]] = []
    for collapse_id in selected_collapse:
        target_length = greedy_lengths[collapse_id]
        control_id = min(
            available_controls,
            key=lambda candidate: (
                abs(greedy_lengths[candidate] - target_length),
                candidate,
            ),
        )
        available_controls.remove(control_id)
        pairs.append(
            {
                "collapse_image_id": collapse_id,
                "control_image_id": control_id,
                "collapse_greedy_words": target_length,
                "control_greedy_words": greedy_lengths[control_id],
            }
        )

    diagnostics = {
        "available_beam_rows": len(beam_rows),
        "available_collapse": len(collapse_ids),
        "available_noncollapse": len(noncollapse_ids),
        "mean_abs_match_gap_words": float(
            np.mean(
                [
                    abs(pair["collapse_greedy_words"] - pair["control_greedy_words"])
                    for pair in pairs
                ]
            )
        ),
    }
    return pairs, diagnostics


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    greedy_rows = read_jsonl(args.greedy_jsonl)
    beam_rows = read_jsonl(args.beam_jsonl)
    require_unique(greedy_rows, "greedy")
    require_unique(beam_rows, "beam")

    prevalence_ids = build_prevalence(greedy_rows, args.prevalence_size, args.seed)
    mechanism_pairs, diagnostics = build_mechanism(
        greedy_rows, beam_rows, args.mechanism_per_class
    )

    common = {
        "seed": args.seed,
        "greedy_source": str(args.greedy_jsonl.resolve()),
        "beam_source": str(args.beam_jsonl.resolve()),
        "greedy_rows": len(greedy_rows),
        "beam_rows": len(beam_rows),
    }
    prevalence = {
        **common,
        "cohort": "P",
        "selection": "uniform_without_replacement_from_greedy_500; outcome_blind",
        "image_ids": prevalence_ids,
    }
    prevalence["image_ids_sha256"] = canonical_hash(prevalence_ids)

    mechanism_ids = [pair["collapse_image_id"] for pair in mechanism_pairs] + [
        pair["control_image_id"] for pair in mechanism_pairs
    ]
    mechanism = {
        **common,
        "cohort": "M",
        "selection": "first collapse IDs in beam artifact; controls nearest-matched on greedy word count",
        "pairs": mechanism_pairs,
        "image_ids": mechanism_ids,
        "diagnostics": diagnostics,
    }
    mechanism["image_ids_sha256"] = canonical_hash(mechanism_ids)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.output_dir / "cohort_prevalence_100.json", prevalence)
    write_json(args.output_dir / "cohort_mechanism_64.json", mechanism)
    write_json(
        args.output_dir / "cohort_build_summary.json",
        {
            "prevalence_count": len(prevalence_ids),
            "mechanism_count": len(mechanism_ids),
            "mechanism_pairs": len(mechanism_pairs),
            "prevalence_unique": len(set(prevalence_ids)),
            "mechanism_unique": len(set(mechanism_ids)),
            "prevalence_hash": prevalence["image_ids_sha256"],
            "mechanism_hash": mechanism["image_ids_sha256"],
            **diagnostics,
        },
    )


if __name__ == "__main__":
    main()
