"""Compare model interventions and mathematical bounds without rewriting model evidence."""
import copy,json
from collections import Counter
from pathlib import Path
from analysis_skeleton.common import read_jsonl,read_json,write_jsonl,write_json,check_frozen,digest,sha
from experiments.coco400_revision_v2.visual import merge
from . import run,refine
from .bounds import tighten

ROOT=refine.ROOT


def signature(payload):
    return digest({k:payload[k] for k in ('image_sha256','statement','entity_context','claim_type')})


def compare(old,rows):
    transitions=[]
    for r in rows:
        before=old[r['pair_id']]['observation'];after=r['observation']
        transitions.append({'pair_id':r['pair_id'],'before':before['matrix_classifiable'],'after':after['matrix_classifiable'],
            'H_before':before['hallucination_change'],'H_after':after['hallucination_change'],
            'S_before':before['supported_change'],'S_after':after['supported_change']})
    summary={'pairs':400,'before':sum(r['observation']['matrix_classifiable'] for r in old.values()),
        'after':sum(x['after'] for x in transitions),'target':360,
        'recovered':sum(not x['before'] and x['after'] for x in transitions),
        'regressed':sum(x['before'] and not x['after'] for x in transitions),
        'both_decided_cell_changed':sum(x['before'] and x['after'] and (x['H_before'],x['S_before'])!=(x['H_after'],x['S_after']) for x in transitions)}
    summary.update(rate=summary['after']/400,target_reached=summary['after']>=360)
    return summary,transitions


def main():
    run.ROOT=ROOT
    old={r['pair_id']:r for r in read_jsonl(run.SOURCE)}
    current=read_jsonl(ROOT/'C_visual/pairs.jsonl')
    # Controlled replay: old M3, reuse new visual results only for exact semantic queries.
    tasks={t['id']:t for t in read_jsonl(ROOT/'visual_tasks.jsonl')}
    calls={r['id']:r['result'] for r in read_jsonl(ROOT/'visual_calls/results.jsonl')}
    replay=[];matched=[]
    for prior in old.values():
        r=copy.deepcopy(prior);qm={q['claim_id']:q for q in r['queue']}
        for v in r['verification']:
            key=r['pair_id']+':'+v['claim_id'];q=qm[v['claim_id']]
            if key not in tasks or signature(q)!=signature(tasks[key]['input']):continue
            first=copy.deepcopy(v);v.update(merge(first,calls[key]))
            v['v4_review_audit']=calls[key].get('audit',{})
            matched.append({'pair_id':r['pair_id'],'claim_id':v['claim_id'],'before':first['label'],'after':v['label'],'result_status':calls[key]['status']})
        replay.append(run.recompute(r))
    run.emit('M5_only_exact_replay',replay);write_jsonl(ROOT/'M5_only_exact_replay/reused_calls.jsonl',matched)
    variants={'old_with_bounds':list(old.values()),'D_bounds':current,'M5_only_with_bounds':replay}
    results={};transitions={}
    for name,source in variants.items():
        rows=copy.deepcopy(source)
        for r in rows:r['observation']=tighten(r['observation'],r['ledger'],r['bundle'])
        run.emit(name,rows);results[name],transitions[name]=compare(old,rows)
    for name,rows in [('C_visual',current),('M5_only_exact_replay',replay)]:
        results[name],transitions[name]=compare(old,rows)
    write_json(ROOT/'comparison.json',{'variants':results,'m5_exact_replay_calls':len(matched),
        'repair_status':read_json(ROOT/'repair_status.json'),'independent_accuracy_measured':False,
        'all_variants_development_not_holdout':True,'selection_not_promoted':True})
    write_json(ROOT/'pair_transitions.json',transitions)
    remaining=[]
    for r in read_jsonl(ROOT/'D_bounds/pairs.jsonl'):
        if r['observation']['matrix_classifiable']:continue
        b=r['bundle'];o=r['observation']
        remaining.append({'pair_id':r['pair_id'],'original':b['original']['text'],'steer':b['steer']['text'],
            'candidate_states':o['candidate_states'],'quality':o['quality'],'cardinality_bounds':o['cardinality_bounds_audit'],
            'M2_issues':{s:b[s]['issues'] for s in ('original','steer')},
            'unresolved_alignment':[e for e in b['alignment']['alignments'] if e['status']=='unresolved'],
            'uncertain_visual':[{'statement':q['statement'],'label':v['label'],'reason':v.get('reason'),'evidence':v.get('evidence')}
                for q in r['queue'] for v in r['verification'] if q['claim_id']==v['claim_id'] and v['label'] in ('uncertain',None)]})
    write_jsonl(ROOT/'remaining_cases.jsonl',remaining)
    evidence=[]
    for p in [Path('outputs/matrix_recovery_v4/probe_calls'),refine.PARENT/'probe_calls',refine.PARENT/'align_calls',ROOT/'visual_calls']:
        m=check_frozen(p);records=read_jsonl(p/'results.jsonl');ids=[];checks=0
        for f in (p/'checkpoints').glob('*.json'):
            ck=read_json(f);assert digest(ck['value'])==ck['checksum'];checks+=1
        for record in records:
            a=record['result'].get('audit',{});rid=a.get('response_id')
            if rid:ids.append(rid)
            if a.get('response_model'):assert a['response_model']=='deepseek-flash'
        assert len(ids)==len(set(ids))
        evidence.append({'path':str(p),'requests':len(records),'response_ids':len(ids),'checkpoint_files_verified':checks,
            'statuses':dict(Counter(r['result']['status'] for r in records))})
    for r in current:
        assert {s:digest(r['bundle'][s]) for s in ('original','steer')}=={s:digest(old[r['pair_id']]['bundle'][s]) for s in ('original','steer')}
        assert len(r['ledger'])==len(old[r['pair_id']]['ledger'])
    write_json(ROOT/'integrity.json',{'calls':evidence,'diagnostic_extra_requests':1,'model_list_read':1,
        'inference_http_attempts':8+1+8+400+322,'frozen_M2_unchanged':True,'accepted_facts':5959,
        'source_sha':sha(run.SOURCE),'bounds_code_sha':sha(Path(__file__).with_name('bounds.py')),
        'report_code_sha':sha(__file__),'bounded_remote_repair_requests':0})
    print(json.dumps(results,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
