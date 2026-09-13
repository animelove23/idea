"""Review exactly the frozen B2 queue; merge with explicit provenance, no repeated voting."""
import argparse,copy,json,threading
from concurrent.futures import ThreadPoolExecutor,as_completed
from collections import Counter
from pathlib import Path
from analysis_skeleton.common import read_jsonl,read_json,write_jsonl,write_json,new_run,check_frozen,digest
from analysis_skeleton.framework_v2.runtime import Checkpoints
from analysis_skeleton.framework_v2.ledger import production
from analysis_skeleton.final_v1.routing import routing_inputs
from decomposition.storage import output_lock
from .visual import ReviewStage,validate_typed,merge
from .observation import analyze_pair
from . import run

ROOT=Path('outputs/coco400_revision_v2_guard');LOCAL=threading.local()


def execute(resume=False):
    tasks=read_jsonl(ROOT/'review_rebound_tasks.jsonl');out=ROOT/'review_rebound_calls'
    if out.exists():
        if not resume:raise ValueError('existing_review_requires_resume')
        manifest=check_frozen(out)
    else:
        new_run(out,'independent_review_and_rebinding',[ROOT/'review_rebound_tasks.jsonl',ROOT/'B2_local_and_rebinding/pairs.jsonl',
            *routing_inputs('outputs/final_v1_release/visual_routes.json')],{'model':'deepseek-flash','workers':8,'calls':len(tasks)},list(Path(__file__).parent.glob('*.py')))
        manifest=read_json(out/'manifest.json')
    def work(t):
        if not hasattr(LOCAL,'stage'):LOCAL.stage=ReviewStage('outputs/final_v1_release/visual_routes.json')
        cp=Checkpoints(out/'checkpoints',digest(manifest))
        record=cp.call(t['id'],LOCAL.stage,t['input'],lambda raw:validate_typed(raw,t['input']['claim_type']))
        return {'id':t['id'],'purpose':t['purpose'],'result':record,'new_calls':cp.new_api_calls}
    results=[]
    with output_lock(out),ThreadPoolExecutor(max_workers=8) as pool:
        for f in as_completed([pool.submit(work,t) for t in tasks]):
            results.append(f.result())
            if len(results)%40==0 or len(results)==len(tasks):print('visual',len(results),'/',len(tasks),flush=True)
    write_jsonl(out/'results.jsonl',results)
    print({'statuses':dict(Counter(r['result']['status'] for r in results)),'new_calls':sum(r['new_calls'] for r in results)},flush=True)


def summarize():
    run.ROOT=ROOT;reviews={r['id']:r for r in read_jsonl(ROOT/'review_rebound_calls/results.jsonl')};records=[];transitions=[]
    for r in read_jsonl(ROOT/'B2_local_and_rebinding/pairs.jsonl'):
        for v in r['verification']:
            saved=reviews.get(r['pair_id']+':'+v['claim_id'])
            if saved:
                before=v['label'];v.update(merge(v,saved['result']))
                transitions.append({'pair_id':r['pair_id'],'claim_id':v['claim_id'],'purpose':saved['purpose'],'before':before,'after':v['label'],
                    'review_status':saved['result']['status'],'review_response_id':saved['result'].get('audit',{}).get('response_id')})
        ledger,_,_,_=production(r['bundle'],r['queue'],r['verification']);r['ledger']=ledger
        r['observation'],r['events']=analyze_pair(r['bundle'],ledger);records.append(r)
    run.emit('C_reviewed',records);write_jsonl(ROOT/'C_reviewed/review_transitions.jsonl',transitions)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--resume',action='store_true');p.add_argument('--summarize',action='store_true');a=p.parse_args()
    if a.summarize:summarize()
    else:execute(a.resume)
