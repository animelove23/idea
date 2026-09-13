"""Diagnose duplicated M3 decisions on old raw responses; not a new model test."""
import json
from pathlib import Path
from collections import Counter
from analysis_skeleton.common import read_jsonl,write_json,write_jsonl,sha
from experiments.coco400_revision_v2.local_alignment import validate_local
from .m3 import project_v2,validate

SOURCE=Path('outputs/coco400_revision_v2_guard')
OUT=Path('outputs/entity_attribute_v3/m3_replay')
def counts(aligned):
    c=Counter()
    for r in aligned['alignments']:
        kind='technical' if r.get('reason','').startswith('technical') else 'semantic' if r['status']=='unresolved' else 'decided'
        c[kind]+=len(r['original'])+len(r['steer'])
    return dict(c)
def main():
    saved={r['id']:r['result'] for r in read_jsonl(SOURCE/'align_calls/results.jsonl')};rows=[];bad=[]
    for r in read_jsonl(SOURCE/'A_scope_only/pairs.jsonl'):
        b=r['bundle'];raw=json.loads(saved[r['pair_id']]['audit']['raw_content'])
        old=validate_local(raw,b['original'],b['steer']);newraw,dropped=project_v2(raw,b['original'],b['steer']);new=validate(newraw,b['original'],b['steer'])
        rows.append({'pair_id':r['pair_id'],'before':counts(old),'projected':counts(new),'dropped_redundant_entity_rows':len(dropped),'new_issues':new['issues']})
        if old['issues'] or new['issues']:
            bad.append({'pair_id':r['pair_id'],'original_text':b['original']['text'],'steer_text':b['steer']['text'],'before_issues':old['issues'],'projected_issues':new['issues'],'dropped_entity_rows':dropped})
    summary={'pairs':len(rows),'new_llm_calls':0,'semantic_accuracy_measured':False,'not_an_online_M3_improvement':'projecting an old two-table response may discard conflicting decisions; only diagnoses structural redundancy',
             'before':dict(sum((Counter(r['before']) for r in rows),Counter())),
             'projected':dict(sum((Counter(r['projected']) for r in rows),Counter())),
             'source_sha256':sha(SOURCE/'align_calls/results.jsonl')}
    OUT.mkdir(parents=True,exist_ok=True);write_json(OUT/'summary.json',summary);write_jsonl(OUT/'per_pair.jsonl',rows);write_jsonl(OUT/'bad_cases.jsonl',bad)
    print(summary)
if __name__=='__main__':main()
