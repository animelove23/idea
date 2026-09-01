#!/usr/bin/env python3
"""Analyze the 64-image fixed-prefix VSV x SLA factorial."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=1994)
    parser.add_argument("--bootstrap", type=int, default=10000)
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle]


def bootstrap_mean(values: list[float], count: int, seed: int) -> dict[str, float]:
    array = np.asarray(values, dtype=np.float64)
    rng = np.random.default_rng(seed)
    draws = rng.choice(array, size=(count, len(array)), replace=True).mean(axis=1)
    return {
        "mean": float(array.mean()),
        "std": float(array.std(ddof=1)) if len(array) > 1 else 0.0,
        "ci95_low": float(np.quantile(draws, 0.025)),
        "ci95_high": float(np.quantile(draws, 0.975)),
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    rows = read_jsonl(args.metrics)
    factorial = [row for row in rows if row.get("record_type") == "fixed_prefix_factorial"]
    statuses = [row for row in rows if row.get("record_type") == "image_status"]
    if len(statuses) != 64 or any(row["record_status"] != "ok" for row in statuses):
        raise ValueError("expected 64 successful image-status records")

    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in factorial:
        grouped[
            (
                row["cohort_class"],
                int(row["prefix_len"]),
                row["precision_path"],
                row["method"],
            )
        ].append(row)
    summary_rows: list[dict[str, Any]] = []
    for key, values in sorted(grouped.items()):
        cohort, prefix, precision, method = key
        summary_rows.append(
            {
                "cohort_class": cohort,
                "prefix_len": prefix,
                "precision_path": precision,
                "method": method,
                "n": len(values),
                "mean_eos_margin": float(np.mean([row["eos_margin"] for row in values])),
                "mean_eos_prob": float(np.mean([row["eos_prob"] for row in values])),
                "mean_eos_rank": float(np.mean([row["eos_rank"] for row in values])),
                "mean_entropy": float(np.mean([row["entropy"] for row in values])),
            }
        )

    by_image: dict[tuple[Any, ...], dict[str, float]] = defaultdict(dict)
    precision_pairs: dict[tuple[Any, ...], dict[str, float]] = defaultdict(dict)
    for row in factorial:
        by_image[
            (
                int(row["image_id"]),
                row["cohort_class"],
                int(row["prefix_len"]),
                row["precision_path"],
            )
        ][row["method"]] = float(row["eos_margin"])
        precision_pairs[
            (
                int(row["image_id"]),
                int(row["prefix_len"]),
                row["method"],
            )
        ][row["precision_path"]] = float(row["eos_margin"])

    effects: dict[tuple[str, int, str, str], list[float]] = defaultdict(list)
    for (_, cohort, prefix, precision), methods in by_image.items():
        if set(methods) != {"M00", "M01", "M10", "M11"}:
            raise ValueError("incomplete method quartet")
        derived = {
            "vsv_effect_M10_minus_M00": methods["M10"] - methods["M00"],
            "sla_effect_M01_minus_M00": methods["M01"] - methods["M00"],
            "combined_effect_M11_minus_M00": methods["M11"] - methods["M00"],
            "interaction": (
                methods["M11"] - methods["M10"] - methods["M01"] + methods["M00"]
            ),
        }
        for name, value in derived.items():
            effects[(cohort, prefix, precision, name)].append(value)

    effect_rows: list[dict[str, Any]] = []
    for index, (key, values) in enumerate(sorted(effects.items())):
        cohort, prefix, precision, effect = key
        stats = bootstrap_mean(values, args.bootstrap, args.seed + index)
        effect_rows.append(
            {
                "cohort_class": cohort,
                "prefix_len": prefix,
                "precision_path": precision,
                "effect": effect,
                "n": len(values),
                **stats,
            }
        )

    precision_diffs = []
    for pair in precision_pairs.values():
        if set(pair) == {"release_native", "fp32_projection"}:
            precision_diffs.append(abs(pair["release_native"] - pair["fp32_projection"]))

    primary = [
        row
        for row in effect_rows
        if row["precision_path"] == "fp32_projection" and row["effect"] == "interaction"
    ]
    analysis = {
        "execution": {"images": len(statuses), "exceptions": 0},
        "factorial_rows": len(factorial),
        "precision_agreement": {
            "mean_abs_eos_margin_difference": float(np.mean(precision_diffs)),
            "max_abs_eos_margin_difference": float(np.max(precision_diffs)),
        },
        "primary_fp32_interactions": primary,
    }

    summary_csv = args.output_dir / "method_summary.csv"
    effects_csv = args.output_dir / "effect_summary_bootstrap.csv"
    analysis_json = args.output_dir / "analysis.json"
    report_md = args.output_dir / "RESULTS.md"
    write_csv(summary_csv, summary_rows)
    write_csv(effects_csv, effect_rows)
    analysis_json.write_text(json.dumps(analysis, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Fixed-prefix factorial results (64 images)",
        "",
        "- Completed: 64/64; exceptions: 0.",
        f"- Native-vs-FP32 EOS-margin mean absolute difference: {analysis['precision_agreement']['mean_abs_eos_margin_difference']:.6f}.",
        "",
        "## FP32 interaction by cohort and prefix",
        "",
        "| Cohort | k | Mean interaction | 95% bootstrap CI |",
        "|---|---:|---:|---:|",
    ]
    for row in primary:
        lines.append(
            f"| {row['cohort_class']} | {row['prefix_len']} | {row['mean']:.4f} | "
            f"[{row['ci95_low']:.4f}, {row['ci95_high']:.4f}] |"
        )
    lines.extend(
        [
            "",
            "Positive interaction means M11 shifts EOS margin upward beyond additive VSV and SLA effects; negative means sub-additive/counteracting interaction.",
            "",
            "Full method means are in `method_summary.csv`; all main effects and interactions are in `effect_summary_bootstrap.csv`.",
        ]
    )
    report_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(analysis, indent=2))


if __name__ == "__main__":
    main()
