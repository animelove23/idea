"""Read-only result aggregation. Does not revise prompts, candidates, predictions or scores."""
import argparse
import json
from pathlib import Path
from .common import read_json,read_jsonl,new_run,check_frozen,write_json,report
from .contracts import normalize_document,SLOTS
from .metrics import prf
from .m5_verify import score_labels


def execute(root):
    root=Path(root)
    runs=['m0_resolved','m1','m2_online','m3_online','m5_online']
    for run in runs:check_frozen(root/run)
    inputs=[root/run/'metrics.json' for run in runs]
    inputs += [root/run/'results.jsonl' for run in ('m2_online','m3_online','m5_online')]
    cases_path=Path('analysis_skeleton/fixtures/decompose_pilot.jsonl');inputs.append(cases_path)
    out=new_run(root/'audit','read_only_run_summary',inputs,{'llm_calls':0},[__file__])
    m2=read_jsonl(root/'m2_online/results.jsonl');m3=read_jsonl(root/'m3_online/results.jsonl');m5=read_jsonl(root/'m5_online/results.jsonl')
    refs={c['case_id']:normalize_document(c['reference'],c['text'],c['case_id']) for c in read_jsonl(cases_path)}
    slots={}
    for slot in sorted(SLOTS):
        n=sum(sum(f['slot']==slot for f in r['document']['facts']) for r in m2)
        fp=sum(sum(f['slot']==slot for f in r['score']['unmatched_prediction']) for r in m2)
        g=sum(sum(f['slot']==slot for f in refs[r['case_id']]['facts']) for r in m2)
        slots[slot]=prf(n-fp,n,g)
    statuses={}
    for status in ('retained','removed','added','modified','unresolved'):
        records=[r['score']['by_status'][status] for r in m3]
        statuses[status]=prf(**{k:sum(x[k] for x in records) for k in ('tp','predicted','reference')})
    def api_summary(records):
        return {'calls':len(records),'returned_models':sorted({r['audit'].get('response_model','unknown') for r in records}),
                'total_tokens':sum((r['audit'].get('usage') or {}).get('total_tokens',0) for r in records),
                'sum_call_seconds':sum(r['audit'].get('elapsed_seconds',0) for r in records)}
    metrics={'frozen_runs_checked':runs,'m2_by_attribute_slot':slots,'m3_by_status':statuses,
             'm5_by_semantic_type':{s:score_labels([r for r in m5 if r['semantic_type']==s]) for s in ('entity','attribute')},
             'api_usage':{'m2':api_summary(m2),'m3':api_summary(m3),'m5':api_summary(m5)},
             'independent_repeats':1,'human_gold':False,'llm_calls_in_this_audit':0}
    report(out,'冻结结果复核与分项指标',metrics,['只读取已落盘结果；没有补调用、改参考或重跑语义模型。',
        '本轮每条输入仅一次生成，不能报告独立重复稳定性。计数只反映候选符合度，尚未覆盖完整计划中的人工审计指标。'])
    write_json(out/'m2_disagreements.json',[{'case_id':r['case_id'],'text':r['document']['text'],
                'unmatched_prediction':r['score']['unmatched_prediction'],'unmatched_reference':r['score']['unmatched_reference']}
                for r in m2 if r['score']['unmatched_prediction'] or r['score']['unmatched_reference']])
    (out/'M2_DISAGREEMENT.md').write_text('''# M2 唯一候选参考分歧

样本：397351_steer。原句片段：`appears to be selling these vegetables at a market`。

DeepSeek输出market实体，并将整段放入action排除项；候选参考将market置于推测作用域内，未收入肯定实体。

这是范围判断/参考边界待审，不能仅凭字符串分数断定真实场景中是否存在market。当前参考明确排除推测命题，因此本轮照冻结答案计为1个额外实体；不事后修改分数。

尚需审核：appears的作用域是否包含地点存在；实体vegetables与其carrots/radishes子类的重叠提及是否符合所需信息计数。后者在模型和候选参考中一致，因此F1不会揭露协议自身的潜在重复计数问题。

原始响应、候选参考和评分均保留。下一轮若更改范围规则或示例，必须独立命名实验，不覆盖本轮。
''',encoding='utf-8')
    review=['# Few-shot与候选参考审核入口','','当前全部为助手起草候选，**没有冒充人工gold**。每例完整输入、输出均保存在下方；不在此文件修改运行过的JSONL。','',
            '审核结论请另存：example_id/case_id、accept或reject、理由、修订版本；未审核条目保持pending。', '']
    boundaries={
       'decompose':['只声明实体存在，不补属性','small和red分别计size/color','wooden计material，不另造wood实体','round与made of wood分slot；词性不决定类别',
                    'open计state；beside排除','wet计state；running不计state','数量、评价、动作排除；群体不虚构多个个体','重复红色只计一次；推测和否定不当肯定颜色'],
       'align':['完整等义材质保留','属性缺失removed','属性新出现added','同主体同槽变值modified','跨槽remove+add','主体退出与属性省略区分',
                '身份不能确定时unresolved','对侧原文已表达但输入事实缺失时extraction_gap'],
       'verify':['实体supported','实体hallucinated','实体uncertain','属性supported','属性hallucinated','属性uncertain']}
    for stage in ('decompose','align','verify'):
        review += [f'## {stage}：固定示例','']
        for i,ex in enumerate(read_jsonl(f'analysis_skeleton/shots/{stage}.jsonl')):
            review += [f'### {ex["example_id"]} — {boundaries[stage][i]}','','人工审核：pending。','']
            if stage=='verify':review += [f'![原图]({Path(ex["input"]["image_path"]).resolve().as_posix()})','']
            review += ['```json',json.dumps(ex,ensure_ascii=False,indent=2),'```','']
    review += ['## 固定测评候选参考','','示例与下面测评输入分开。M3只称开发最小对照，不称改写族隔离的held-out测试。','']
    for filename in ('decompose_pilot','align_cases','verify_cases'):
        for c in read_jsonl(f'analysis_skeleton/fixtures/{filename}.jsonl'):
            review += [f'### {filename} / {c["case_id"]}','','人工审核：pending。','']
            if filename=='verify_cases':review += [f'![原图]({Path(c["input"]["image_path"]).resolve().as_posix()})','']
            review += ['```json',json.dumps(c,ensure_ascii=False,indent=2),'```','']
    (out/'EXAMPLE_REVIEW.md').write_text('\n'.join(review),encoding='utf-8')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',default='outputs/skeleton_v1');a=p.parse_args();execute(a.root)
