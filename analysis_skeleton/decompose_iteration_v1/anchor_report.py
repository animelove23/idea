"""Independent deterministic intervention on exact saved control responses."""
import json
from pathlib import Path
from collections import Counter
from analysis_skeleton.common import read_jsonl,read_json,write_json,write_jsonl,check_frozen,sha
from analysis_skeleton.framework_v2.contracts import normalize_document
from analysis_skeleton.repair_v1.scoring import LemmaScorer
from analysis_skeleton.metrics import aggregate_documents
from .value_anchor import normalize_with_value_anchors

def main(root):
    root=Path(root);check_frozen(root/'run');rows=read_jsonl(root/'run/results.jsonl');cases=read_jsonl(root/'references.jsonl')
    refs={r['case_id']:normalize_document(r['reference'],r['text'],r['case_id']) for r in cases};scorer=LemmaScorer();result=[];scores=[]
    for r in rows:
        if r['condition']!='control':continue
        assert r['status']=='complete'
        d=normalize_with_value_anchors(json.loads(r['audit']['raw_content']),refs[r['case_id']]['text'],r['case_id'])
        score=scorer.score(d,refs[r['case_id']]);scores.append(score)
        result.append({'case_id':r['case_id'],'document':d,'score':score,'source_response_id':r['audit']['response_id'],'new_api_calls':0})
    metrics={'before':read_json(root/'metrics.json')['control'],'after':aggregate_documents(scores),
             'repaired_value_quotes':sum(len(r['document']['value_anchor_audit']['repairs']) for r in result),
             'affected_captions':sum(bool(r['document']['value_anchor_audit']['repairs']) for r in result),
             'new_api_calls':0,'source_condition':'control: original eight examples, no failed split-shot intervention',
             'code_sha':sha(Path(__file__).with_name('value_anchor.py')),'raw_response_file_sha':sha(root/'run/results.jsonl'),
             'labels_references_scorer_unchanged':True,'production_installed':False}
    write_json(root/'anchor_metrics.json',metrics);write_jsonl(root/'anchor_results.jsonl',result);print(json.dumps(metrics,ensure_ascii=False,indent=2))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();main(a.output)
