"""Fresh 30-pair run with reviewed reference; old predictions rescored identically."""
import argparse
import json
from pathlib import Path

from decomposition.storage import digest, write_json, write_jsonl
from . import reference_experiment as experiment
from .fewshot_experiment import read_lines
from .reference_metrics import compute

OUT = Path('outputs/alignment_reference30_v2')
REF = Path('outputs/alignment_reference30_v1/user_review_20260912_v2/reference.jsonl')


def freeze():
    experiment.OUT = OUT
    experiment.freeze()
    reference = read_lines(REF)
    write_jsonl(OUT / 'reference.jsonl', reference)
    manifest = json.loads((OUT / 'manifest.json').read_text(encoding='utf-8'))
    manifest.update(reference_digest=digest(reference), reference_source=str(REF),
                    existing_decomposer='not executed; fixed assistant-authored facts identical to prior test',
                    comparison='old and new predictions evaluated against the same revised reference; development rerun, not held-out evaluation')
    manifest['files'][str(REF)] = digest(REF.read_text(encoding='utf-8'))
    dest = OUT / 'frozen' / REF
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(REF.read_bytes())
    write_json(OUT / 'manifest.json', manifest)


def compare():
    reference = read_lines(OUT / 'reference.jsonl')
    runs = {
        'original_live_rescored': Path('outputs/alignment_reference30_v1/alignment.jsonl'),
        'v12_offline_replay_rescored': Path('outputs/alignment_policy_v12/alignment.jsonl'),
        'new_live': OUT / 'alignment.jsonl',
    }
    results = {}
    for name, path in runs.items():
        results[name], _, _ = compute(reference, read_lines(path))
    write_json(OUT / 'comparison.json', results)
    fmt = lambda x: 'N/A' if x is None else f'{x:.2%}'
    lines = ['# 30 对 Alignment 复测对照', '',
             '全部使用同一份修订参考标注：341389 数量事实拆成 added / removed；此前发球阶段等修订继续保留。旧输出只重评分，新输出重新调用模型。', '',
             '| 指标 | 旧在线结果重评分 | v1.2旧响应离线回放 | 本次新在线实验 |',
             '| --- | --- | --- | --- |']
    selectors = [
        ('Edge Precision', lambda m: m['alignment_edge']['precision']),
        ('Edge Recall', lambda m: m['alignment_edge']['recall']),
        ('Edge F1', lambda m: m['alignment_edge']['f1']),
        ('Edge + Status F1', lambda m: m['joint_edge_status']['f1']),
        ('Status Macro-F1', lambda m: m['status_macro_f1']),
        ('Removed Precision', lambda m: m['status_per_class']['removed']['precision']),
        ('确认误删除率 FRR', lambda m: m['false_removal']['rate']),
        ('技术失败事实比例', lambda m: m['technical_failure']['rate']),
    ]
    selectors += [(s + ' F1', lambda m, s=s: m['status_per_class'][s]['f1'])
                  for s in ('retained', 'removed', 'added', 'modified', 'ambiguous')]
    for label, select in selectors:
        lines.append('| ' + ' | '.join([label] + [fmt(select(m)) for m in results.values()]) + ' |')
    lines += ['', '参考主体仍由助手起草，只有部分边界经过用户反馈修订；输入为固定助手标注 facts。本轮属于同一开发集上的规则复测，不能等同于独立人工金标准上的泛化准确率，也未评估 Decomposer/Coverage 或重复稳定性。', '',
              'Edge 包含新增/删除的空端点，按完整事实组匹配；联合 F1 另要求状态正确。Status Macro-F1 按两侧各事实的五类状态计算。FRR 只统计确认在对侧仍完整表达却预测 removed 的原事实，部分保留及不可裁决另列在 TEST_REPORT.md。']
    (OUT / 'COMPARISON.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['freeze', 'run', 'report'])
    args = parser.parse_args()
    experiment.OUT = OUT
    if args.mode == 'freeze':
        freeze()
    else:
        if args.mode == 'run':
            experiment.run()
        else:
            experiment.report()
        compare()
