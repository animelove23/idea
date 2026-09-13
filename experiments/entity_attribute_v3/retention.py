"""Explicit observed-fact denominators; unresolved is not attribute loss."""
import argparse
from collections import Counter,defaultdict
from pathlib import Path
from analysis_skeleton.common import read_jsonl,write_json,write_jsonl,ratio,sha
from experiments.coco400_revision_v2.observation import analyze_pair as scoped_observation

SLOTS=('color','material','size','shape','state')

def rates(rows):
    c=Counter(r['outcome'] for r in rows);n=len(rows);r=c['retained'];lost=c['removed']+c['modified'];u=c['unresolved']
    assert r+lost+u==n
    return {'denominator':n,'retained':r,'removed':c['removed'],'modified':c['modified'],'unresolved':u,
            'retention_lower':ratio(r,n),'retention_upper':ratio(r+u,n),
            'loss_lower':ratio(lost,n),'loss_upper':ratio(lost+u,n),
            'decided_only_retention':ratio(r,r+lost),'decided_coverage':ratio(r+lost,n)}

def analyze(records):
    detail=[];err=[];eligibility=Counter();source_issues=Counter();seen=set()
    for record in records:
        b=record['bundle'];ledger=record['ledger'];pid=record['pair_id']
        if pid in seen:raise ValueError('duplicate_pair_id')
        seen.add(pid)
        parent_rows={r['entity_id']:r for r in ledger if r['side']=='original' and r['type']=='entity'}
        steer_parents={r['entity_id']:r for r in ledger if r['side']=='steer' and r['type']=='entity'}
        _,events=scoped_observation(b,ledger)
        uncertain_refs={(ev['side'],ev['fact_id']) for ev in events if ev.get('uncertain') and 'fact_id' in ev}
        uncertain_refs.update(tuple(ref) for ev in events if ev.get('uncertain') for ref in ev.get('refs',[]))
        mapping={eid:e for e in b['alignment']['entities'] for eid in e['original']}
        for d in (b['original'],b['steer']):source_issues.update(i['kind'] for i in d.get('issues',[]))
        for row in ledger:
            if row['side']!='original' or row['visual_label']!='supported':continue
            e=mapping.get(row['entity_id'],{});matched=e.get('status')=='matched' and not e.get('reason','').startswith('technical')
            if row['type']=='entity':
                outcome='retained' if matched else 'removed' if e.get('status')=='original_only' else 'unresolved'
                err.append({'pair_id':pid,'fact_id':row['fact_id'],'outcome':outcome,'description_change':e.get('description_change','unresolved')})
                continue
            parent=parent_rows.get(row['entity_id'],{})
            if parent.get('visual_label')!='supported':eligibility['original_parent_not_supported']+=1;continue
            if not matched:
                eligibility['parent_removed' if e.get('status')=='original_only' else 'parent_identity_unresolved']+=1
                continue
            peer_parent=steer_parents.get(e['steer'][0],{})
            if peer_parent.get('visual_label')!='supported' or parent.get('truth_conflict'):
                eligibility['retained_parent_visual_unconfirmed']+=1;continue
            eligibility['eligible_supported_attribute_on_retained_owner']+=1
            status=row['status']
            if row['alignment_axis']!='decided' or row.get('truth_conflict') or ('original',row['fact_id']) in uncertain_refs:outcome='unresolved'
            elif status=='retained':outcome='retained' if row.get('peer_label')=='supported' else 'unresolved'
            elif status in {'removed','modified'}:outcome=status
            else:outcome='unresolved'
            detail.append({'pair_id':pid,'fact_id':row['fact_id'],'entity_id':row['entity_id'],'slot':row['slot'],
                           'outcome':outcome,'alignment_axis':row['alignment_axis'],'peer_label':row.get('peer_label'),
                           'parent_description_change':e.get('description_change','unresolved')})
    per_pair=[{'pair_id':pid,**rates([r for r in detail if r['pair_id']==pid])} for pid in sorted(seen)]
    summary={'pairs':len(seen),'denominator_scope':'observed_original_supported_facts_not_complete_image_recall',
             'entity_identity_retention':rates(err),'description_changes_among_retained_entities':dict(Counter(r['description_change'] for r in err if r['outcome']=='retained')),
             'conditional_attribute_retention':rates(detail),'by_slot':{s:rates([r for r in detail if r['slot']==s]) for s in SLOTS},
             'attribute_denominator_exclusions':dict(eligibility),'m2_issue_counts':dict(source_issues),
             'macro_pair_retention_lower':ratio(sum(r['retention_lower'] for r in per_pair if r['denominator']),sum(bool(r['denominator']) for r in per_pair)),
             'not_independent_human_gold':True,'missing_extraction_not_recoverable_from_production_denominator':True}
    return summary,detail,per_pair,err

def main():
    p=argparse.ArgumentParser();p.add_argument('--pairs',default='outputs/coco400_revision_v2_guard/C_reviewed/pairs.jsonl');p.add_argument('--output',default='outputs/entity_attribute_v3/retention');a=p.parse_args()
    summary,rows,pairs,entities=analyze(read_jsonl(a.pairs));summary.update(input_sha256=sha(a.pairs),new_llm_calls=0)
    out=Path(a.output);out.mkdir(parents=True,exist_ok=True);write_json(out/'summary.json',summary);write_jsonl(out/'attribute_denominator.jsonl',rows);write_jsonl(out/'per_pair.jsonl',pairs);write_jsonl(out/'entity_denominator.jsonl',entities)
    print(summary)

if __name__=='__main__':main()
