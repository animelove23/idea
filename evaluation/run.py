"""Durable downstream runner for already independently decomposed v6 pairs."""
import argparse
import copy
import json
from collections import Counter
from pathlib import Path

from decomposition.config import API_CONFIG_PATH, load_api_config
from decomposition.storage import digest, output_lock, write_json, write_jsonl
from . import VERSION
from .alignment_core import PairAligner, fallback_alignments, STATUSES
from .common import JsonStage, StageFailure, document_context, require
from .coverage import CoverageAudit
from .verifier import pending_claims


def load_pairs(path):
    pairs = [json.loads(line) for line in Path(path).read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    seen = set()
    for p in pairs:
        require(isinstance(p.get("pair_id"), str) and p["pair_id"] not in seen, "unique pair_id required")
        seen.add(p["pair_id"])
        for side in ["original", "steer"]:
            document_context(p[side]); require(isinstance(p[side].get("id"), str), "caption id required")
    return pairs


def prepare(pair_path, out, shots=0):
    require(shots in (0, 8), "only zero or eight shots supported")
    pairs = load_pairs(pair_path)
    require(not out.exists(), "Use a fresh output directory")
    out.mkdir(parents=True)
    for name in ["inputs", "coverage", "entities", "alignments", "started", "frozen"]: (out / name).mkdir()
    paths = list(Path("evaluation").glob("*.py")) + list(Path("evaluation/prompts").glob("*.txt"))
    paths += list(Path("evaluation/examples").glob("*.jsonl"))
    paths += [p for p in Path("decomposition/v6").iterdir() if p.is_file()]
    paths += [Path("decomposition/semantic_decomposer.py"), Path("decomposition/config.py")]
    hashes = {}
    for path in paths:
        hashes[str(path)] = digest(path.read_text(encoding="utf-8"))
        target = out / "frozen" / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())
    write_jsonl(out / "pairs.jsonl", pairs)
    docs = {digest(p[side]): p[side] for p in pairs for side in ["original", "steer"]}
    for key, doc in docs.items(): write_json(out / "inputs" / (key + ".json"), doc)
    manifest = {"version": VERSION, "shots": shots, "pairs_digest": digest(pairs), "files": hashes, "pairs": len(pairs),
                "unique_captions": len(docs), "maximum_requests": len(docs) + 2*len(pairs),
                "thinking": "disabled", "base_url": "https://api.deepseek.com", "workers": 1,
                "existing_decomposer": "unchanged; using frozen independent v6 outputs, no decomposition calls",
                "coverage_policy": "one attempt per unique input document; append-only; no retries or automatic prompt changes",
                "visual_verifier": "pending interface only, no image reads or requests"}
    write_json(out / "manifest.json", manifest)
    print(json.dumps(manifest | {"files": f"{len(hashes)} frozen files"}), flush=True)


def checkpoint(out, stage_name, key, function):
    destination = out / stage_name / (key + ".json")
    if destination.exists(): return json.loads(destination.read_text(encoding="utf-8"))
    marker = out / "started" / (stage_name + "_" + key + ".json")
    require(not marker.exists(), f"Uncertain earlier request: {marker}. Inspect before any repeated call.")
    write_json(marker, {"stage": stage_name, "key": key, "state": "started"})
    result = function()
    write_json(destination, result)
    return result


def execute(out, stage=None):
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    pairs = load_pairs(out / "pairs.jsonl")
    require(digest(pairs) == manifest["pairs_digest"], "inputs changed since freeze")
    for name, h in manifest["files"].items(): require(digest(Path(name).read_text(encoding="utf-8")) == h, f"code changed: {name}")
    if stage is None:
        config = load_api_config(API_CONFIG_PATH, timeout=120)
        require(config.base_url.rstrip("/") == manifest["base_url"], "expected official DeepSeek destination")
        identity = {"model": config.model, "max_tokens": config.max_tokens, "base_url": config.base_url,
                    "temperature": 0, "thinking": "disabled", "timeout": config.timeout}
        path = out / "execution_config.json"
        if path.exists(): require(json.loads(path.read_text()) == identity, "execution config changed")
        else: write_json(path, identity)
        examples = {}
        if manifest.get("shots", 0):
            for name in ("coverage", "entities", "alignment"):
                examples[name] = [json.loads(line) for line in Path(f"evaluation/examples/{name}.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
                require(len(examples[name]) == manifest["shots"], "frozen example count mismatch")
        stage = JsonStage(config, examples=examples)
    coverage = CoverageAudit(stage); aligner = PairAligner(stage)
    with output_lock(out):
        for pair in pairs:
            augmented = {}
            for side in ["original", "steer"]:
                doc = pair[side]; key = digest(doc)
                cov = checkpoint(out, "coverage", key, lambda doc=doc: coverage.run(doc))
                augmented[side] = cov["augmented_document"]
                print(pair["pair_id"], side, "coverage", cov["status"], len(cov["added_facts"]), flush=True)
            original, steer = augmented["original"], augmented["steer"]
            key = digest(pair["pair_id"])
            def entities():
                try: return {"pair_id": pair["pair_id"], **aligner.entities(original, steer)}
                except StageFailure as exc: return {"pair_id": pair["pair_id"], "status": "failed", "error": str(exc), "audit": exc.audit}
            sidecar = checkpoint(out, "entities", key, entities)
            print(pair["pair_id"], "entities", sidecar["status"], flush=True)
            def facts():
                if sidecar["status"] == "failed":
                    return {"pair_id": pair["pair_id"], "status": "failed", "error": "entity alignment failed",
                            "fact_alignment": fallback_alignments(original, steer), "audit": {"api_calls": 0}}
                try: return aligner.facts(pair["pair_id"], original, steer, sidecar)
                except StageFailure as exc:
                    return {"pair_id": pair["pair_id"], "status": "failed", "error": str(exc), "audit": exc.audit,
                            "entity_alignment": sidecar["entity_alignment"], "fact_alignment": fallback_alignments(original, steer)}
            result = checkpoint(out, "alignments", key, facts)
            print(pair["pair_id"], "facts", result["status"], flush=True)
            report(out)


def report(out):
    pairs = load_pairs(out / "pairs.jsonl")
    coverage = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((out / "coverage").glob("*.json"))]
    entities = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((out / "entities").glob("*.json"))]
    alignment = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((out / "alignments").glob("*.json"))]
    cmap = {c["input_digest"]: c for c in coverage}; amap = {a["pair_id"]: a for a in alignment}
    verification = []; excluded_facts = []
    counts = Counter(); main_counts = Counter(); side_counts = {s: Counter() for s in ["original", "steer"]}
    for pair in pairs:
        if pair["pair_id"] not in amap: continue
        docs = {s: cmap[digest(pair[s])]["augmented_document"] for s in ["original", "steer"]}
        eligible = {s: {fid for row in amap[pair['pair_id']]['fact_alignment'] if row['in_main']
                        for fid in row[s+'_fact_ids']} for s in docs}
        verification_docs = {s: {**doc, 'facts': [f for f in doc['facts'] if f['id'] in eligible[s]]} for s,doc in docs.items()}
        verification.extend(pending_claims(pair['pair_id'], verification_docs['original'], verification_docs['steer']))
        for row in amap[pair['pair_id']]['fact_alignment']:
            if not row['in_main']:
                for s,doc in docs.items():
                    for f in doc['facts']:
                        if f['id'] in row[s+'_fact_ids']:
                            excluded_facts.append(dict(pair_id=pair['pair_id'],side=s,fact=f,reason=row['reason'],status=row['status']))
        for row in amap[pair["pair_id"]]["fact_alignment"]:
            counts[row["status"]] += 1
            if row["in_main"]: main_counts[row["status"]] += 1
            for side, doc in docs.items():
                ftype = {f["id"]: f["type"] for f in doc["facts"]}
                if row['in_main']:
                    side_counts[side][row["status"]] += sum(ftype[f] != "other" for f in row[side + "_fact_ids"])
    write_jsonl(out / "coverage.jsonl", coverage)
    write_jsonl(out / "coverage_augmented.jsonl", [c["augmented_document"] for c in coverage])
    write_jsonl(out / "entity_alignment.jsonl", entities)
    write_jsonl(out / "alignment.jsonl", alignment)
    write_jsonl(out / "verification_pending.jsonl", verification)
    write_jsonl(out / "excluded_facts.jsonl", excluded_facts)
    stats = {"pairs_planned": len(pairs), "pairs_completed": len(alignment), "coverage_captions": len(coverage),
             "coverage_added": sum(len(c["added_facts"]) for c in coverage),
             "coverage_status": dict(Counter(c["status"] for c in coverage)),
             "entity_status": dict(Counter(e["status"] for e in entities)),
             "alignment_status": dict(Counter(a["status"] for a in alignment)),
             "alignment_rows_all": {s: counts[s] for s in sorted(STATUSES)},
             "alignment_rows_main": {s: main_counts[s] for s in sorted(STATUSES)},
             "main_fact_status_counts": {side: {s: c[s] for s in sorted(STATUSES)} for side, c in side_counts.items()},
             "extraction_gap_rows": sum(row["reason"] == "extraction_gap" for a in alignment for row in a["fact_alignment"]),
             "contextual_references": sum(len(a.get('related_correspondences', [])) for a in alignment),
             "equivalent_fact_groups": sum(bool(r.get('equivalent_fact_group')) for a in alignment for r in a['fact_alignment']),
             "api_calls": sum(r.get("audit", {}).get("api_calls", 0) for r in coverage + entities + alignment),
             "pending_claims": len(verification), "excluded_facts":len(excluded_facts),
             "note": "Alignment outputs are not human gold; other/extraction_gap/technical failures are excluded from main changes and pending verification, retained in excluded_facts.jsonl. All verifier labels pending."}
    write_json(out / "summary.json", stats)
    lines = ["# Coverage / Alignment 首轮测试", "", "Decomposer、v6 few-shot 和既有事实均未修改；使用先前独立拆分的真实 caption。所有视觉验证保持 pending。", "",
             "## 状态计数", "", "```json", json.dumps(stats, ensure_ascii=False, indent=2), "```", "",
             "注意：alignment 行数与事实数不同，ambiguous 可以多对多；主线不统计 other。未完成/失败另列，不用它们制造信息删除。", "",
             "## Coverage 追加事实", ""]
    for cov in coverage:
        lines += ["### " + cov["caption_id"] + " — " + cov["status"], ""]
        for f in cov["added_facts"]:
            lines += [f"- {f['id']} [{f['type']}] {f['fact']}（source: {f['source']}）"]
        if not cov["added_facts"]: lines += ["无已接收新增事实。"]
        if cov.get("error"): lines += ["失败：" + cov["error"]]
        if cov.get("rejected_additions"): lines += ["拒绝的候选：" + json.dumps(cov["rejected_additions"], ensure_ascii=False)]
        lines += [""]
    lines += ["## Entity Alignment", ""]
    for ent in entities:
        lines += ["### " + ent["pair_id"], "", "```json", json.dumps({k: v for k, v in ent.items() if k != "audit"}, ensure_ascii=False, indent=2), "```", ""]
    lines += ["## Fact Alignment（完整状态；非人工准确率）", ""]
    for pair in pairs:
        if pair["pair_id"] not in amap: continue
        a = amap[pair["pair_id"]]
        lookup = {side: {f["id"]: f["fact"] for f in cmap[digest(pair[side])]["augmented_document"]["facts"]} for side in ["original", "steer"]}
        lines += ["### " + pair["pair_id"] + " — " + a["status"], "", "| status / reason | Vanilla | Steer |", "| --- | --- | --- |"]
        for row in a["fact_alignment"]:
            values = [row["status"] + " / " + row["reason"]] + [" ; ".join(fid + ": " + lookup[s][fid] for fid in row[s + "_fact_ids"]) for s in ["original", "steer"]]
            lines += ["| " + " | ".join(v.replace("|", "\\|").replace("\n", " ") for v in values) + " |"]
            if row["reason"] == "extraction_gap": lines += ["", "对侧原文证据：" + json.dumps(row["evidence"], ensure_ascii=False), ""]
        if a.get("error"): lines += ["失败：" + a["error"]]
        if a.get('related_correspondences'):
            lines += ['', '关联引用（不重复计作主对齐；语气等限定保留）：', '```json', json.dumps(a['related_correspondences'], ensure_ascii=False, indent=2), '```']
        if a.get("rejected_alignments"): lines += ["拒绝的对应（保留原始响应，回退 ambiguous）：", "```json", json.dumps(a["rejected_alignments"], ensure_ascii=False, indent=2), "```"]
        lines += [""]
    for status in sorted(STATUSES):
        if not counts[status]: lines += [f"本轮真实 pair 未观察到 {status}；不编造实际例子，见本地 contract tests 中的受控案例。"]
    (out / "TEST_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["prepare", "execute", "report"])
    p.add_argument("--pairs", type=Path)
    p.add_argument("--shots", type=int, choices=[0, 8], default=0)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.mode == "prepare":
        if args.pairs is None: p.error("prepare requires --pairs")
        prepare(args.pairs, args.output, shots=args.shots)
    else: globals()[args.mode](args.output)
