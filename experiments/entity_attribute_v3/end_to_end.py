"""Reusable fresh-pair entry point: frozen M2 -> revised M3 -> M5 -> one targeted review."""
import argparse,copy,json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from analysis_skeleton.common import read_json,read_jsonl,write_json,write_jsonl,new_run,check_frozen,digest
from analysis_skeleton.framework_v2.runtime import Checkpoints
from analysis_skeleton.framework_v2.ledger import production
from analysis_skeleton.final_v1.routing import routing_inputs
from decomposition.storage import output_lock
from .pipeline import execute
from experiments.coco400_revision_v2.visual import ReviewStage,validate_typed,merge
from experiments.coco400_revision_v2.observation import analyze_pair
from .retention import analyze as retention_analysis


def run_full(pairs_path,output,profile='outputs/final_v1_release/profile.json',resume=False,
             stages=None,review_stage=None,workers=8,parser=None,variant='m2_only',config='decomposition/api_config.local.json'):
    profile=read_json(profile) if isinstance(profile,(str,Path)) else copy.deepcopy(profile)
    if profile.get('visual_candidate')!='typed':raise ValueError('v3_requires_explicit_typed_visual_profile')
    routes=profile['visual_shots_path']
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    first=execute(pairs_path,out/'first_pass',profile=profile,resume=resume,stages=stages,parser=parser,
                  condition_id='entity_attribute_v3_'+variant,replicate_id='r1',variant=variant,config=config)
    base=out/'first_pass';bundles=read_jsonl(base/'bundles.jsonl');queue=read_jsonl(base/'verification_queue.jsonl')
    values=read_jsonl(base/'verification.jsonl');ledger=read_jsonl(base/'denominator_ledger.jsonl')
    vm={v['claim_id']:v for v in values};qm={q['claim_id']:q for q in queue}
    byref={(q['pair_id'],ref['side'],ref['fact_id']):q['claim_id'] for q in queue for ref in q['refs']}
    targets={cid for cid,v in vm.items() if v['label']=='uncertain'}
    for r in ledger:
        if r['type']=='attribute' and (r['claim_id'] in targets or (r['visual_label']=='supported' and r['parent_visual_label']!='supported')):
            targets.add(r['claim_id']);parent=byref.get((r['pair_id'],r['side'],'entity_'+r['entity_id']))
            if parent:targets.add(parent)
    tasks=[]
    for cid in sorted(targets):
        q=qm[cid];v=vm[cid]
        payload={k:copy.deepcopy(q[k]) for k in ('image_path','image_sha256','statement','entity_context','claim_type')}
        payload.update(review_bbox=v.get('evidence',{}).get('bbox'),review_focus='locate the intended referent in the full image' if q['claim_type']=='entity' else 'resolve the owner, then inspect '+q['slot'])
        tasks.append({'id':cid,'input':payload})
    taskfile=out/'review_tasks.jsonl'
    if taskfile.exists():
        if read_jsonl(taskfile)!=tasks:raise ValueError('review_task_identity_changed')
    else:write_jsonl(taskfile,tasks)
    stage=review_stage or ReviewStage(routes,config_path=config)
    review=out/'review'
    if review.exists():
        manifest=check_frozen(review)
        if manifest['config']['stage']!=stage.identity:raise ValueError('review_stage_identity_changed')
    else:
        new_run(review,'one_bounded_visual_review',[taskfile,base/'manifest.json',base/'bundles.jsonl',base/'verification.jsonl',
            *routing_inputs(routes)],{'stage':stage.identity,'workers':workers},list(Path(__file__).parent.glob('*.py')))
        manifest=read_json(review/'manifest.json')
    def work(t):
        cp=Checkpoints(review/'checkpoints',digest(manifest));r=cp.call(t['id'],stage,t['input'],lambda raw:validate_typed(raw,t['input']['claim_type']))
        return {'id':t['id'],'result':r,'new_calls':cp.new_api_calls}
    with output_lock(review),ThreadPoolExecutor(max_workers=workers) as pool:results=list(pool.map(work,tasks))
    write_jsonl(review/'results.jsonl',results)
    for saved in results:vm[saved['id']]=merge(vm[saved['id']],saved['result'])
    records=[];allledger=[]
    for b in bundles:
        qq=[q for q in queue if q['pair_id']==b['pair_id']];vv=[vm[q['claim_id']] for q in qq]
        ll,_,_,_=production(b,qq,vv);ob,events=analyze_pair(b,ll);allledger+=ll
        records.append({'pair_id':b['pair_id'],'bundle':b,'queue':qq,'verification':vv,'ledger':ll,'observation':ob,'events':events})
    write_jsonl(out/'pairs.jsonl',records);write_jsonl(out/'denominator_ledger.jsonl',allledger)
    write_jsonl(out/'observation_pairs.jsonl',[r['observation'] for r in records])
    summary={'selected_pairs':first['selected_pairs'],'analyzed_pairs':len(records),'first_pass_metrics':first,
        'review_tasks':len(tasks),'review_new_calls':sum(r['new_calls'] for r in results),
        'matrix_classifiable':sum(r['observation']['matrix_classifiable'] for r in records),
        'facts':len(allledger),'semantic_accuracy_measured':False}
    retention,attribute_rows,pair_rates,entity_rows=retention_analysis(records)
    write_json(out/'retention.json',retention);write_jsonl(out/'conditional_attribute_denominator.jsonl',attribute_rows)
    write_jsonl(out/'entity_retention_denominator.jsonl',entity_rows);write_jsonl(out/'retention_by_pair.jsonl',pair_rates)
    summary['variant']=variant;write_json(out/'summary.json',summary);return summary


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--pairs',required=True);p.add_argument('--output',required=True)
    p.add_argument('--profile',default='outputs/final_v1_release/profile.json');p.add_argument('--resume',action='store_true')
    p.add_argument('--variant',choices=['baseline','m2_only','m3_only','combined'],default='m2_only')
    p.add_argument('--config',default='decomposition/api_config.local.json');a=p.parse_args()
    print(json.dumps(run_full(a.pairs,a.output,a.profile,a.resume,variant=a.variant,config=a.config),ensure_ascii=False))
