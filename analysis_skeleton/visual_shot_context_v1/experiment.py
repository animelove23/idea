"""Single-factor X5a: contextualize six existing examples, same fixed 60 claims."""
import argparse,copy,json,random
from pathlib import Path
from collections import Counter
from decomposition.storage import output_lock
from analysis_skeleton.common import read_json,read_jsonl,write_json,write_jsonl,new_run,check_frozen,sha,digest
from analysis_skeleton.m5_verify import VisualStage,validate_label,score_labels
from analysis_skeleton.framework_v2.runtime import SafeStage,Checkpoints,query_payload
from .stage import with_context,ContextShotStage

def prepare(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    if (root/'protocol.json').exists():raise ValueError('already_prepared')
    oldshots=read_jsonl('analysis_skeleton/shots/verify.jsonl');write_jsonl(root/'shots.jsonl',with_context(oldshots))
    pairs={p['image_id']:p for p in read_jsonl('analysis_skeleton/fixtures/expansion20/pairs.jsonl')}
    old=read_jsonl('outputs/skeleton_repair_v1/visual_ab/results.jsonl');inputs=[]
    for r in old:
        if r['condition']!='context':continue
        payload=copy.deepcopy(r['audit']['input']);payload['image_path']=pairs[r['image_id']]['image_path']
        assert sha(payload['image_path'])==payload['image_sha256']
        inputs.append({'case_id':r['case_id'],'image_id':r['image_id'],'semantic_type':r['semantic_type'],'input':payload})
    assert len(inputs)==60 and len({r['case_id'] for r in inputs})==60
    assert not {r['input']['image_sha256'] for r in inputs}&{r['input']['image_sha256'] for r in oldshots}
    write_jsonl(root/'inputs.jsonl',inputs);write_jsonl(root/'references.jsonl',read_jsonl('analysis_skeleton/fixtures/expansion20/verify_cases.jsonl'))
    order=[(r['case_id'],c) for r in inputs for c in ('control','shot_context')];random.Random(20260915).shuffle(order);write_json(root/'order.json',order)
    write_json(root/'protocol.json',{'single_factor':'X5a: add source-derived context fields to six existing few-shot inputs','source_window':'original example statement; no new caption or visual box','cases':60,'entity_cases':41,'attribute_guard':19,'calls_planned':120,'conditions':['control','shot_context'],'six_example_images_statements_answers_order':'unchanged','query_images_statements_context':'unchanged full images, no tiles','model_and_system_prompt':'unchanged','reference_labels':'unchanged assistant candidates','min_entity_correct':37,'acceptance':'entity >=37/41, better than control; no more confident entity errors; attribute correct count not lower; all technical checks pass','development_only':True,'candidate_count':1})
    print({'cases':60,'calls':120,'shot_count':6},flush=True)

def run(root,resume=False):
    root=Path(root);stages={'control':SafeStage(VisualStage()),'shot_context':SafeStage(ContextShotStage(root/'shots.jsonl'))}
    rows=read_jsonl(root/'inputs.jsonl');by_id={r['case_id']:r for r in rows};order=read_json(root/'order.json')
    identity={'stages':{k:s.identity for k,s in stages.items()},'order':order,'fresh':True,'replicate_id':'r1'}
    files=[root/n for n in ('protocol.json','shots.jsonl','inputs.jsonl','references.jsonl','order.json')]+[Path('analysis_skeleton/prompts/verify.txt'),Path('analysis_skeleton/shots/verify.jsonl')]
    files += [r['input']['image_path'] for r in rows]+[r['input']['image_path'] for r in stages['control'].source.shots]
    code=[__file__,Path(__file__).parent/'stage.py','analysis_skeleton/framework_v2/runtime.py','analysis_skeleton/llm.py','analysis_skeleton/m5_verify.py']
    out=root/'run'
    if resume:
        manifest=check_frozen(out)
        if manifest['config']!=identity:raise ValueError('identity_changed')
    else:new_run(out,'visual_shot_context_v1',files,identity,code);manifest=read_json(out/'manifest.json')
    with output_lock(out):
        cp=Checkpoints(out/'checkpoints',digest(manifest),cache_mode='fresh');results=[]
        for i,(cid,condition) in enumerate(order):
            check_frozen(out);r=by_id[cid];v=cp.call(cid+':'+condition,stages[condition],r['input'],validate_label)
            record={k:r[k] for k in ('case_id','image_id','semantic_type')};record.update(condition=condition,status=v['status'],prediction=v.get('value',{}),audit=v.get('audit',{}))
            results.append(record);write_jsonl(out/'results.jsonl',results)
            print(f"{i+1}/120 {cid} {condition}: {record['prediction'].get('label',v['status'])}",flush=True)
            if i==0 and v['status']!='complete':raise RuntimeError('first_call_failed')
        write_json(root/('resume_metrics.json' if resume else 'call_metrics.json'),{'new_api_calls':cp.new_api_calls,'resumed':cp.resumed,'records':len(results),'status':dict(Counter(r['status'] for r in results))})

def score(rows,expected):
    result=score_labels(rows);result['correct']=sum(r['prediction'].get('label')==r['reference_label'] for r in rows);result['agreement']=result['correct']/expected
    result['confident_errors']=sum(r['prediction'].get('label') in ('supported','hallucinated') and r['prediction']['label']!=r['reference_label'] for r in rows)
    return result

def report(root):
    root=Path(root);check_frozen(root/'run');rows=read_jsonl(root/'run/results.jsonl');refs={r['case_id']:r for r in read_jsonl(root/'references.jsonl')}
    rows=[{**r,'reference_label':refs[r['case_id']]['reference_label']} for r in rows];metrics={};paired=[]
    for condition in ('control','shot_context'):
        subset=[r for r in rows if r['condition']==condition]
        metrics[condition]={'all':score(subset,60),'entity':score([r for r in subset if r['semantic_type']=='entity'],41),'attribute':score([r for r in subset if r['semantic_type']=='attribute'],19)}
    for cid in refs:
        group={r['condition']:r for r in rows if r['case_id']==cid}
        if len(group)!=2:continue
        a,b=group['control'],group['shot_context'];gold=refs[cid]['reference_label']
        assert query_payload('verify',a['audit']['input'])==query_payload('verify',b['audit']['input'])
        paired.append({'case_id':cid,'semantic_type':a['semantic_type'],'reference':gold,'control':a['prediction'].get('label'),'shot_context':b['prediction'].get('label'),'control_reason':a['prediction'].get('reason'),'candidate_reason':b['prediction'].get('reason'),'improved':a['prediction'].get('label')!=gold and b['prediction'].get('label')==gold,'regressed':a['prediction'].get('label')==gold and b['prediction'].get('label')!=gold})
    metrics['paired']={kind:{k:sum(r[k] for r in paired if r['semantic_type']==kind) for k in ('improved','regressed')} for kind in ('entity','attribute')}
    metrics['engineering']={'all_120_complete':len(rows)==120 and all(r['status']=='complete' for r in rows),'unique_responses':len({r['audit'].get('response_id') for r in rows})==120,'all_fresh':all(r['audit'].get('api_calls')==1 and not r['audit'].get('cache_hit') for r in rows),'same_queries':len(paired)==60,'requested_returned_models_match':all(r['audit']['identity']['model']==r['audit'].get('response_model') for r in rows)}
    a,b=metrics['control'],metrics['shot_context'];metrics['accept_candidate']=b['entity']['correct']>=37 and b['entity']['correct']>a['entity']['correct'] and b['entity']['confident_errors']<=a['entity']['confident_errors'] and b['attribute']['correct']>=a['attribute']['correct'] and all(metrics['engineering'].values())
    write_json(root/'metrics.json',metrics);write_jsonl(root/'paired.jsonl',paired)
    lines=['# X5a：现有6-shot主体字段补齐测试','','仅补齐现有示例的entity_context，示例图像、命题、答案、顺序及数量不变；查询使用原图，未叠加局部视图。全部60条固定视觉命题两条件交错、fresh调用。','','| 条件 | 实体正确/41 | 属性正确/19 | 整体正确/60 | 整体Macro-F1 |','|---|---:|---:|---:|---:|']
    for c in ('control','shot_context'):
        m=metrics[c];lines.append(f"| {c} | {m['entity']['correct']} ({m['entity']['agreement']:.2%}) | {m['attribute']['correct']} | {m['all']['correct']} | {m['all']['macro_f1']:.2%} |")
    lines += ['',f"是否达到预设接受条件：{metrics['accept_candidate']}。",'','## 变化样本','']
    for r in paired:
        if r['control']!=r['shot_context']:lines += [f"- {r['case_id']}（{r['semantic_type']}）：参考{r['reference']}；{r['control']} → {r['shot_context']}。原理由：{r['control_reason']}；候选理由：{r['candidate_reason']}"]
    lines += ['','## 解释限制','','- 参考仍是旧助手候选，图像已用于开发；不是独立人工gold或未见确认集。','- source_window使用原示例命题本身，没有虚构完整caption或视觉边框。此实验衡量输入字段格式对齐，不代表新增视觉定位证据。','- 没有添加或替换示例内容，不归因于某一新增正反例。','- 主框架默认行为未修改；不通过则保留为失败实验。']
    (root/'RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8');print(json.dumps(metrics,ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['prepare','run','report']);p.add_argument('--output',required=True);p.add_argument('--resume',action='store_true');a=p.parse_args()
    if a.phase=='prepare':prepare(a.output)
    elif a.phase=='run':run(a.output,a.resume)
    else:report(a.output)
