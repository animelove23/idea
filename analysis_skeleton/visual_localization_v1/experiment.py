"""Frozen full-image versus original-pixel multiview entity experiment."""
import argparse,copy,json,random
from pathlib import Path
from collections import Counter
from decomposition.storage import output_lock
from analysis_skeleton.common import read_json,read_jsonl,write_json,write_jsonl,new_run,check_frozen,sha,digest
from analysis_skeleton.m5_verify import VisualStage,validate_label,score_labels
from analysis_skeleton.framework_v2.runtime import SafeStage,Checkpoints,query_payload
from .views import MultiViewStage,prepare_views,POLICY

def prepare(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    if (root/'protocol.json').exists():raise ValueError('already_prepared')
    inputs=read_jsonl('outputs/visual_entity_v3/inputs.jsonl')
    assert len(inputs)==41
    views={r['input']['image_sha256']:prepare_views(r['input'],root/'views') for r in inputs}
    write_json(root/'view_manifest.json',views);write_jsonl(root/'inputs.jsonl',inputs)
    write_jsonl(root/'references.jsonl',read_jsonl('outputs/visual_entity_v3/references.jsonl'))
    order=[(r['case_id'],c) for r in inputs for c in ('control','multiview')]
    random.Random(20260914).shuffle(order);write_json(root/'order.json',order)
    write_json(root/'protocol.json',{'single_factor':'query image representation: full original versus full original plus four deterministic overlapping original-pixel views','view_policy':POLICY,'model':'deepseek-flash','prompt':'original verify.txt','six_shots':'unchanged','case_count':41,'calls':82,'candidate_count':1,'min_correct_for_90_percent':37,'minimum_effect':'candidate >= 37/41, improves over same-run control, no increase in confident S/H errors','no_reference_relabeling':True,'development_cohort':True,'independent_test':False,'candidate_locations':'not selected by labels, entities, reference boxes or model outputs','attribute_acceptance':'not tested in this entity-only experiment','next_if_pass':'repeat and evaluate fixed attribute guard plus end-to-end sample','next_if_fail':'preserve outputs, do not deploy by default'})
    print({'cases':len(inputs),'unique_images':len(views),'views':len(views)*4,'planned_calls':82},flush=True)

def run(root,resume=False):
    root=Path(root);views=read_json(root/'view_manifest.json')
    stages={'control':SafeStage(VisualStage()),'multiview':SafeStage(MultiViewStage(view_records=views))}
    inputs=read_jsonl(root/'inputs.jsonl');by_id={r['case_id']:r for r in inputs};order=read_json(root/'order.json')
    files=[root/n for n in ('protocol.json','inputs.jsonl','references.jsonl','order.json','view_manifest.json')]
    files += [Path('analysis_skeleton/prompts/verify.txt'),Path('analysis_skeleton/shots/verify.jsonl')]
    files += [r['input']['image_path'] for r in inputs]+[r['input']['image_path'] for r in stages['control'].source.shots]
    files += [v['image_path'] for record in views.values() for v in record['views']]
    code=[__file__,Path(__file__).parent/'views.py','analysis_skeleton/framework_v2/runtime.py','analysis_skeleton/llm.py','analysis_skeleton/m5_verify.py']
    identity={'stages':{k:v.identity for k,v in stages.items()},'order':order,'fresh':True,'replicate_id':'r1'}
    out=root/'run'
    if resume:
        manifest=check_frozen(out)
        if manifest['config']!=identity:raise ValueError('identity_changed')
    else:new_run(out,'visual_localization_v1',files,identity,code);manifest=read_json(out/'manifest.json')
    with output_lock(out):
        cp=Checkpoints(out/'checkpoints',digest(manifest),cache_mode='fresh');results=[]
        for i,(cid,condition) in enumerate(order):
            check_frozen(out);r=by_id[cid]
            v=cp.call(cid+':'+condition,stages[condition],r['input'],validate_label)
            record={k:r[k] for k in ('case_id','image_id','semantic_type')}
            record.update(condition=condition,status=v['status'],prediction=v.get('value',{}),audit=v.get('audit',{}))
            results.append(record);write_jsonl(out/'results.jsonl',results)
            print(f"{i+1}/82 {cid} {condition}: {record['prediction'].get('label',v['status'])}",flush=True)
            if i==0 and v['status']!='complete':raise RuntimeError('first_call_failed')
        invocation={'new_api_calls':cp.new_api_calls,'resumed':cp.resumed,'results':len(results),'status':dict(Counter(r['status'] for r in results))}
        write_json(root/('resume_metrics.json' if resume else 'call_metrics.json'),invocation)

def report(root):
    root=Path(root);check_frozen(root/'run')
    rr=read_jsonl(root/'run/results.jsonl');refs={r['case_id']:r for r in read_jsonl(root/'references.jsonl')};metrics={}
    for condition in ('control','multiview'):
        rows=[{**r,'reference_label':refs[r['case_id']]['reference_label']} for r in rr if r['condition']==condition]
        m=score_labels(rows);m.update(correct=sum(r['prediction'].get('label')==r['reference_label'] for r in rows),planned_cases=41)
        m['agreement']=m['correct']/41;m['passes90']=len(rows)==41 and m['correct']>=37
        m['confident_errors']=sum(r['prediction'].get('label') in ('supported','hallucinated') and r['prediction']['label']!=r['reference_label'] for r in rows)
        m['usage']={key:sum((r['audit'].get('usage') or {}).get(key,0) or 0 for r in rows) for key in ('prompt_tokens','completion_tokens','total_tokens')}
        m['elapsed_seconds_sum']=sum(r['audit'].get('elapsed_seconds',0) for r in rows)
        metrics[condition]=m
    paired=[]
    for cid in refs:
        group={r['condition']:r for r in rr if r['case_id']==cid}
        if len(group)!=2:continue
        a,b=group['control'],group['multiview'];gold=refs[cid]['reference_label']
        assert query_payload('verify',a['audit']['input'])==query_payload('verify',b['audit']['input'])
        paired.append({'case_id':cid,'image_id':a['image_id'],'statement':a['audit']['input']['statement'],'reference':gold,'control':a['prediction'].get('label'),'multiview':b['prediction'].get('label'),'control_reason':a['prediction'].get('reason'),'multiview_reason':b['prediction'].get('reason'),'improved':a['prediction'].get('label')!=gold and b['prediction'].get('label')==gold,'regressed':a['prediction'].get('label')==gold and b['prediction'].get('label')!=gold})
    metrics['paired']={k:sum(r[k] for r in paired) for k in ('improved','regressed')}
    metrics['engineering']={'all_82_complete':len(rr)==82 and all(r['status']=='complete' for r in rr),'unique_responses':len({r['audit'].get('response_id') for r in rr})==82,'all_fresh':all(r['audit'].get('api_calls')==1 and not r['audit'].get('cache_hit') for r in rr),'all_requested_returned_models_match':all(r['audit']['identity']['model']==r['audit'].get('response_model') for r in rr),'semantic_query_inputs_same':len(paired)==41}
    metrics['accept_candidate']=metrics['multiview']['passes90'] and metrics['multiview']['correct']>metrics['control']['correct'] and metrics['multiview']['confident_errors']<=metrics['control']['confident_errors'] and all(metrics['engineering'].values())
    write_json(root/'metrics.json',metrics);write_jsonl(root/'paired.jsonl',paired)
    lines=['# 原图与固定局部视图：实体视觉测试','', '固定41条实体命题，原提示和原6-shot；每图保留原图并附四个60%边长、重叠的原像素视图。区域不依赖标签或人工主体框。','', '| 条件 | 正确/41 | 一致率 | Macro-F1 | 错误确定判断 | 输入tokens |','|---|---:|---:|---:|---:|---:|']
    for c in ('control','multiview'):
        m=metrics[c];lines.append(f"| {c} | {m['correct']} | {m['agreement']:.2%} | {m['macro_f1']:.2%} | {m['confident_errors']} | {m['usage']['prompt_tokens']} |")
    lines += ['',f"成对修复{metrics['paired']['improved']}条，回退{metrics['paired']['regressed']}条；候选是否通过本轮预设门槛：{metrics['accept_candidate']}。",'','## 发生变化的样本','']
    for r in paired:
        if r['control']!=r['multiview']:lines += [f"- {r['case_id']}：参考{r['reference']}；{r['control']} → {r['multiview']}。原理由：{r['control_reason']}；局部视图理由：{r['multiview_reason']}"]
    lines += ['','## 范围','', '- 旧开发图上的候选参考一致率，不是新图泛化或人工gold准确率。原标签未修改。','- 输入视图改变，不能把不同条件当相同query的随机重复。模型调用均为fresh；无投票、重试、额外裁判。','- 5项局部模块测试覆盖像素一致、几何、全图覆盖、重用和few-shot/原query不变。','- 判断增加局部视图能否帮助识别，不等于实现了实例级自动定位。','- 未修改主框架默认行为。属性和端到端迁移结论尚未在本条件下验证。']
    (root/'RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(metrics,ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['prepare','run','report']);p.add_argument('--output',required=True);p.add_argument('--resume',action='store_true');a=p.parse_args()
    if a.phase=='prepare':prepare(a.output)
    elif a.phase=='run':run(a.output,a.resume)
    else:report(a.output)
