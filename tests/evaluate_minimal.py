"""Offline, strict text repeatability and fixed semantic regression checks."""
import argparse
from collections import Counter
import json
from pathlib import Path

from decomposition.quality import normalized_text, semantic_signature


def load_run(directory):
    result = {data["caption"]["sample_id"]: data
            for path in (Path(directory) / "checkpoints").glob("*.json")
            for data in [json.loads(path.read_text(encoding="utf-8"))]}
    if any("document" in sample for sample in result.values()):
        raise ValueError("This flat-fact evaluator/replayer is for v3 archives only. entity-facts-v4 requires entity-aware human gold and matching; do not compare local eIDs across captions.")
    return result


def evaluate_gold(directory, fixture=Path(__file__).parent / "fixtures/minimal_cases.jsonl"):
    saved = {s["caption"]["image_id"]: s for s in load_run(directory).values()}
    cases = [json.loads(line) for line in Path(fixture).read_text(encoding="utf-8").splitlines()]
    results = []
    for case in cases:
        sample = saved.get(case["image_id"], {})
        errors = []
        if "expected_review" in case:
            if sample.get("status") != "needs_review" or sample.get("error", {}).get("error") != case["expected_review"]:
                errors.append("expected repetition quarantine")
        elif sample.get("status") != "success":
            errors.append("missing or not successful")
        else:
            expected = Counter((t, normalized_text(f)) for t, f in case["expected_facts"])
            observed = Counter(semantic_signature(f) for f in sample["facts"])
            if expected != observed:
                errors.append({"missing": list((expected - observed).elements()),
                               "extra": list((observed - expected).elements())})
        results.append({"case": case["image_id"], "passed": not errors, "errors": errors})
    return {"passed": sum(r["passed"] for r in results), "total": len(results), "cases": results,
            "scope": "Prewritten fixed examples; strict wording; not image truth or held-out accuracy"}


def compare_runs(first, second):
    left, right = load_run(first), load_run(second)
    results = []
    for key in sorted(left.keys() | right.keys()):
        a, b = left.get(key), right.get(key)
        if not a or not b or a["status"] != "success" or b["status"] != "success":
            results.append({"sample_id": key, "compared": False,
                            "statuses": [a.get("status") if a else None, b.get("status") if b else None]})
            continue
        ca = Counter(semantic_signature(f) for f in a["facts"])
        cb = Counter(semantic_signature(f) for f in b["facts"])
        common, union = sum((ca & cb).values()), sum((ca | cb).values())
        results.append({"sample_id": key, "compared": True, "exact_fact_set": ca == cb,
                        "common": common, "union": union, "jaccard": common / union if union else 1,
                        "only_first": list((ca - cb).elements()), "only_second": list((cb - ca).elements())})
    comparable = [r for r in results if r["compared"]]
    union = sum(r["union"] for r in comparable)
    return {"compared": len(comparable), "excluded": len(results) - len(comparable),
            "exact_fact_sets": sum(r["exact_fact_set"] for r in comparable),
            "micro_jaccard": sum(r["common"] for r in comparable) / union if union else None,
            "cases": results, "scope": "Exact type+normalized text; excludes IDs and order. Paraphrases count as differences. Not semantic accuracy."}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("first", type=Path)
    cli.add_argument("--second", type=Path)
    args = cli.parse_args()
    result = compare_runs(args.first, args.second) if args.second else evaluate_gold(args.first)
    path = args.first / ("repeatability.json" if args.second else "gold_evaluation.json")
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not args.second:
        raise SystemExit(0 if result["passed"] == result["total"] else 1)
