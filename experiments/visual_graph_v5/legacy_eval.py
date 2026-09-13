"""Frozen 579 legacy labels, never present in model input; diagnostic not new gold."""
import argparse,json,threading
from pathlib import Path
from collections import defaultdict,Counter
from concurrent.futures import ThreadPoolExecutor,as_completed
from analysis_skeleton.common import read_jsonl,read_json,write_jsonl,write_json,new_run,check_frozen,digest
from analysis_skeleton.framework_v2.runtime import SafeStage,Checkpoints
from analysis_skeleton.m5_verify import score_labels
from analysis_skeleton.final_v1.routing import routing_inputs
from decomposition.storage import output_lock
from .stage import JointStage
from .search_binding import validate

ROOT=Path('outputs/visual_graph_v5/legacy579');LOCAL=threading.local()

def prepare():
    ROOT.mkdir(exist_ok=False);refs=read_jsonl('outputs/final_v1_m5/references.jsonl')
    inputs={}
    for t in read_jsonl('outputs/final_v1_m5/tasks.jsonl'):
        if t['condition']==('context' if t['semantic_type']=='entity' else 'proposition'):inputs[t['case_id']]=t['input']
    groups=defaultdict(list)
    for r in refs:groups[r['image_id']].append(r)
    tasks=[]
    for pid,rr in sorted(groups.items()):
        for i in range(0,len(rr),12):
            subset=rr[i:i+12];first=inputs[subset[0]['case_id']]
            payload={k:first[k] for k in ('image_path','image_sha256')}
            payload['claims']=[{'claim_id':r['case_id'],'statement':inputs[r['case_id']]['statement'],
                'entity_context':inputs[r['case_id']].get('entity_context',{}),'claim_type':r['semantic_type'],'parent_claim_ids':[]} for r in subset]
            tasks.append({'id':pid+':'+str(i//12),'input':payload})
    write_jsonl(ROOT/'tasks.jsonl',tasks);write_jsonl(ROOT/'references.jsonl',[{'case_id':r['case_id'],'semantic_type':r['semantic_type'],'label':r['reference_label']} for r in refs])
    write_json(ROOT/'protocol.json',{'cases':len(refs),'images':len(groups),'requests':len(tasks),'shots':6,'batch_limit':12,
        'reference_status':'reused_legacy_labels_not_new_independent_gold','query_has_references':False,
        'parent_links':'legacy claims lack reliable subject IDs; no inferred parent edges in this compatibility evaluation'})
    print(read_json(ROOT/'protocol.json'),flush=True)

def run():
    out=ROOT/'run';tasks=read_jsonl(ROOT/'tasks.jsonl')
    new_run(out,'legacy579_joint_validation',[ROOT/'tasks.jsonl',ROOT/'protocol.json',*routing_inputs('outputs/final_v1_release/visual_routes.json')],
        {'model':'deepseek-flash','calls':len(tasks),'workers':4},list(Path(__file__).parent.glob('*.py')))
    manifest=read_json(out/'manifest.json')
    def work(t):
        if not hasattr(LOCAL,'stage'):LOCAL.stage=SafeStage(JointStage())
        cp=Checkpoints(out/'checkpoints',digest(manifest));r=cp.call(t['id'],LOCAL.stage,t['input'],lambda raw:validate(raw,t['input']))
        return {'id':t['id'],'result':r,'new_calls':cp.new_api_calls}
    rows=[]
    with output_lock(out),ThreadPoolExecutor(max_workers=4) as pool:
        for f in as_completed([pool.submit(work,t) for t in tasks]):
            rows.append(f.result())
            if len(rows)%10==0 or len(rows)==len(tasks):print('legacy',len(rows),'/',len(tasks),flush=True)
    write_jsonl(out/'results.jsonl',rows)

def report():
    results=read_jsonl(ROOT/'run/results.jsonl');pred={}
    for r in results:
        if r['result']['status']=='complete':pred.update(r['result']['value']['claims'])
    rows=[];old={r['case_id']:r for r in read_jsonl('outputs/final_v1_m5/paired.jsonl')}
    for ref in read_jsonl(ROOT/'references.jsonl'):
        p=pred.get(ref['case_id'],{});base=old[ref['case_id']]
        rows.append({**ref,'prediction':p.get('value',{}).get('label','technical_failure'),
            'baseline':base['context' if ref['semantic_type']=='entity' else 'proposition'],'prediction_status':p.get('status','technical_failure')})
    summary={}
    for kind in ('entity','attribute','all'):
        rr=[r for r in rows if kind=='all' or r['semantic_type']==kind]
        summary[kind]={'cases':len(rr),'baseline_correct':sum(r['baseline']==r['label'] for r in rr),
            'joint_correct':sum(r['prediction']==r['label'] for r in rr),'joint_agreement':sum(r['prediction']==r['label'] for r in rr)/len(rr),
            'false_supported':sum(r['prediction']=='supported' and r['label']=='hallucinated' for r in rr),
            'false_hallucinated':sum(r['prediction']=='hallucinated' and r['label']=='supported' for r in rr),
            'technical_failures':sum(r['prediction']=='technical_failure' for r in rr)}
    summary['calls']={'requests':len(results),'new_calls':sum(r['new_calls'] for r in results),'statuses':dict(Counter(r['result']['status'] for r in results))}
    check_frozen(ROOT/'run');write_json(ROOT/'summary.json',summary);write_jsonl(ROOT/'paired.jsonl',rows)
    print(json.dumps(summary,ensure_ascii=False),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run','report']);a=p.parse_args()
    {'prepare':prepare,'run':run,'report':report}[a.action]()
