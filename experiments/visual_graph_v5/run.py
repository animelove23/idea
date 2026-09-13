import argparse,copy,json,threading
from pathlib import Path
from collections import Counter
from concurrent.futures import ThreadPoolExecutor,as_completed
from analysis_skeleton.common import read_jsonl,read_json,write_jsonl,write_json,digest,sha,new_run,check_frozen
from analysis_skeleton.framework_v2.runtime import SafeStage,Checkpoints
from analysis_skeleton.final_v1.routing import routing_inputs
from experiments.coco400_revision_v2.visual import merge
from experiments.matrix_recovery_v4 import run as base
from experiments.matrix_recovery_v4.bounds import tighten
from experiments.matrix_recovery_v4.report import compare
from decomposition.storage import output_lock
from .stage import JointStage,compiled,shots

ROOT=Path('outputs/visual_graph_v5');SOURCE=Path('outputs/matrix_recovery_v4_refined/M5_only_with_bounds/pairs.jsonl');LOCAL=threading.local()


def prepare():
    ROOT.mkdir(exist_ok=False);tasks=[]
    for r in read_jsonl(SOURCE):
        qm={q['claim_id']:q for q in r['queue']};vm={v['claim_id']:v for v in r['verification']}
        byref={(ref['side'],ref['fact_id']):q['claim_id'] for q in r['queue'] for ref in q['refs']}
        target={cid for cid,v in vm.items() if v['label'] in ('uncertain',None)}
        for l in r['ledger']:
            if l['type']=='attribute' and l['visual_label']=='supported' and l['parent_visual_label']!='supported':target.add(l['claim_id'])
        parents={}
        for cid in list(target):
            q=qm[cid];pp=[]
            if q['claim_type']=='attribute':
                for ref in q['refs']:
                    f=next(f for f in r['bundle'][ref['side']]['facts'] if f['id']==ref['fact_id'])
                    parent=byref.get((ref['side'],'entity_'+f['entity_id']))
                    if parent:pp.append(parent)
            parents[cid]=sorted(set(pp));target.update(pp)
        if not target:continue
        claims=[{'claim_id':cid,'claim_type':qm[cid]['claim_type'],'statement':qm[cid]['statement'],
            'entity_context':copy.deepcopy(qm[cid]['entity_context']),'parent_claim_ids':parents.get(cid,[])} for cid in sorted(target)]
        if len(claims)>24:raise ValueError('batch_exceeds_predeclared_24_claim_limit')
        tasks.append({'id':r['pair_id'],'input':{'image_path':r['bundle']['image_path'],'image_sha256':r['bundle']['image_sha256'],'claims':claims}})
    write_jsonl(ROOT/'tasks.jsonl',tasks);write_jsonl(ROOT/'shots.jsonl',shots())
    write_json(ROOT/'protocol.json',{'source_sha':sha(SOURCE),'source_coverage':292,'denominator':400,'model':'deepseek-flash',
        'intervention':'only visual query organization: joint region inventory and parent-bound evidence; fixed old M3/M2',
        'fewshot':6,'references_sent':False,'target_policy':'all residual uncertain/pending plus parent conflicts across all 400 pairs',
        'max_claims_per_call':24,'requests':len(tasks),'claims':sum(len(t['input']['claims']) for t in tasks),
        'merge':'new condition replaces uncertain only; changed decided label becomes uncertain; no majority vote'})
    print(read_json(ROOT/'protocol.json'),flush=True)


def calls(resume=False):
    tasks=read_jsonl(ROOT/'tasks.jsonl');out=ROOT/'calls'
    if out.exists():
        if not resume:raise ValueError('resume_required')
        manifest=check_frozen(out)
    else:
        new_run(out,'joint_visual_graph',[ROOT/'tasks.jsonl',ROOT/'shots.jsonl',ROOT/'protocol.json',SOURCE,*routing_inputs(base.ROUTES)],
            {'model':'deepseek-flash','workers':4},[*Path(__file__).parent.glob('*.py'),*Path('analysis_skeleton/final_v1').glob('*.py'),
                *Path('analysis_skeleton/framework_v2').glob('*.py'),Path('experiments/matrix_recovery_v4/bounds.py'),
                Path('experiments/coco400_revision_v2/visual.py'),Path('experiments/coco400_v1/observe.py')])
        manifest=read_json(out/'manifest.json')
    def work(t):
        if not hasattr(LOCAL,'stage'):LOCAL.stage=SafeStage(JointStage())
        cp=Checkpoints(out/'checkpoints',digest(manifest));result=cp.call(t['id'],LOCAL.stage,t['input'],lambda raw:compiled(raw,t['input']))
        return {'id':t['id'],'result':result,'new_calls':cp.new_api_calls}
    rows=[]
    with output_lock(out),ThreadPoolExecutor(max_workers=4) as pool:
        for f in as_completed([pool.submit(work,t) for t in tasks]):
            rows.append(f.result())
            if len(rows)%10==0 or len(rows)==len(tasks):print('joint',len(rows),'/',len(tasks),flush=True)
    write_jsonl(out/'results.jsonl',rows);write_json(out/'summary.json',{'requests':len(rows),'new_calls':sum(r['new_calls'] for r in rows),'statuses':dict(Counter(r['result']['status'] for r in rows))})


def report():
    prior=read_jsonl(SOURCE);results={r['id']:r['result'] for r in read_jsonl(ROOT/'calls/results.jsonl')};rows=copy.deepcopy(prior);changes=[]
    for r in rows:
        saved=results.get(r['pair_id'])
        if saved and saved['status']=='complete':
            vals=saved['value']['claims']
            for v in r['verification']:
                if v['claim_id'] not in vals:continue
                new={**vals[v['claim_id']],'audit':saved.get('audit',{})};old=v['label'];v.update(merge(v,new))
                v['v5_joint_response_id']=saved.get('audit',{}).get('response_id')
                changes.append({'pair_id':r['pair_id'],'claim_id':v['claim_id'],'before':old,'after':v['label'],'status':new['status']})
        base.recompute(r);r['observation']=tighten(r['observation'],r['ledger'],r['bundle'])
    base.ROOT=ROOT;base.emit('joint',rows)
    summary,trans=compare({r['pair_id']:r for r in prior},rows)
    summary['calls']=read_json(ROOT/'calls/summary.json');summary['visual_transitions']=[{'before':a,'after':b,'count':n} for (a,b),n in Counter((x['before'],x['after']) for x in changes).items()]
    summary['local_claim_failures']=sum(x['status']!='complete' for x in changes);summary['independent_accuracy_measured']=False
    check_frozen(ROOT/'calls')
    for a,b in zip(prior,rows):
        assert a['pair_id']==b['pair_id'] and digest(a['bundle'])==digest(b['bundle'])
    assert len(rows)==400 and sum(len(r['ledger']) for r in rows)==5959
    write_json(ROOT/'summary.json',summary);write_jsonl(ROOT/'transitions.jsonl',trans);write_jsonl(ROOT/'claim_transitions.jsonl',changes)
    write_jsonl(ROOT/'remaining_cases.jsonl',[{'pair_id':r['pair_id'],'original':r['bundle']['original']['text'],'steer':r['bundle']['steer']['text'],'observation':r['observation']} for r in rows if not r['observation']['matrix_classifiable']])
    print(json.dumps(summary,ensure_ascii=False),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run','report']);p.add_argument('--resume',action='store_true');a=p.parse_args()
    if a.action=='prepare':prepare()
    elif a.action=='run':calls(a.resume)
    else:report()
