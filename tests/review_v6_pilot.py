"""Explicit assistant semantic adjudication of frozen v6 predictions; not an LLM API judge.

Every match is reviewable in semantic_review.json. Never changes predictions/references.
Compound statements receive at most one primary-proposition match under the frozen policy.
"""
import json
from collections import Counter
from pathlib import Path
from decomposition.storage import digest, write_json, write_csv

OUT = Path("outputs/semantic_core_v6/experiment_v1")


def prf(tp, fp, fn):
    return {"tp": tp, "fp": fp, "fn": fn, "precision": tp/(tp+fp) if tp+fp else None,
            "recall": tp/(tp+fn) if tp+fn else None,
            "f1": 2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None}


def main():
    refs = {r["id"]: r for r in json.loads((OUT / "references.json").read_text(encoding="utf-8"))}
    predictions = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in (OUT / "checkpoints").glob("*.json")}
    maps = {
        "a0_s0_r1": [1, 3, 6, 4, 5, 8],
        "a1_s0_r1": [1, 2, 3, 5, 7],
        "b0_s0_r1": [3, 4, 5], "b1_s0_r1": [3, 4, 5],
        "c0_s0_r1": [3, 4], "c1_s0_r1": [4, 5, 3],
        "d0_s0_r1": [1, 2, 5, 3, 4, 6], "d1_s0_r1": [1, 2, 5, 3, 4, 6, 7],
        "a0_s8_r1": list(range(1, 9)), "a0_s8_r2": list(range(1, 9)), "a0_s8_r3": list(range(1, 9)),
        "a1_s8_r1": list(range(1, 8)), "b0_s8_r1": list(range(1, 6)),
        "b1_s8_r1": [1, 2, 4, 3, 5], "c0_s8_r1": [1, 2, 3, 4, None],
        "c1_s8_r1": list(range(1, 6)), "d0_s8_r1": list(range(1, 7)), "d1_s8_r1": list(range(1, 8)),
        "para_a0_s8_r1": [3, 1, 2, 5, 4, 6, 8], "para_b0_s8_r1": [2, 1, 3, 4, 5],
        "para_c0_s8_r1": [2, 1, 3, None, 4]}
    notes = {
        "a0_s0_r1": "f3 retains coat modifiers as context; f6 combines standing+beside and receives only the primary location match g8. Coat existence and standing are not separately extracted.",
        "a1_s0_r1": "Wool remains a modifier, not an independent attribute fact. f5 combines posture and position; only g7 location matched.",
        "b0_s0_r1": "f1 receives the counting match, not an additional material/existence TP. f2 semantically expresses ceramic material but is wrongly labeled entity. No separate plate/counter existence.",
        "b1_s0_r1": "Same boundary errors as b0: counting retains material modifier, material fact mislabeled entity, two object-existence facts absent.",
        "c0_s0_r1": "Two semantically valid existence records use coarse category=entity and were quarantined. Main score uses validated output; raw recovery is separately reported. f2 combines sleeping/location, gets only g4.",
        "c1_s0_r1": "Two semantically valid existence records use coarse category=entity and were quarantined; not genuine semantic omissions. Report parsing penalty separately.",
        "c0_s8_r1": "f5 asserts under-table location. Frozen conservative scope requires may for both sleeping and location; f5 unmatched. This scope interpretation is a reference-policy sensitivity, not indisputable human gold.",
        "para_c0_s8_r1": "f4 asserts under-table location; same conservative frozen-scope mismatch as base c0. Their shared error does not reduce consistency but does reduce acceptance accuracy.",
        "para_a0_s8_r1": "All seven outputs matched; independent standing is absent after inversion 'Beside ... stands a girl'.",
        "para_b0_s8_r1": "made of ceramic and ceramic are accepted as semantically equivalent; ordering differences ignored.",
        "d0_s0_r1": "Small/metal modifiers used for reference context are not extra TPs; independent small and metal facts are present.",
        "d1_s0_r1": "Accept referential modifiers; negative red polarity is preserved. No image truth inference."}
    reviews = {}
    for job, indices in maps.items():
        row = predictions[job]
        ref_id = row.get("base", row["id"])
        ref = refs[ref_id]
        facts = row["document"]["facts"]
        assert len(facts) == len(indices), job
        nonnull = [g for g in indices if g is not None]
        assert len(set(nonnull)) == len(nonnull), job
        matches = []
        for f, g in zip(facts, indices):
            gold = ref["reference"][g-1] if g is not None else None
            matches.append({"prediction_id": f["id"], "prediction": f["fact"], "prediction_type": f["type"],
                            "reference_id": gold["id"] if gold else None,
                            "reference_meaning": gold["meaning"] if gold else None,
                            "reference_type": gold["type"] if gold else None,
                            "type_correct": f["type"] == gold["type"] if gold else None})
        reviews[job] = {"reference_sample": ref_id, "prediction_digest": digest(row),
                        "reference_digest": digest(ref), "matches": matches,
                        "notes": notes.get(job, "Primary propositions match; lexical paraphrases and fine categories do not affect the score.")}
    write_json(OUT / "semantic_review.json", {"reviewer": "assistant; same author as synthetic references, no independent human adjudication",
                                            "policy": "Frozen one-to-one primary atomic proposition matching, with strict coarse type as separate/joint score",
                                            "jobs": reviews})
    metrics = {}
    for shots in [0, 8]:
        scores = {t: [0, 0, 0] for t in ["entity", "relation", "attribute", "other"]}
        semantic_tp = semantic_pred = semantic_gold = classified = correct_class = 0
        invalid = 0
        for ref_id, ref in refs.items():
            job = f"{ref_id}_s{shots}_r1"; row = predictions[job]; rev = reviews[job]
            invalid += len(row["document"]["invalid_elements"])
            for t in scores:
                tp = sum(m["prediction_type"] == t and m["reference_type"] == t for m in rev["matches"])
                np = sum(f["type"] == t for f in row["document"]["facts"])
                ng = sum(g["type"] == t for g in ref["reference"])
                for i, v in enumerate([tp, np-tp, ng-tp]): scores[t][i] += v
            semantic_tp += sum(m["reference_type"] not in {None, "other"} and m["prediction_type"] != "other" for m in rev["matches"])
            semantic_pred += sum(f["type"] != "other" for f in row["document"]["facts"])
            semantic_gold += sum(g["type"] != "other" for g in ref["reference"])
            matched = [m for m in rev["matches"] if m["reference_type"] not in {None, "other"} and m["prediction_type"] != "other"]
            classified += len(matched); correct_class += sum(m["type_correct"] for m in matched)
        metrics[str(shots)] = {"n": 8, "by_type": {t: prf(*v) for t, v in scores.items()},
                              "main_joint": prf(*(sum(scores[t][i] for t in ["entity", "relation", "attribute"]) for i in range(3))),
                              "main_proposition_only": prf(semantic_tp, semantic_pred-semantic_tp, semantic_gold-semantic_tp),
                              "coarse_type_on_matched": {"correct": correct_class, "total": classified,
                                                         "accuracy": correct_class/classified}, "invalid_records": invalid}
    # These records have already been inspected above; diagnostic rescue never mutates runtime output.
    zero = metrics["0"]["main_joint"]
    metrics["raw_coarse_label_recovery_diagnostic"] = {"record_count": 4,
        "explanation": "Only c0/c1 raw category=entity records accepted as entity; all other rules unchanged. Not a rerun or patched production result.",
        "zero_shot_joint": prf(zero["tp"]+4, zero["fp"], zero["fn"]-4)}
    metrics["scope_sensitivity"] = {"explanation": "If c0 under-table location is treated as outside may's scope, 8-shot matches all 46 main facts. This is not the frozen main result and needs human adjudication.",
                                     "eight_shot_joint_if_location_asserted_allowed": prf(46, 0, 0)}
    # Map wording variants to the reviewed meaning, retaining unmatched actual claims explicitly.
    def tags(job, gold=False):
        review = reviews[job]
        if gold:
            return Counter((g["type"], g["meaning"]) for g in refs[review["reference_sample"]]["reference"] if g["type"] != "other")
        return Counter((m["prediction_type"], m["reference_meaning"] or m["prediction"])
                       for m in review["matches"] if m["prediction_type"] != "other")
    paraphrases = []
    for id in ["a0", "b0", "c0"]:
        a, b = tags(id + "_s8_r1"), tags("para_" + id + "_s8_r1")
        tp = sum((a & b).values())
        paraphrases.append({"id": id, **prf(tp, sum((b-a).values()), sum((a-b).values())),
                            "missing_meanings": list((a-b).elements())})
    metrics["semantic_paraphrase_agreement"] = {"pairs": paraphrases,
        "micro": prf(*(sum(p[k] for p in paraphrases) for k in ["tp", "fp", "fn"]))}
    changes = []
    for a, b in [("a0", "a1"), ("b0", "b1"), ("c0", "c1"), ("d0", "d1")]:
        def delta(gold):
            x, y = tags(a + "_s8_r1", gold), tags(b + "_s8_r1", gold)
            return Counter({("removed", k): v for k, v in (x-y).items()}) + Counter({("added", k): v for k, v in (y-x).items()})
        observed, expected = delta(False), delta(True)
        tp = sum((observed & expected).values())
        changes.append({"pair": [a, b], **prf(tp, sum((observed-expected).values()), sum((expected-observed).values())),
                        "expected": list(expected.elements()), "observed": list(observed.elements())})
    metrics["known_change_operations"] = {"pairs": changes, "micro": prf(*(sum(p[k] for p in changes) for k in ["tp", "fp", "fn"]))}
    structural = json.loads((OUT / "structural_metrics.json").read_text(encoding="utf-8"))
    repeats = structural["strict_wording_repeats"]
    total_shared = sum(p["shared"] for p in repeats)
    metrics["strict_wording_repeat_micro"] = {"shared": total_shared, "a": sum(p["a"] for p in repeats), "b": sum(p["b"] for p in repeats),
                                              "f1": 2*total_shared/sum(p["a"]+p["b"] for p in repeats),
                                              "note": "Ignores ID/order/fine category, normalizes punctuation/case; measures wording consistency, not correctness."}
    write_json(OUT / "semantic_metrics.json", metrics)
    csv_rows = []
    for shots in [0, 8]:
        for t, score in metrics[str(shots)]["by_type"].items():
            csv_rows.append({"shots": shots, "type": t, **score})
        csv_rows.append({"shots": shots, "type": "main_joint", **metrics[str(shots)]["main_joint"]})
    write_csv(OUT / "METRICS.csv", ["shots", "type", "tp", "fp", "fn", "precision", "recall", "f1"], csv_rows)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
