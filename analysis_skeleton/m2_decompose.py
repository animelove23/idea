"""M2 independent extraction and pre-frozen candidate-reference pilot evaluation."""
import argparse
from pathlib import Path
from .common import new_run,read_jsonl,write_json,write_jsonl,report,check_frozen
from .contracts import normalize_document
from .llm import FewShotStage,CallFailure,ROOT
from .metrics import score_documents,aggregate_documents


def execute(cases_path, output, config="decomposition/api_config.local.json", repeat=1):
    cases = read_jsonl(cases_path)
    stage = FewShotStage("decompose",config)
    for c in cases:
        ref = normalize_document(c["reference"],c["text"],c["case_id"])
        if ref["issues"]:
            raise ValueError("Candidate reference has invalid spans/schema")
        if c["text"] in {s["input"]["text"] for s in stage.shots}:
            raise ValueError("Example/test text overlap")
    out = new_run(output,"M2",[cases_path,stage.rules_path,stage.shots_path],stage.identity,
                  [__file__,ROOT/"contracts.py",ROOT/"llm.py",ROOT/"metrics.py"])
    records,scores = [],[]
    for round_id in range(repeat):
        for c in cases:
            check_frozen(out)
            key = f"{c['case_id']}_r{round_id+1}"
            write_json(out / (key + "_started.json"),{"started":True,"case_id":c["case_id"]})
            doc = {"caption_id":c["case_id"],"text":c["text"],"entities":[],"facts":[],"issues":[]}
            try:
                raw,audit = stage.run({"text":c["text"]})
                write_json(out/(key+"_response.json"),audit)
                doc = normalize_document(raw,c["text"],c["case_id"])
            except CallFailure as exc:
                audit = exc.audit
                doc.update(status="technical_failure",issues=[{"reason":audit["error"]}])
            except ValueError as exc:
                doc.update(status="technical_failure",issues=[{"reason":str(exc)}])
            score = score_documents(doc,normalize_document(c["reference"],c["text"],c["case_id"]))
            record = {"case_id":c["case_id"],"round":round_id+1,"split":c["split"],
                      "document":doc,"audit":audit,"score":score}
            write_json(out/(key+".json"),record)
            records.append(record)
            scores.append(score)
            print(f"M2 {key}: {doc.get('status')} facts={len(doc['facts'])}",flush=True)
    write_jsonl(out/"results.jsonl",records)
    metrics = {"calls":len(records),"summary":aggregate_documents(scores),
               "technical_failures":sum(r["document"].get("status") == "technical_failure" for r in records),
               "by_split":{split:aggregate_documents([r["score"] for r in records if r["split"] == split]) for split in sorted({r["split"] for r in records})},
               "independent_human_accuracy":None,"reference_status":"assistant_candidate_not_gold"}
    report(out,"M2 固定8-shot独立分解测评",metrics,
           ["先冻结参考/示例/代码再请求；没有自动修复或重试，没有视觉/POS输入。",
            "指标是相对预写候选参考的确定性匹配，主体依据名称及原文span；有限同义词表可能漏计等义表达，需审阅差异。",
            "真实样本与合成边界分开，不将候选符合度当独立人工准确率；技术失败仍计参考漏报。"])
    return metrics


if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--cases",required=True);p.add_argument("--output",required=True)
    p.add_argument("--repeat",type=int,default=1);p.add_argument("--config",default="decomposition/api_config.local.json")
    a=p.parse_args();execute(a.cases,a.output,a.config,a.repeat)
