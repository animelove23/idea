"""Offline audit of frozen independent runs; no model calls or semantic judge."""
import argparse
from collections import Counter
from itertools import combinations
import json
import re
from pathlib import Path

from decomposition.config import FACT_TYPES, load_prompt
from decomposition.storage import digest
from tests.evaluate_minimal import compare_runs, evaluate_gold, load_run


def limited_equivalence(fact):
    """Two explicit harmless forms only; not a general entailment judge."""
    text = " ".join(fact["fact"].lower().rstrip(".").split())
    text = re.sub(r"\bslice of lemon\b", "lemon slice", text)
    if fact["type"] == "count":
        text = re.sub(r"\s+(?:exist|exists|are present)$", "", text)
    return fact["type"], text


def report(gold_dir, run_dirs):
    directories = [gold_dir, *run_dirs]
    manifests = [json.loads((p / "run_manifest.json").read_text(encoding="utf-8")) for p in directories]
    protocols = [m["protocol"] for m in manifests]
    assert all(p == protocols[0] for p in protocols), "Mixed protocol versions"
    assert all(m["cache_bypassed"] for m in manifests), "Independent runs must bypass cache"
    assert protocols[0]["thinking"] == "disabled" and protocols[0]["temperature"] == 0
    source = Path(__file__).resolve().parents[1] / "decomposition"
    assert protocols[0]["code_hashes"] == {p.name: digest(p.read_text(encoding="utf-8")) for p in sorted(source.glob("*.py"))}
    assert protocols[0]["prompt_sha256"] == digest(load_prompt("extract"))
    runs = [load_run(p) for p in run_dirs]
    assert all(set(r) == set(runs[0]) for r in runs), "Different samples"
    for key in runs[0]:
        assert len({r[key]["caption"]["caption"] for r in runs}) == 1
    summaries = {p.name: json.loads((p / "summary.json").read_text(encoding="utf-8")) for p in directories}
    assert all(s["pending"] == 0 for s in summaries.values()), "Incomplete run"
    pairs = [{"runs": [a.name, b.name], **compare_runs(a, b)} for a, b in combinations(run_dirs, 2)]
    equivalent_pairs = []
    for i, j in combinations(range(len(runs)), 2):
        same = common = union = compared = 0
        for key in runs[i]:
            a, b = runs[i][key], runs[j][key]
            if a["status"] != "success" or b["status"] != "success":
                continue
            ca, cb = (Counter(limited_equivalence(f) for f in d["facts"]) for d in (a, b))
            compared += 1
            same += ca == cb
            common += sum((ca & cb).values())
            union += sum((ca | cb).values())
        equivalent_pairs.append({"runs": [run_dirs[i].name, run_dirs[j].name], "compared": compared,
                                 "same_fact_sets": same, "micro_jaccard": common / union if union else None})
    rows, totals = [], []
    for run in runs:
        totals.append(dict(Counter(f["type"] for d in run.values() if d["status"] == "success" for f in d["facts"])))
    for key in sorted(runs[0]):
        versions = [r[key] for r in runs]
        counts = [{k: sum(f["type"] == k for f in v["facts"]) for k in FACT_TYPES}
                  if v["status"] == "success" else None for v in versions]
        rows.append({"sample_id": key, "caption": versions[0]["caption"]["caption"],
                     "statuses": [v["status"] for v in versions], "type_counts": counts,
                     "same_type_counts": all(c is not None and c == counts[0] for c in counts),
                     "facts_by_run": [v["facts"] for v in versions],
                     "errors": [v.get("error") for v in versions]})
    return {"scope": "Literal repeatability and type counts; no image truth, held-out accuracy or semantic equivalence score",
            "protocol": protocols[0], "current_code_matches": True, "cache_bypassed": True,
            "run_provenance": {p.name: {k: m.get(k) for k in ("replay_of", "replay_zero_network", "source_api_calls", "source_fingerprint")}
                               for p, m in zip(directories, manifests)},
            "summaries": summaries, "gold": evaluate_gold(gold_dir), "pairs": pairs,
            "limited_equivalence_rules": ["slice of lemon = lemon slice", "count trailing exist/exists/are present optional"],
            "limited_equivalence_pairs": equivalent_pairs, "type_totals": totals, "samples": rows}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--gold", type=Path, required=True)
    cli.add_argument("--runs", type=Path, nargs=3, required=True)
    cli.add_argument("--output", type=Path, required=True)
    args = cli.parse_args()
    result = report(args.gold, args.runs)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"gold": [result["gold"]["passed"], result["gold"]["total"]],
                      "pairs": [{k: p[k] for k in ("runs", "compared", "exact_fact_sets", "micro_jaccard")} for p in result["pairs"]]}))
