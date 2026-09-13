"""Re-score unchanged legacy M2 outputs and export owner disagreements for review."""
from pathlib import Path
from analysis_skeleton.common import read_jsonl,write_json,write_jsonl
from analysis_skeleton.framework_v2.contracts import normalize_document
from analysis_skeleton.repair_v1.scoring import LemmaScorer
from analysis_skeleton.metrics import aggregate_documents
from .scoring import diagnostics

def main():
    refs={r['case_id']:r for r in read_jsonl('analysis_skeleton/fixtures/expansion20/decompose_cases.jsonl')}
    docs=[r for r in read_jsonl('outputs/final_v1_m2/documents.jsonl') if r['variant']=='owner_final'];scorer=LemmaScorer();rows=[];bad=[]
    for r in docs:
        raw=refs[r['case_id']];ref=normalize_document(raw['reference'],raw['text'],r['case_id']);d=diagnostics(r['document'],ref,scorer)
        rows.append({'case_id':r['case_id'],**d})
        if d['ownership_wrong'] or d['reference_missing_facts'] or d['score']['joint']['tp']<d['score']['joint']['predicted']:
            bad.append({'case_id':r['case_id'],'text':raw['text'],'prediction':r['document'],'reference':ref,'diagnostic':d,'human_text_faithful':None})
    metrics={'captions':len(rows),'scores':aggregate_documents([r['score'] for r in rows]),
             **{k:sum(r[k] for r in rows) for k in ('ownership_correct','ownership_wrong','ownership_unjudged','reference_missing_facts')},
             'new_model_calls':0,'human_accuracy_measured':False,'references_unchanged':True}
    root=Path('outputs/entity_attribute_v3/historical_m2');root.mkdir(parents=True,exist_ok=True)
    write_json(root/'summary.json',metrics);write_jsonl(root/'per_caption.jsonl',rows);write_jsonl(root/'bad_cases.jsonl',bad);print(metrics)

if __name__=='__main__':main()
