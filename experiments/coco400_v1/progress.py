"""Inspect only completed pair exports; never open exports while being replaced."""
import json
from collections import Counter
from pathlib import Path
from analysis_skeleton.common import read_json,read_jsonl
from .observe import analyze_pair

ROOT=Path('outputs/coco400_final_v1')


def main():
    records=[]
    for line in (ROOT/'run_events.jsonl').read_text(encoding='utf-8').splitlines():
        try:records.append(json.loads(line))
        except json.JSONDecodeError:pass
    quality=Counter();status=Counter();issues=Counter();matrix=Counter();labels=Counter()
    calls=0
    for e in records:
        status[e['status']]+=1
        if e['status']!='exported':continue
        calls+=e['metrics']['new_api_calls_this_invocation']
        run=ROOT/'runs'/e['pair_id'];bundles=read_jsonl(run/'bundles.jsonl')
        if not bundles:continue
        b=bundles[0];ledger=read_jsonl(run/'denominator_ledger.jsonl')
        r,_=analyze_pair(b,ledger);quality.update(r['quality'])
        labels.update(x['visual_label'] for x in ledger)
        matrix['classifiable' if r['matrix_classifiable'] else 'unresolved']+=1
        for side in ('original','steer'):
            issues.update(str(i) for i in b[side].get('issues',[]))
    print(json.dumps({'completed':len(records),'status':status,'completed_pair_calls':calls,
        'quality':quality,'matrix_coverage':matrix,'labels':labels,'top_extraction_issues':issues.most_common(8)},ensure_ascii=False))


if __name__=='__main__':main()
