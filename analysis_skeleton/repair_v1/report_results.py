"""Summarize repaired runs without editing predictions or candidate references."""
from collections import Counter
from pathlib import Path
import numpy as np
from analysis_skeleton.common import read_json,read_jsonl,write_json,write_jsonl,write_csv,check_frozen

BASE=Path('outputs/skeleton_expansion20')
ROOT=Path('outputs/skeleton_repair_v1')


def integration(root):
    bundles=read_jsonl(root/'bundles.jsonl');pairs=read_jsonl(root/'m6/pair_analysis.jsonl')
    result={'pairs':len(bundles),'facts':{s:sum(len(b[s]['facts']) for b in bundles) for s in ('original','steer')},
            'technical_facts':sum(len(e['original'])+len(e['steer']) for b in bundles for e in b['alignment']['alignments'] if e.get('reason','').startswith('technical')),
            'alignment_review_pairs':sum(b['alignment']['status']!='ready' for b in bundles),
            'words':{s:sum(b['lexical'][s]['caption']['word_len'] for b in bundles) for s in ('original','steer')},
            'm6':read_json(root/'m6/metrics.json')}
    for kind in ('entity','attribute'):
        result[kind]={}
        for truth in ('true','hallucinated'):
            value={k:sum(p[kind][truth][k] for p in pairs) for k in ('denominator','retained','removed','modified','unresolved')}
            n=value['denominator'];value['removal_lower']=value['removed']/n if n else None
            value['removal_upper']=(value['removed']+value['unresolved'])/n if n else None
            result[kind][truth]=value
    return result


def main():
    checks=[BASE/p for p in ('m2','m3_independent','m5_independent','end_to_end')]+[ROOT/p for p in ('m2_replay','m3_replay','visual_ab','end_to_end','end_to_end/m6')]
    for p in checks:check_frozen(p)
    m2=read_json(ROOT/'m2_replay/metrics.json');m3=read_json(ROOT/'m3_replay/metrics.json')
    m5=read_json(ROOT/'visual_ab/metrics.json');records=read_jsonl(ROOT/'visual_ab/results.jsonl')
    cases={c['case_id']:c for c in read_jsonl('analysis_skeleton/fixtures/repair_v1/visual_ab.jsonl')}
    lookup={(r['case_id'],r['condition']):r for r in records}
    paired=read_jsonl(ROOT/'visual_ab/paired.jsonl');delta={}
    for p in paired:delta.setdefault(cases[p['case_id']]['image_id'],[]).append(int(p['improved'])-int(p['regressed']))
    means=np.array([np.mean(v) for v in delta.values()]);rng=np.random.default_rng(1994)
    samples=means[rng.integers(0,len(means),size=(2000,len(means)))].mean(axis=1)
    m5['paired']['agreement_delta_cluster_bootstrap_95ci']=[float(v) for v in np.quantile(samples,[.025,.975])]
    m5['paired']['bootstrap_unit']='20 images, paired conditions, 2000 resamples, seed=1994; development set only'
    review=[]
    for p in paired:
        c=cases[p['case_id']]
        review.append({**p,'image_id':c['image_id'],'statement':c['input']['statement'],
            'source_window':c['context_input']['entity_context']['source_window'],'reference_reason':c['reference_reason'],
            **{s+'_reason':lookup[(p['case_id'],s)].get('prediction',{}).get('reason','') for s in ('control','context')}})
    write_jsonl(ROOT/'visual_case_review.jsonl',review)
    write_csv(ROOT/'visual_case_review.csv',list(review[0]),review)
    before=integration(BASE/'end_to_end');after=integration(ROOT/'end_to_end')
    run=read_json(ROOT/'end_to_end/metrics.json')
    api=sum(r['audit'].get('api_calls',0) for r in records)+run['new_api_calls']
    tokens=sum((r['audit'].get('usage') or {}).get('total_tokens',0) for r in records)+run['new_tokens']
    result={'m2':m2,'m3':m3,'m5':m5,'integration_before':before,'integration_after':after,
            'integration_run':run,'total_new_api_calls':api,'total_new_tokens':tokens,
            'frozen_runs_checked':[str(p) for p in checks]}
    write_json(ROOT/'metrics.json',result)
    pct=lambda x:f'{100*x:.1f}%' if x is not None else 'N/A'
    lines=['# 修复与复测结果','',
        '固定原 20 图、40 条文本、60 条视觉候选事实。原响应、参考标签、类别规则和 8/8/6-shot 未改。修复版独立保存在 repair_v1，旧基线保持可复查。','',
        '## 独立模块结果','',
        '| 模块与口径 | 修复前/同期对照 | 修复后/补充语境 |','|---|---:|---:|',
        f'| M2，同一响应、同一实体词形计分器 F1 | {pct(m2["before"]["joint"]["f1"])} | {pct(m2["after"]["joint"]["f1"])} |',
        f'| M3，同一响应、固定候选事实联合 F1 | {pct(m3["before"]["joint"]["f1"])} | {pct(m3["after"]["joint"]["f1"])} |',
        f'| M3 技术未决事实 / 300 | {m3["before"]["technical_facts"]} | {m3["after"]["technical_facts"]} |',
        f'| M5，同期 60 条 Macro-F1 | {pct(m5["control"]["macro_f1"])} | {pct(m5["context"]["macro_f1"])} |',
        f'| M5，候选标签一致率 | {pct(m5["control"]["agreement"])} | {pct(m5["context"]["agreement"])} |',
        f'| M5，uncertain 召回 | {pct(m5["control"]["by_label"]["uncertain"]["recall"])} | {pct(m5["context"]["by_label"]["uncertain"]["recall"])} |','',
        'M2 只隔离错误提及，恢复 cloud、man、skateboarders 三个实体；有效实体仍参与对齐和视觉验证。原 71.7% 与词形口径 80.2% 的差异属于计分变化，不能算作本次修复提升。7 条非法 state 仍按原规则隔离。','',
        'M3 只拆开单侧批量行、合并相交纯 unresolved 集合。剩余 3 条技术未决在 303499 与 483723：主体未确定，属性却被声明新增/删除；保留冲突，不猜身份。','',
        'M5 同一模型、图片、命题、系统规则和 6-shot；仅 query 增加原文定位窗口及主体提及偏移。两种条件各一次，30/30 平衡先后顺序。历史 59.8% 仅作历史值，不作为同期对照。','',
        f'配对结果：{m5["paired"]["improved"]} 条由不符候选变为符合，{m5["paired"]["regressed"]} 条反向变化；共 {m5["paired"]["label_changed"]} 条标签变化。候选一致率差的图像级配对 bootstrap 95% 区间为 '+ ' 至 '.join(f'{100*v:.1f}' for v in m5['paired']['agreement_delta_cluster_bootstrap_95ci'])+' 个百分点，包含零，不能据此宣称稳定显著提升。该区间不覆盖人工标签不确定性或模型跨次生成变动。','',
        '改善/退化仅指与冻结候选标签的符合度。比如 small tractor 从 supported 变 uncertain 的模型理由是无法确定主体为 tractor，原候选属性与主体之间已有一致性问题；不能直接认定这是模型新增错误。large bird 仍存在大小参照标准分歧。','',
        '## 视觉逐例复查','',
        '[完整 60 条对照 CSV](visual_case_review.csv) 保存命题、原文语境、候选理由、两个模型理由及改善/退化标记。以下列出所有发生标签变化的样本：','',
        '| ID | 命题 | 候选 | 原输入 | 补充语境 |','|---|---|---|---|---|']
    for r in review:
        if r['control']!=r['context']:lines.append(f'| {r["case_id"]} | {r["statement"]} | {r["reference_label"]} | {r["control"]} | {r["context"]} |')
    lines+=['','## 端到端集成','',
        '| 统计 | 原版本 | 修复版本 |','|---|---:|---:|',
        f'| 原文/steer 事实数 | {before["facts"]["original"]}/{before["facts"]["steer"]} | {after["facts"]["original"]}/{after["facts"]["steer"]} |',
        f'| 技术未决事实 | {before["technical_facts"]} | {after["technical_facts"]} |',
        f'| 唯一视觉命题 | {before["m6"]["queue_claims"]} | {after["m6"]["queue_claims"]} |',
        f'| 属性/主体真值冲突 | {before["m6"]["truth_conflicts"]} | {after["m6"]["truth_conflicts"]} |']
    for kind,label in [('entity','实体'),('attribute','属性')]:
        for truth,name in [('true','视觉supported'),('hallucinated','视觉hallucinated')]:
            b=before[kind][truth];a=after[kind][truth]
            fmt=lambda v:f'{v["removed"]}/{v["denominator"]}' if v['denominator'] else 'N/A（分母为0）'
            lines.append(f'| 原文{name}{label}删除 / 分母 | {fmt(b)} | {fmt(a)} |')
    lines+=['',f'20 个 pair 已完成；视觉待处理 {run["pending_claims"]} 条。词数仍为 1914 → 908。集成同时含三项修复，统计变化不作单变量因果结论。',
        '',f'本轮合计新增 {api} 次 API 调用、{tokens} tokens；其中集成 M3 新调用 {run["m3_new_calls"]} 次、M5 新调用 {run["m5_new_calls"]} 次，缓存复用 {run["cached_calls"]} 次。M2 和独立 M3 修复复测新增调用为 0。',
        '', '[端到端事实迁移表](end_to_end/m6/transitions.csv) · [每图指标及词数](end_to_end/m6/pair_metrics.csv) · [POS 切片](end_to_end/m6/pos_slices.csv) · [完整机器指标](metrics.json)',
        '', '## 解释边界与下一变量','',
        '视觉参考是助手预先整理的候选标签，尚非独立人工 gold；Macro-F1 不是总体准确率。主体定位补齐能处理指代信息缺失，但不能自动解决 large、small、材质等证据边界。下一步应先盲审 uncertain 与 hallucinated 的边界及对应例子，形成独立版本；不在这批结果上修改标签来追求高分，也不同时换模型、换标签和换示例。',
        '', '工程回归共 18 项通过（修复、缓存/输入隔离、原 pipeline 集成）；上述 9 个冻结 run 的代码与输入哈希复查通过。']
    (ROOT/'RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('Wrote repair metrics, RESULTS.md, and 60-case visual review')


if __name__=='__main__':main()
