"""Frozen 33-call v6 pilot. No visual inputs, reference labels, or automatic semantic judge."""
import argparse
import itertools
import json
import random
import re
import shutil
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from annotation.v6.acceptance import acceptance, PARAPHRASES
from decomposition.config import API_CONFIG_PATH, load_api_config
from decomposition.storage import digest, output_lock, write_json, write_jsonl
from decomposition.v6.pipeline import DecomposerV6, V6Failure, prompt
from decomposition.v6.schema import summary


def prepare(out):
    if out.exists():
        raise ValueError("Use a new experiment directory")
    out.mkdir(parents=True)
    (out / "checkpoints").mkdir()
    (out / "frozen").mkdir()
    refs = acceptance()
    old = [json.loads(line) for line in Path("annotation/v5/references.jsonl").read_text(encoding="utf-8").splitlines()]
    real = [{"id": r["id"], "kind": "real_regression", "text": r["document"]["text"]}
            for r in old if r["kind"] == "holdout"]
    jobs = []
    for r in refs + real:
        for shots in ([0, 8] if r["kind"] == "acceptance" else [8]):
            jobs.append({"job_id": f"{r['id']}_s{shots}_r1", "id": r["id"], "kind": r["kind"],
                         "shots": shots, "repeat": 1, "text": r["text"]})
    for id in ["a0", "299573_vanilla", "417586_vanilla"]:
        j = next(j for j in jobs if j["id"] == id and j["shots"] == 8)
        for repeat in [2, 3]:
            jobs.append({**j, "repeat": repeat, "job_id": f"{id}_s8_r{repeat}"})
    for r in PARAPHRASES:
        jobs.append({**r, "kind": "paraphrase", "shots": 8, "repeat": 1, "job_id": r["id"] + "_s8_r1"})
    random.Random(6112026).shuffle(jobs)
    assert len(jobs) == 33
    assert not {r["text"] for r in refs} & {s["text"] for s in json.loads(Path("decomposition/v6/shots.json").read_text())}
    prompts = {str(n): prompt(n) for n in [0, 8]}
    files = [p for p in Path("decomposition/v6").iterdir() if p.is_file()] + [
        Path("decomposition/semantic_decomposer.py"), Path("decomposition/config.py"),
        Path(__file__), Path("annotation/v6/acceptance.py")]
    hashes = {}
    for index, p in enumerate(files):
        key = str(p.resolve().relative_to(Path.cwd()))
        hashes[key] = digest(p.read_text(encoding="utf-8"))
        shutil.copy2(p, out / "frozen" / (f"{index:02}_" + p.name))
    protocol = {"version": "semantic-core-v6.0-pilot1", "created_at": datetime.now(timezone.utc).isoformat(),
                "decompositions": 33, "maximum_http_requests": 66, "workers": 4,
                "thinking": "disabled", "temperature": 0, "base_url": "https://api.deepseek.com",
                "model_policy": "existing local API configuration, frozen at execution start", "timeout": 120,
                "jobs_digest": digest(jobs), "prompts_digest": digest(prompts), "reference_digest": digest(refs),
                "files": hashes, "label_origin": "Assistant-authored synthetic acceptance references, frozen before predictions; NOT independently reviewed human gold",
                "permission": "User requested v6 test execution after reviewing v6 scope and eight-shot package.",
                "scope": "8 synthetic acceptance captions at 0/8 shots; 8 prior real captions at 8 shots; 6 extra repeat runs; 3 paraphrases; only text and demonstration annotations sent",
                "metric_policy": "Manual semantic matching against frozen propositions, one-to-one. Preserve referent, quantity/unit, negation, modality; fine-label differences within same coarse type do not penalize meaning. Main precision includes every predicted main fact, including duplicates. Wrongly routed other loses main recall. No changes to references after predictions. Source problems reported separately. Compound facts cannot earn multiple atomic TPs. Real captions have no gold accuracy claim. Strict normalized text repeat F1 is wording agreement, not semantic accuracy.",
                "ambiguity_policy": "c0 may scopes both sleeping and under-table proposition. Paragraph-scope accepted; synonymous complete facts accepted. Reviewer must explain unmatched/partial facts. No numerical confidence threshold is claimed."}
    write_json(out / "protocol.json", protocol)
    write_json(out / "jobs.json", jobs)
    write_json(out / "prompts.json", prompts)
    write_json(out / "references.json", refs)
    (out / "SCORING_POLICY.md").write_text("# 冻结评分口径\n\n" + protocol["label_origin"] + "\n\n" + protocol["metric_policy"] + "\n\n" + protocol["ambiguity_policy"], encoding="utf-8")
    print(json.dumps({"prepared": str(out), "decompositions": len(jobs), "maximum_requests": 66}), flush=True)


def execute(out):
    protocol = json.loads((out / "protocol.json").read_text(encoding="utf-8"))
    jobs = json.loads((out / "jobs.json").read_text(encoding="utf-8"))
    prompts = json.loads((out / "prompts.json").read_text(encoding="utf-8"))
    assert digest(jobs) == protocol["jobs_digest"] and digest(prompts) == protocol["prompts_digest"]
    assert digest(json.loads((out / "references.json").read_text(encoding="utf-8"))) == protocol["reference_digest"]
    for name, checksum in protocol["files"].items():
        assert digest(Path(name).read_text(encoding="utf-8")) == checksum, name
    config = load_api_config(API_CONFIG_PATH, timeout=protocol["timeout"])
    assert config.base_url.rstrip("/") == protocol["base_url"]
    identity = {"model": config.model, "base_url": config.base_url, "max_tokens": config.max_tokens,
                "timeout": config.timeout, "thinking": "disabled", "temperature": 0}
    with output_lock(out):
        p = out / "execution_config.json"
        if p.exists():
            assert json.loads(p.read_text()) == identity
        else:
            write_json(p, identity)
        def run(job):
            path = out / "checkpoints" / (job["job_id"] + ".json")
            if path.exists():
                row = json.loads(path.read_text(encoding="utf-8"))
                assert all(row.get(k) == v for k, v in job.items())
                return job["job_id"], row["status"]
            row = {**job, "started_at": datetime.now(timezone.utc).isoformat()}
            try:
                doc, audit = DecomposerV6(config, frozen_prompt=prompts[str(job["shots"])]).decompose(job["text"])
                doc["id"] = job["id"]
                row.update(document=doc, audit=audit, status=doc["status"])
            except V6Failure as exc:
                row.update(status="failed", error=str(exc), audit=exc.audit)
            row["finished_at"] = datetime.now(timezone.utc).isoformat()
            write_json(path, row)
            return job["job_id"], row["status"]
        pending = [j for j in jobs if not (out / "checkpoints" / (j["job_id"] + ".json")).exists()]
        if pending:
            first = run(pending[0]); print(*first, flush=True)
            if first[1] == "failed":
                raise RuntimeError("Initial request failed; inspect checkpoint before continuing")
            with ThreadPoolExecutor(max_workers=protocol["workers"]) as pool:
                for future in as_completed([pool.submit(run, job) for job in pending[1:]]):
                    print(*future.result(), flush=True)
    report(out)


def lexical_key(f):
    return (f["type"], " ".join(re.findall(r"\w+", f["fact"].lower())), f["assertion"], f["polarity"])


def lexical_compare(a, b):
    ca = Counter(lexical_key(f) for f in a.get("document", {}).get("facts", []) if f["in_main"])
    cb = Counter(lexical_key(f) for f in b.get("document", {}).get("facts", []) if f["in_main"])
    tp, na, nb = sum((ca & cb).values()), sum(ca.values()), sum(cb.values())
    return {"shared": tp, "a": na, "b": nb, "f1": 2*tp/(na+nb) if na+nb else None,
            "both_ready": a["status"] == b["status"] == "ready"}


def report(out):
    rows = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((out / "checkpoints").glob("*.json"))]
    write_jsonl(out / "results.jsonl", rows)
    mapping = {r["job_id"]: r for r in rows}
    attempts = [a for r in rows for a in r.get("audit", {}).get("attempts", [])]
    stats = {"completed": len(rows), "status": dict(Counter(r["status"] for r in rows)), "http_requests": len(attempts),
             "prompt_tokens": sum((a.get("usage") or {}).get("prompt_tokens", 0) for a in attempts),
             "completion_tokens": sum((a.get("usage") or {}).get("completion_tokens", 0) for a in attempts)}
    stats["routing"] = {str(n): summary(r["document"] for r in rows if r["shots"] == n and r["kind"] == "acceptance" and r["repeat"] == 1 and "document" in r) for n in [0, 8]}
    stats["real_routing"] = {method: summary(r["document"] for r in rows if r["kind"] == "real_regression" and r["repeat"] == 1 and r["id"].endswith(method) and "document" in r) for method in ["vanilla", "vista"]}
    stats["strict_wording_repeats"] = []
    for id in ["a0", "299573_vanilla", "417586_vanilla"]:
        for a, b in itertools.combinations([1, 2, 3], 2):
            ka, kb = f"{id}_s8_r{a}", f"{id}_s8_r{b}"
            if ka in mapping and kb in mapping:
                stats["strict_wording_repeats"].append({"id": id, "runs": [a, b], **lexical_compare(mapping[ka], mapping[kb])})
    stats["strict_wording_paraphrases"] = []
    for p in PARAPHRASES:
        ka, kb = p["base"] + "_s8_r1", p["id"] + "_s8_r1"
        if ka in mapping and kb in mapping:
            stats["strict_wording_paraphrases"].append({"id": p["id"], **lexical_compare(mapping[ka], mapping[kb])})
    write_json(out / "structural_metrics.json", stats)
    lines = ["# v6 DeepSeek 实际输出", "", "真实响应；type/in_main/source_status 由程序处理，verification=pending。", ""]
    for r in rows:
        lines += ["## " + r["job_id"] + " — " + r["status"], "", "> " + r["text"], "",
                  "| id | type / category | fact | assertion / polarity | reason | source status |",
                  "| --- | --- | --- | --- | --- | --- |"]
        for f in r.get("document", {}).get("facts", []):
            vals = [f["id"], f["type"] + " / " + f["category"], f["fact"], f["assertion"] + " / " + f["polarity"], f.get("reason", ""), f["source_status"]]
            lines.append("| " + " | ".join(v.replace("|", "\\|").replace("\n", " ") for v in vals) + " |")
        if r.get("error"):
            lines.append(r["error"])
        lines.append("")
    (out / "MODEL_OUTPUTS.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"completed": stats["completed"], "status": stats["status"], "http_requests": len(attempts)}), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("mode", choices=["prepare", "execute", "report"])
    p.add_argument("--output", type=Path, default=Path("outputs/semantic_core_v6/experiment_v1"))
    args = p.parse_args(); globals()[args.mode](args.output)
