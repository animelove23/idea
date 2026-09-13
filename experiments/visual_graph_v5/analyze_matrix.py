"""Offline descriptive analysis of the frozen conservative v5 output."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np

from experiments.entity_attribute_v3.retention import analyze as retention_analysis

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'outputs/visual_graph_v5/entity_graph_attribute_frozen'
OUT = ROOT / 'outputs/visual_graph_v5/analysis'
STATES = ['lost', 'unchanged', 'gained', 'mixed']
LABELS = {'lost': '仅减少', 'unchanged': '不变', 'gained': '仅增加', 'mixed': '有增有减', 'unresolved': '未确定'}
COLORS = {'lost': '#df7767', 'unchanged': '#86a8b7', 'gained': '#62ad98', 'mixed': '#aa8abf', 'unresolved': '#d4d7dd'}


def save_json(name, obj):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')


def save_csv(name, rows):
    if not rows:
        return
    with (OUT / name).open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)


def savefig(fig, name):
    fig.savefig(OUT / f'{name}.png', dpi=180, bbox_inches='tight', facecolor='white')
    fig.savefig(OUT / f'{name}.pdf', bbox_inches='tight', facecolor='white')
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    font = Path('C:/Windows/Fonts/msyh.ttc')
    font_manager.fontManager.addfont(str(font))
    plt.rcParams.update({'font.family': font_manager.FontProperties(fname=str(font)).get_name(), 'axes.unicode_minus': False, 'font.size': 11, 'pdf.fonttype': 42})
    raw = (SOURCE / 'pairs.jsonl').read_bytes()
    records = [json.loads(line) for line in raw.decode('utf-8').splitlines()]
    obs = [r['observation'] for r in records]
    assert len(records) == len({r['pair_id'] for r in records}) == 400
    short = [o for o in obs if o['length_group'] == 'shorter']
    key = [o for o in short if o['matrix_classifiable'] and o['hallucination_change'] == 'unchanged' and o['supported_change'] == 'mixed']
    matrices = {}
    for length in ['shorter', 'unchanged', 'longer']:
        group = [o for o in obs if o['length_group'] == length]
        counts = Counter((o['hallucination_change'], o['supported_change']) for o in group if o['matrix_classifiable'])
        matrices[length] = {'total': len(group), 'classified': sum(counts.values()), 'unresolved': len(group)-sum(counts.values()), 'cells': [[counts[h, s] for s in STATES] for h in STATES]}
    with (SOURCE / 'matrix.csv').open(encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            assert matrices[row['length_group']]['cells'][STATES.index(row['H'])][STATES.index(row['S'])] == int(row['count'])
    assert sum(m['classified'] for m in matrices.values()) == 322
    fig, ax = plt.subplots(figsize=(10, 7))
    a = np.array(matrices['shorter']['cells'])
    ax.imshow(a, cmap='Blues', vmin=0, vmax=100)
    for i in range(4):
        for j in range(4):
            ax.text(j, i, f'{a[i,j]} 对\n{a[i,j]/len(short):.1%}', ha='center', va='center', fontsize=16, color='white' if a[i,j] > 65 else '#172b40')
    ax.set(xticks=range(4), yticks=range(4), xticklabels=[LABELS[x] for x in STATES], yticklabels=[LABELS[x] for x in STATES], xlabel='支持信息 S 的命题集合变化', ylabel='幻觉 H 的命题集合变化')
    ax.set_title('输出缩短后的语义变化矩阵', fontsize=19, pad=40)
    ax.text(.5, 1.025, f'缩短 {len(short)} 对 · 确定 {a.sum()} 对 · 未确定 {len(short)-a.sum()} 对；每格比例均以 395 为分母', transform=ax.transAxes, ha='center', fontsize=11)
    fig.text(.12, .015, '“有增有减”表示旧命题损失且新命题出现，不能解读为净增加或新物体出现。\n自动分析标签；80.5% 是矩阵覆盖率，不是准确率。', fontsize=10, color='#536172')
    fig.subplots_adjust(bottom=.16)
    savefig(fig, '01_shorter_matrix')

    comp_keys = ['entity_S', 'attribute_S', 'entity_H', 'attribute_H']
    names = ['支持实体', '支持属性', '幻觉实体', '幻觉属性']
    components = {k: dict(Counter(o['component_states'][k][0] if len(o['component_states'][k]) == 1 else 'unresolved' for o in obs)) for k in comp_keys}
    fig, ax = plt.subplots(figsize=(12, 4.6))
    left = np.zeros(4)
    for s in ['lost', 'unchanged', 'gained', 'mixed', 'unresolved']:
        vals = np.array([components[k].get(s, 0) for k in comp_keys])
        ax.barh(names, vals, left=left, label=LABELS[s], color=COLORS[s], height=.62)
        for i, v in enumerate(vals):
            if v >= 19: ax.text(left[i]+v/2, i, str(v), ha='center', va='center', fontsize=11)
        left += vals
    ax.invert_yaxis(); ax.set_xlim(0, 400); ax.set_xlabel('样本对数（每行分母均为全部 400 对）')
    ax.set_title('实体与属性：分别判断变化，不因整对未确定而丢弃可用成分', pad=20)
    ax.legend(ncol=5, loc='upper center', bbox_to_anchor=(.5, -.18), frameon=False)
    savefig(fig, '02_component_states')

    retention, attr_rows, pair_retention, entity_rows = retention_analysis(records)
    assert retention['conditional_attribute_retention']['denominator'] == len(attr_rows)
    save_json('retention.json', retention)
    save_csv('conditional_attributes.csv', attr_rows)
    save_csv('entity_identity_retention.csv', entity_rows)
    save_csv('per_pair_retention.csv', pair_retention)
    slots = ['color', 'material', 'size', 'shape', 'state']
    slot_names = ['颜色', '材质', '大小', '形状', '状态']
    fig, ax = plt.subplots(figsize=(12, 5.5))
    left = np.zeros(5)
    for status, label, color in [('retained', '保留', '#62ad98'), ('removed', '删除', '#df7767'), ('modified', '改写原属性', '#aa8abf'), ('unresolved', '未确定', '#d4d7dd')]:
        ns = np.array([retention['by_slot'][s]['denominator'] for s in slots])
        counts = np.array([retention['by_slot'][s][status] for s in slots])
        vals = counts / ns * 100
        ax.barh([f'{n}（n={nn}）' for n, nn in zip(slot_names, ns)], vals, left=left, color=color, label=label, height=.62)
        for i, v in enumerate(vals):
            if v > 9: ax.text(left[i]+v/2, i, f'{counts[i]} / {v:.0f}%', ha='center', va='center', fontsize=10)
        left += vals
    ax.set_xlim(0, 100); ax.invert_yaxis(); ax.set_xlabel('占各属性分母的比例（%）')
    ax.set_title('主体保留后，原来支持的属性去了哪里？', fontsize=18, pad=30)
    ax.text(.5, 1.025, '分母：314 条原支持属性；前后主体均受支持且身份对齐。形状、状态样本很少。', transform=ax.transAxes, ha='center', fontsize=10)
    ax.legend(ncol=4, loc='upper center', bbox_to_anchor=(.5, -.17), frameon=False)
    savefig(fig, '03_conditional_attributes')

    pos = []
    all_pos = set().union(*(o['pos_original'] for o in obs), *(o['pos_steer'] for o in obs))
    original_words = sum(o['original_words'] for o in obs)
    steer_words = sum(o['steer_words'] for o in obs)
    for tag in all_pos:
        before = sum(o['pos_original'].get(tag, 0) for o in obs)
        after = sum(o['pos_steer'].get(tag, 0) for o in obs)
        pos.append({'POS': tag, 'original': before, 'steer': after, 'net_reduction': before-after, 'within_pos_reduction': (before-after)/before if before else None, 'share_of_word_reduction': (before-after)/(original_words-steer_words)})
    pos.sort(key=lambda x: x['net_reduction'], reverse=True)
    assert sum(x['original'] for x in pos) == original_words
    assert sum(x['steer'] for x in pos) == steer_words
    save_csv('pos.csv', pos)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.4))
    p = pos[:10]
    axes[0].barh([x['POS'] for x in p], [x['net_reduction'] for x in p], color='#668caa')
    axes[0].invert_yaxis(); axes[0].set_title('哪些词类贡献了净缩短？'); axes[0].set_xlabel('全 400 对净减少词数（前十词类）')
    axes[1].hist([o['word_reduction']*100 for o in obs], bins=22, color='#76afa0', edgecolor='white')
    axes[1].axvline(np.median([o['word_reduction']*100 for o in obs]), color='#bd5a50', linestyle='--', label='样本中位数')
    axes[1].set_title('每对输出的长度减少比例'); axes[1].set_xlabel('（原词数 − steer 词数）/ 原词数，%'); axes[1].set_ylabel('样本对数'); axes[1].legend(frameon=False)
    fig.suptitle(f'总词数 {original_words:,} → {steer_words:,}；净减少 {1-steer_words/original_words:.1%}', fontsize=17)
    fig.text(.09, .01, '词数由项目 NLP 分词统计；POS 只描述表面表达，不能把形容词减少直接等同于真实属性丢失。', fontsize=10)
    fig.tight_layout(rect=(0, .055, 1, .93)); savefig(fig, '04_length_pos')

    sums = {k: {f: sum(c.get(f, 0) for o in obs for c in o['components'] if c['type']+'_'+c['role'] == k) for f in ['original_count', 'steer_count', 'retained', 'loss', 'gain', 'removed', 'added', 'modified_out', 'modified_in', 'possible_loss', 'possible_gain']} for k in comp_keys}
    for counts in sums.values():
        assert counts['loss'] == counts['removed'] + counts['modified_out']
        assert counts['gain'] == counts['added'] + counts['modified_in']
    for counts in components.values():
        assert sum(counts.values()) == 400
    key_transition = Counter()
    key_ids = {o['pair_id'] for o in key}
    for r in records:
        if r['pair_id'] in key_ids:
            transitions = {e.get('description_change') for e in r['bundle']['alignment']['entities']}
            for name in ['generalized', 'specialized']:
                if name in transitions: key_transition[name] += 1
    motif = {
        'H_unchanged_S_mixed_shorter': {'n': len(key), 'subtypes': dict(Counter(o['hallucination_unchanged_subtype'] for o in key)), 'description_transition_pair_counts_overlapping': dict(key_transition)},
        'H_unchanged_shorter_joint_decided': sum(o['matrix_classifiable'] and o['hallucination_change']=='unchanged' for o in short),
        'H_unchanged_shorter_H_axis_decided': sum(o['hallucination_change']=='unchanged' for o in short),
        'H_lost_without_supported_loss_shorter': sum(o['matrix_classifiable'] and o['hallucination_change']=='lost' and o['supported_change'] in ['unchanged', 'gained'] for o in short),
        'supported_mixed_shorter_joint_decided': sum(o['matrix_classifiable'] and o['supported_change']=='mixed' for o in short),
        'H_gain_present_shorter_joint_decided': sum(o['matrix_classifiable'] and o['hallucination_change'] in ['gained','mixed'] for o in short),
    }
    pair_rows = []
    for o in obs:
        pair_rows.append({k: o[k] for k in ['pair_id', 'original_words', 'steer_words', 'word_reduction', 'length_group', 'matrix_classifiable', 'supported_change', 'hallucination_change', 'hallucination_unchanged_subtype']})
    save_csv('pair_metrics.csv', pair_rows)
    save_csv('matrix.csv', [{'length_group': length, 'H': h, 'S': s, 'count': m['cells'][i][j], 'full_group_denominator': m['total'], 'full_group_fraction': m['cells'][i][j]/m['total']} for length, m in matrices.items() for i,h in enumerate(STATES) for j,s in enumerate(STATES)])
    metric = {'source': str(SOURCE / 'pairs.jsonl'), 'source_sha256': hashlib.sha256(raw).hexdigest(), 'pairs': len(records), 'matrix_classifiable': 322, 'coverage': 322/400, 'semantic_accuracy_measured': False, 'new_llm_calls': 0, 'matrices': matrices, 'components': components, 'component_event_totals': sums, 'motifs': motif, 'word_counts': {'original': original_words, 'steer': steer_words, 'pooled_reduction': 1-steer_words/original_words, 'mean_pair_reduction': float(np.mean([o['word_reduction'] for o in obs])), 'median_pair_reduction': float(np.median([o['word_reduction'] for o in obs]))}, 'repeat_mention_proxy': {side:sum(o['repeat_mention_proxy'][side] for o in obs) for side in ['original', 'steer']}, 'cohort_word_reduction': {name:{'n':len(g),'mean':float(np.mean([o['word_reduction'] for o in g]))} for name,g in [('classified',[o for o in obs if o['matrix_classifiable']]),('unresolved',[o for o in obs if not o['matrix_classifiable']])]}, 'limitations': ['automatic development labels, not independent human gold', 'mixed is proposition turnover, including specificity changes; not necessarily different physical objects', '314 conditional attributes are not all image attributes', 'no causal control or token-level attribution']}
    save_json('metrics.json', metric)
    cases = []
    for pid in ['281331', '276066', '438426', '38438']:
        r = next(r for r in records if r['pair_id'] == pid)
        cases.append({'pair_id':pid, 'original':r['bundle']['original']['text'], 'steer':r['bundle']['steer']['text'], 'observation':r['observation'], 'entity_alignment':r['bundle']['alignment']['entities'], 'changes':[e for e in r['events'] if e.get('action') in ['loss','gain']], 'image_path':r['bundle']['image_path']})
    save_json('case_examples.json', cases)
    print(json.dumps(metric, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
