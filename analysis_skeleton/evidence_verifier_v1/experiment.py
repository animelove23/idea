"""Compare direct labeling with one-call evidence observation and deterministic labels."""
import argparse,copy,json,random
from pathlib import Path
from collections import Counter
from decomposition.storage import output_lock
from analysis_skeleton.common import read_json,read_jsonl,write_json,write_jsonl,new_run,check_frozen,sha,digest
from analysis_skeleton.m5_verify import VisualStage,validate_label,score_labels
from analysis_skeleton.framework_v2.runtime import SafeStage,Checkpoints,query_payload
from .stage import EvidenceStage,make_evidence_shots,validate_evidence,ROOT

def prepare(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    if (root/'protocol.json').exists():raise ValueError('already_prepared')
    original=read_jsonl('analysis_skeleton/shots/verify.jsonl');write_jsonl(root/'shots.jsonl',make_evidence_shots(original))
    inputs=read_jsonl('outputs/visual_shot_context_v1/inputs.jsonl');refs=read_jsonl('outputs/visual_shot_context_v1/references.jsonl')
    assert len(inputs)==60 and not {r['input']['image_sha256'] for r in inputs}&{r['input']['image_sha256'] for r in original}
    write_jsonl(root/'inputs.jsonl',inputs);write_jsonl(root/'references.jsonl',refs)
    order=[(r['case_id'],c) for r in inputs for c in ('control','evidence')];random.Random(20260916).shuffle(order);write_json(root/'order.json',order)
    write_json(root/'protocol.json',{'factor':'visual decision interface: free label vs structured visual evidence plus fixed decision table','operational_changes':['evidence output schema','system instructions for that schema','same six demonstrations expressed in evidence fields','deterministic compiler'],'causal_claim_limit':'one module-level intervention; cannot attribute gain to any individual field or sentence','unchanged':['model','thinking disabled','temperature','query statement/context','original images','six-shot image/question order','reference labels','M2/M3'],'candidate_count':1,'cases':60,'entity_cases':41,'attribute_guard_cases':19,'calls_planned':120,'calls_per_claim':1,'no_extra_judge_or_crop':True,'acceptance':'entity >=37/41 and better than control; no more confident entity errors; attribute agreement not below control; no technical failures','development_not_holdout':True,'evidence_and_bbox_are_model_predictions':True,'references_are_assistant_candidates':True,'test_reference_labels_in_requests':False})
    print({'cases':60,'shots':6,'planned_calls':120},flush=True)

def run(root,resume=False):
    root=Path(root);stages={'control':SafeStage(VisualStage()),'evidence':SafeStage(EvidenceStage(root/'shots.jsonl'))}
    rows=read_jsonl(root/'inputs.jsonl');by_id={r['case_id']:r for r in rows};order=read_json(root/'order.json')
    files=[root/n for n in ('inputs.jsonl','references.jsonl','shots.jsonl','order.json','protocol.json')]+[ROOT/'prompt.txt',Path('analysis_skeleton/prompts/verify.txt'),Path('analysis_skeleton/shots/verify.jsonl')]
    files += [r['input']['image_path'] for r in rows]+[r['input']['image_path'] for r in stages['control'].source.shots]
    code=[__file__,ROOT/'stage.py','analysis_skeleton/framework_v2/runtime.py','analysis_skeleton/llm.py','analysis_skeleton/m5_verify.py']
    identity={'stages':{c:s.identity for c,s in stages.items()},'order':order,'fresh':True,'replicate_id':'r1'};out=root/'run'
    if resume:
        manifest=check_frozen(out)
        if manifest['config']!=identity:raise ValueError('resume_identity_changed')
    else:new_run(out,'evidence_verifier_v1',files,identity,code);manifest=read_json(out/'manifest.json')
    with output_lock(out):
        cp=Checkpoints(out/'checkpoints',digest(manifest),cache_mode='fresh');results=[]
        for i,(cid,condition) in enumerate(order):
            check_frozen(out);r=by_id[cid];payload=copy.deepcopy(r['input'])
            validator=validate_label
            if condition=='evidence':
                payload['claim_type']=r['semantic_type'];validator=lambda raw,kind=r['semantic_type']:validate_evidence(raw,kind)
            v=cp.call(cid+':'+condition,stages[condition],payload,validator)
            record={k:r[k] for k in ('case_id','image_id','semantic_type')};record.update(condition=condition,status=v['status'],prediction=v.get('value',{}),audit=v.get('audit',{}))
            if 'diagnostic' in v:record['diagnostic']=v['diagnostic']
            results.append(record);write_jsonl(out/'results.jsonl',results)
            print(f"{i+1}/120 {cid} {condition}: {record['prediction'].get('label',v['status'])}",flush=True)
            if i==0 and v['status']!='complete':raise RuntimeError('first_call_failed')
        write_json(root/('resume_metrics.json' if resume else 'call_metrics.json'),{'new_api_calls':cp.new_api_calls,'resumed':cp.resumed,'records':len(results),'status':dict(Counter(r['status'] for r in results))})

def score(rows,n):
    m=score_labels(rows);m['correct']=sum(r['prediction'].get('label')==r['reference_label'] for r in rows);m['agreement']=m['correct']/n
    m['confident_errors']=sum(r['prediction'].get('label') in ('supported','hallucinated') and r['prediction']['label']!=r['reference_label'] for r in rows)
    m['input_tokens']=sum((r['audit'].get('usage') or {}).get('prompt_tokens',0) or 0 for r in rows)
    m['output_tokens']=sum((r['audit'].get('usage') or {}).get('completion_tokens',0) or 0 for r in rows)
    return m

def report(root):
    root=Path(root);check_frozen(root/'run');rows=read_jsonl(root/'run/results.jsonl');refs={r['case_id']:r for r in read_jsonl(root/'references.jsonl')};metrics={};paired=[]
    scored=[{**r,'reference_label':refs[r['case_id']]['reference_label']} for r in rows]
    for c in ('control','evidence'):
        subset=[r for r in scored if r['condition']==c]
        metrics[c]={'all':score(subset,60),'entity':score([r for r in subset if r['semantic_type']=='entity'],41),'attribute':score([r for r in subset if r['semantic_type']=='attribute'],19)}
    for cid in refs:
        group={r['condition']:r for r in scored if r['case_id']==cid}
        if len(group)!=2:continue
        a,b=group['control'],group['evidence'];gold=refs[cid]['reference_label']
        assert query_payload('verify',a['audit']['input'])==query_payload('verify',b['audit']['input'])
        paired.append({'case_id':cid,'semantic_type':a['semantic_type'],'reference':gold,'control':a['prediction'].get('label'),'evidence_label':b['prediction'].get('label'),'control_reason':a['prediction'].get('reason'),'evidence_record':b['prediction'].get('evidence'),'decision_rule':b['prediction'].get('decision_rule'),'improved':a['prediction'].get('label')!=gold and b['prediction'].get('label')==gold,'regressed':a['prediction'].get('label')==gold and b['prediction'].get('label')!=gold})
    metrics['paired']={kind:{k:sum(r[k] for r in paired if r['semantic_type']==kind) for k in ('improved','regressed')} for kind in ('entity','attribute')}
    metrics['engineering']={'all_120_complete':len(rows)==120 and all(r['status']=='complete' for r in rows),'unique_responses':len({r['audit'].get('response_id') for r in rows})==120,'all_fresh':all(r['audit'].get('api_calls')==1 and not r['audit'].get('cache_hit') for r in rows),'same_semantic_query_inputs':len(paired)==60,'requested_returned_models_match':all(r['audit']['identity']['model']==r['audit'].get('response_model') for r in rows)}
    a,b=metrics['control'],metrics['evidence'];metrics['accept_candidate']=b['entity']['correct']>=37 and b['entity']['correct']>a['entity']['correct'] and b['entity']['confident_errors']<=a['entity']['confident_errors'] and b['attribute']['correct']>=a['attribute']['correct'] and all(metrics['engineering'].values())
    write_json(root/'metrics.json',metrics);write_jsonl(root/'paired.jsonl',paired)
    write_jsonl(root/'evidence_records.jsonl',[{'case_id':r['case_id'],'image_id':r['image_id'],'semantic_type':r['semantic_type'],**r['prediction']} for r in rows if r['condition']=='evidence'])
    print(json.dumps(metrics,ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['prepare','run','report']);p.add_argument('--output',required=True);p.add_argument('--resume',action='store_true');a=p.parse_args()
    if a.phase=='prepare':prepare(a.output)
    elif a.phase=='run':run(a.output,a.resume)
    else:report(a.output)
