"""Read-only audit of completed experiment artifacts; never calls a model."""
from collections import Counter
from pathlib import Path
from analysis_skeleton.common import read_json,read_jsonl,write_json,sha,check_frozen
from decomposition.storage import digest

ROOT=Path('outputs/coco400_final_v1')


def main():
    pairs=read_jsonl(ROOT/'pairs.jsonl')
    assert len(pairs)==len({p['pair_id'] for p in pairs})==400
    check_frozen(ROOT/'orchestration')
    old=read_json('outputs/final_v1_release/release_manifest.json')
    assert all(sha(p)==h for p,h in old['files'].items())
    totals=Counter();statuses=Counter();errors=Counter();failure_phases=Counter();responses=[];parent_anomalies=[]
    failures=[];fact_keys=[];raw_models=Counter()
    for p in pairs:
        pid=p['pair_id'];run=ROOT/'runs'/pid
        check_frozen(run)
        for f in (run/'checkpoints').glob('*.json'):
            rec=read_json(f);assert digest(rec['value'])==rec['checksum'],str(f)
            totals['checksummed_checkpoints']+=1
            v=rec['value'];a=v.get('audit',{})
            if f.name.endswith('_response.json'):
                responses.append(a['response_id']);raw_models[a['response_model']]+=1
                assert a['response_model']==a['identity']['model']=='deepseek-flash'
                assert a['identity']['base_url'].rstrip('/')=='https://api.deepseek.com'
                assert a['identity']['shots']=={'decompose':8,'align':8,'verify':6}[a['stage']]
                if a['stage']=='verify':
                    kind=a['input']['claim_type']
                    assert a['typed_route']=={'claim_type':kind,'contract':'context' if kind=='entity' else 'proposition'}
            else:
                statuses[v['status']]+=1
                if v['status']!='complete':failure_phases[v.get('phase','unknown')]+=1
                totals['recorded_api_calls']+=a.get('api_calls',0)
                if a.get('error'):errors[str(a['error'])]+=1
        bundles=read_jsonl(run/'bundles.jsonl');ledger=read_jsonl(run/'denominator_ledger.jsonl')
        queue=read_jsonl(run/'verification_queue.jsonl');labels=read_jsonl(run/'verification.jsonl')
        expected={(b['pair_id'],s,f['id']) for b in bundles for s in ('original','steer') for f in b[s]['facts']}
        queued=[(q['pair_id'],r['side'],r['fact_id']) for q in queue for r in q['refs']]
        recorded=[(r['pair_id'],r['side'],r['fact_id']) for r in ledger]
        assert expected==set(queued)==set(recorded)
        assert len(expected)==len(queued)==len(recorded)
        assert {q['claim_id'] for q in queue}=={v['claim_id'] for v in labels}
        fact_keys+=recorded
        m=read_json(run/'metrics.json')
        totals.update({k:m[k] for k in ('facts','claims','pending_claims','failed_pairs','shared_claims','visual_routing_failures')})
        if m['failed_pairs']:failures.append(pid)
        for r in ledger:
            if r['type']=='attribute' and r['visual_label']=='supported' and r['parent_visual_label']!='supported':
                assert not r['strict_parent_supported_eligible']
                parent_anomalies.append(r)
        totals['pairs_checked']+=1
    assert len(responses)==len(set(responses))
    assert len(fact_keys)==len(set(fact_keys))==totals['facts']
    summary=read_json(ROOT/'observations/summary.json')
    assert summary['accepted_fact_rows']==totals['facts']
    assert summary['new_api_calls_recorded_in_checkpoints']==totals['recorded_api_calls']
    assert summary['unique_response_ids']==len(responses)
    for length,n in summary['length_counts'].items():
        assert summary['matrix_classifiable_by_length'][length]+summary['matrix_unresolved_by_length'][length]==n
    result={'passed':True,**dict(totals),'old_frozen_files_unchanged':len(old['files']),
        'all_accepted_facts_queued_and_recorded_exactly_once':True,'unique_raw_responses':len(responses),
        'raw_response_models':dict(raw_models),'call_status':dict(statuses),'call_errors':dict(errors),
        'failure_phases':dict(failure_phases),
        'failed_pair_ids':failures,'supported_attribute_parent_not_supported':len(parent_anomalies),
        'parent_anomaly_breakdown':dict(Counter(r['parent_visual_label'] or 'missing' for r in parent_anomalies)),
        'strict_statistics_exclude_all_parent_anomalies':True,'semantic_accuracy_measured':False}
    write_json(ROOT/'observations/integrity.json',result)
    print(result)


if __name__=='__main__':main()
