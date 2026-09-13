"""Replay binding normalization and locked-subgraph composition, with full ablations."""
import copy,json,csv
from collections import Counter
from pathlib import Path
from analysis_skeleton.common import read_jsonl,read_json,write_jsonl,write_json,check_frozen,digest,sha
from experiments.coco400_revision_v2.visual import merge
from experiments.matrix_recovery_v4 import run as base
from experiments.matrix_recovery_v4.bounds import tighten
from experiments.matrix_recovery_v4.report import compare
from .run import ROOT,SOURCE
from .search_binding import validate
from .local_alignment import patch,signature


def main():
    old=read_jsonl(SOURCE);oldmap={r['pair_id']:r for r in old}
    tasks={t['id']:t for t in read_jsonl(ROOT/'tasks.jsonl')};raws=read_jsonl(ROOT/'calls/results.jsonl');values={};audits=[]
    for r in raws:
        if r['result']['status']!='complete':continue
        v=validate(json.loads(r['result']['audit']['raw_content']),tasks[r['id']]['input'])
        values[r['id']]={'claims':v['claims'],'audit':r['result']['audit']}
        audits.extend({'pair_id':r['id'],**x} for x in v['search_binding_audit'])
    candidate={r['pair_id']:r for r in read_jsonl('outputs/matrix_recovery_v4_approved_repair/D_bounds/pairs.jsonl')}
    comparisons={};base.ROOT=ROOT
    for name,use_patch in [('joint_search_binding',False),('combined_search_binding',True)]:
        rows=copy.deepcopy(old);changes=[];patch_audit=[]
        for r in rows:
            saved=values.get(r['pair_id'])
            if saved:
                for v in r['verification']:
                    if v['claim_id'] not in saved['claims']:continue
                    result={**saved['claims'][v['claim_id']],'audit':saved['audit']};before=v['label'];v.update(merge(v,result))
                    v['v5_joint_response_id']=saved['audit'].get('response_id')
                    changes.append({'pair_id':r['pair_id'],'claim_id':v['claim_id'],'before':before,'after':v['label'],'status':result['status']})
            if use_patch:
                b=r['bundle'];b['alignment'],audit=patch(b['alignment'],candidate[r['pair_id']]['bundle']['alignment'],b['original'],b['steer'])
                patch_audit.append({'pair_id':r['pair_id'],**audit})
            base.recompute(r);r['observation']=tighten(r['observation'],r['ledger'],r['bundle'])
        base.emit(name,rows);summary,trans=compare(oldmap,rows)
        summary['local_claim_failures']=sum(x['status']!='complete' for x in changes)
        write_json(ROOT/name/'comparison.json',summary);write_jsonl(ROOT/name/'transitions.jsonl',trans)
        write_jsonl(ROOT/name/'claim_transitions.jsonl',changes);write_jsonl(ROOT/name/'patch_audit.jsonl',patch_audit)
        comparisons[name]=summary
        assert len(rows)==len({r['pair_id'] for r in rows})==400
        assert sum(len(r['ledger']) for r in rows)==5959
        for r in rows:
            for side in ('original','steer'):assert digest(r['bundle'][side])==digest(oldmap[r['pair_id']]['bundle'][side])
            for table in ('entities','alignments'):
                fixed={signature(e):e for e in oldmap[r['pair_id']]['bundle']['alignment'][table] if e['status']!='unresolved'}
                current={signature(e):e for e in r['bundle']['alignment'][table]}
                assert all(current.get(k)==e for k,e in fixed.items())
        with (ROOT/name/'matrix.csv').open(encoding='utf-8-sig',newline='') as f:assert sum(int(x['count']) for x in csv.DictReader(f))==summary['after']
        if use_patch:
            remaining=[];inc=Counter()
            for r in rows:
                if r['observation']['matrix_classifiable']:continue
                q=r['observation']['quality'];inc.update({k:bool(q.get(k)) for k in ('visual_uncertain_facts','alignment_semantic_facts','alignment_technical_facts','retained_label_or_parent_conflicts')})
                remaining.append({'pair_id':r['pair_id'],'original':r['bundle']['original']['text'],'steer':r['bundle']['steer']['text'],'observation':r['observation'],
                    'unresolved_alignment':[e for e in r['bundle']['alignment']['alignments'] if e['status']=='unresolved'],
                    'visual_uncertain':[{'statement':q['statement'],'reason':v.get('reason')} for q in r['queue'] for v in r['verification'] if q['claim_id']==v['claim_id'] and v['label'] in ('uncertain',None)]})
            write_jsonl(ROOT/'remaining_final.jsonl',remaining);write_json(ROOT/'remaining_summary.json',{'pairs':len(remaining),'overlapping_problem_incidence':dict(inc)})
    write_jsonl(ROOT/'search_binding_audit.jsonl',audits)
    comparisons['joint_strict']=read_json(ROOT/'summary.json')
    for name in ('local_alignment_only','combined'):comparisons[name]=read_json(ROOT/name/'comparison.json')
    write_json(ROOT/'final_comparison.json',comparisons)
    check_frozen(ROOT/'calls');checks=0
    for f in (ROOT/'calls/checkpoints').glob('*.json'):
        c=read_json(f);assert c['checksum']==digest(c['value']);checks+=1
    ids=[r['result']['audit']['response_id'] for r in raws];assert len(ids)==len(set(ids))
    assert all(r['result']['audit']['response_model']=='deepseek-flash' for r in raws)
    write_json(ROOT/'integrity.json',{'pairs':400,'facts':5959,'new_main_calls':117,'main_response_ids':len(ids),'checkpoints_verified':checks,
        'M2_unchanged':True,'known_M3_rows_unchanged':True,'offline_composition_new_calls':0,
        'search_binding_repairs':len(audits),'final_code_sha':sha(__file__),'patch_code_sha':sha(Path(__file__).with_name('local_alignment.py'))})
    print(json.dumps(comparisons,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
