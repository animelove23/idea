"""Versioned 30-pair live run, four substantive statuses plus audited exclusion."""
import argparse
import json
from collections import Counter
from pathlib import Path

from decomposition.storage import digest, write_json, write_jsonl
from . import reference_experiment as runner
from .alignment_core import PairAligner, fallback_alignments
from .core_metrics import score, legacy_predictions
from .fewshot_experiment import read_lines

OUT=Path('outputs/alignment_core_v13/experiment_v1')
SOURCE=Path('annotation/alignment_v13')
OLD=Path('outputs/alignment_reference30_v2_online')


def configure():
    runner.OUT=OUT;runner.SOURCE=SOURCE
    runner.PairAligner=PairAligner;runner.fallback_alignments=fallback_alignments
    runner.report=report


def freeze():
    configure();runner.freeze()
    manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
    texts={p[s]['text'].strip().casefold() for p in read_lines(OUT/'pairs.jsonl') for s in ('original','steer')}
    for name in ('entities','alignment_core'):
        examples=read_lines(Path(f'evaluation/examples/{name}.jsonl'))
        assert len(examples)==8
        assert not texts & {e['input'][s]['text'].strip().casefold() for e in examples for s in ('original','steer')}
    manifest.update(alignment_protocol='core-change-v1.3',active_alignment_examples='evaluation/examples/alignment_core.jsonl',
                    reference_policy='assistant re-adjudication under new taxonomy, not wholly human reviewed',
                    existing_decomposer='not executed; same fixed assistant-authored facts as prior 30-pair experiment',
                    scoring_policy='four core classes plus full five-class/exclusion reporting; model exclusion never removes core gold from recall denominator')
    write_json(OUT/'manifest.json',manifest)


def report():
    gold=read_lines(OUT/'reference.jsonl')
    predictions=[json.loads(p.read_text(encoding='utf-8')) for p in sorted((OUT/'alignments').glob('*.json'))]
    metrics,errors,frr=score(gold,predictions)
    stages={s:[json.loads(p.read_text(encoding='utf-8')) for p in (OUT/s).glob('*.json')] for s in ('entities','alignments')}
    calls=0;responses=0;usage=Counter()
    for records in stages.values():
        for item in records:
            audit=item.get('audit',{});calls+=audit.get('api_calls',0)
            if audit.get('usage'):
                responses+=1;usage.update({k:v for k,v in audit['usage'].items() if type(v)==int})
    metrics.update(complete=len(predictions)==len(gold),api_calls=calls,responses_with_usage=responses,usage=dict(usage),
                   stage_status={s:dict(Counter(x['status'] for x in xs)) for s,xs in stages.items()})
    write_json(OUT/'metrics.json',metrics);write_jsonl(OUT/'alignment.jsonl',predictions)
    write_jsonl(OUT/'errors.jsonl',errors);write_jsonl(OUT/'false_removal_audit.jsonl',frr)
    previous,_,_=score(gold,legacy_predictions(read_lines(OLD/'alignment.jsonl')))
    write_json(OUT/'comparison.json',{'previous_live_reclassified':previous,'new_live':metrics})
    fmt=lambda x:'N/A' if x is None else f'{x:.2%}'
    lines=['# v1.3 对齐复测', '', f"完成 {len(predictions)}/30 对，API 调用 {calls}/60，模型响应 {responses}。DeepSeek 思考关闭，8-shot；同一固定 caption/facts，未运行 Decomposer 或 Coverage。", '',
           '旧在线预测仅把 ambiguous 改名为 other，未按新参考修正模型结论。两组均使用本轮冻结的新参考和同一计分函数。', '',
           '| 指标 | 旧在线结果（新口径重评分） | 新在线结果 |','| --- | --- | --- |']
    measures=[('主线 Edge Precision',lambda m:m['core_edge']['precision']),('主线 Edge Recall',lambda m:m['core_edge']['recall']),
              ('主线 Edge F1',lambda m:m['core_edge']['f1']),('主线 Edge + Status F1',lambda m:m['core_joint']['f1']),
              ('主线四类 Status Macro-F1',lambda m:m['core_status_macro_f1']),
              ('全量五类 Edge F1',lambda m:m['alignment_edge']['f1']),('全量五类 Status Macro-F1',lambda m:m['status_macro_f1']),
              ('Removed Precision',lambda m:m['status_per_class']['removed']['precision']),
              ('确认 FRR',lambda m:m['false_removal']['rate']),('技术失败事实比例',lambda m:m['technical_failure']['rate']),
              ('全部 other 排除率（含技术失败）',lambda m:m['exclusions']['predicted_other_rate']),
              ('参考可判定事实的错误排除率',lambda m:m['exclusions']['false_exclusion_rate_on_reference_core'])]
    for name,fn in measures:lines.append('| '+' | '.join([name,fmt(fn(previous)),fmt(fn(metrics))])+' |')
    lines += ['', '| 状态 | 参考事实数 | 预测事实数（不含技术失败） | Precision | Recall | F1 |', '| --- | --- | --- | --- | --- | --- |']
    for s,v in metrics['status_per_class'].items():
        lines.append('| '+' | '.join([s,str(v['reference']),str(v['predicted']),*[fmt(v[k]) for k in ('precision','recall','f1')]])+' |')
    x=metrics['exclusions'];fr=metrics['false_removal']
    lines += ['',f"参考 other {x['reference_other']}/{metrics['facts']}；预测排除 {x['predicted_other']}，其中语义 other {x['semantic_other']}、技术失败 {x['technical_other']}。参考可判定 {x['reference_core']} 条，其中错误排除 {x['false_exclusions']} 条。",'',
              f"确认误删除 {fr['confirmed_false']}/{fr['predicted_removed']}；部分保留 {fr['partial_overlap']}，无法裁决 {fr['uncertain']}。把部分/无法裁决均算误删的上界 {fmt(fr['upper_bound'])}。",'',
              '主线指标不把 other 当作语义变化，但模型对参考主线事实的 other/失败仍计漏报；对参考 other 的主线预测仍计误报。因此排除不能自动抬高分数。全量五类同时呈现，技术失败不获 other 正确分。', '',
              '参考由助手按新协议逐项修订，尚未经用户全面审核。30对都是此前参与规则开发的样本；这是开发复测，不是独立泛化测试。一次运行不构成重复稳定性结论。modified 扩大后与此前窄定义分数不可直接比；本表旧结果也已统一新定义。']
    (OUT/'TEST_REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


def audit():
    manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
    pairs=read_lines(OUT/'pairs.jsonl');gold=read_lines(OUT/'reference.jsonl');pred=read_lines(OUT/'alignment.jsonl')
    assert len(pairs)==len(gold)==len(pred)==30
    assert digest(pairs)==manifest['pairs_digest'] and digest(gold)==manifest['reference_digest']
    for name,h in manifest['files'].items():
        assert digest(Path(name).read_text(encoding='utf-8'))==h,name
        assert digest((OUT/'frozen'/name).read_text(encoding='utf-8'))==h,name
    pm={x['pair_id']:x for x in pred};gm={x['pair_id']:x for x in gold}
    lines=['# 30 对原文、修订参考与实际输出','']
    for p in pairs:
        for side in ('original','steer'):
            assert Counter(f['id'] for f in p[side]['facts'])==Counter(fid for r in pm[p['pair_id']]['fact_alignment'] for fid in r[side+'_fact_ids'])
        lines += ['## '+p['pair_id'],'','**Original**','',p['original']['text'],'','**Steer**','',p['steer']['text'],'']
        for label,rows in [('新参考',gm[p['pair_id']]['fact_alignment']),('实际输出',pm[p['pair_id']]['fact_alignment'])]:
            lines += ['### '+label,'','| Original fact | Steer fact | 状态 | 原因 |','| --- | --- | --- | --- |']
            for r in rows:
                columns=[]
                for side in ('original','steer'):
                    fs={f['id']:f['fact'] for f in p[side]['facts']}
                    columns.append('<br>'.join(fid+': '+fs[fid] for fid in r[side+'_fact_ids']) or '∅')
                lines.append('| '+' | '.join(c.replace('|','\\|') for c in columns+[r['status'],r['reason']])+' |')
            lines+=['']
    calls=0
    for stage in ('entities','alignments'):
        for path in (OUT/stage).glob('*.json'):
            a=json.loads(path.read_text(encoding='utf-8')).get('audit',{})
            calls+=a.get('api_calls',0)
            if a.get('api_calls'):
                body=a['request'];assert body['thinking']=={'type':'disabled'} and body['temperature']==0
                assert len(body['messages'])==18
                payload=json.loads(body['messages'][-1]['content'])
                assert not {'gold','reference','fact_alignment'} & set(payload)
    assert calls<=60
    (OUT/'CAPTIONS_RESULTS.md').write_text('\n'.join(lines),encoding='utf-8')
    write_json(OUT/'integrity_checks.json',dict(passed=True,pairs=30,api_calls=calls,thinking_disabled=True,
               frozen_code_and_inputs_unchanged=True,reference_not_sent=True,primary_membership_once=True))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['freeze','run','report']);args=parser.parse_args()
    configure()
    if args.mode=='freeze':freeze()
    else:
        if args.mode=='run':runner.run()
        else:report()
        audit()
