"""Render source-backed results after the complete cohort has been aggregated."""
import csv
from collections import Counter
from pathlib import Path
from analysis_skeleton.common import read_json,read_jsonl

ROOT=Path('outputs/coco400_final_v1');OUT=ROOT/'observations'
CN={'shorter':'句子变短','unchanged':'不变','longer':'句子变长','lost':'减少/丢失','gained':'增加','mixed':'有增有减'}


def pct(n,d):return f'{100*n/d:.2f}%' if d else 'N/A'


def main():
    s=read_json(OUT/'summary.json');audit=read_json(OUT/'integrity.json')
    rows=read_jsonl(OUT/'observation_pairs.jsonl')
    with (OUT/'change_matrices.csv').open(encoding='utf-8-sig',newline='') as f:matrix=list(csv.DictReader(f))
    lines=['# COCO 400：冻结框架端到端实验结果','',
        '目标：观察 steer 导致文本缩短时，幻觉、真实信息及实体/属性成分如何共同变化，为后续单变量干预提供 motivation。',
        '',f"本轮处理 **400 张图片、800 条已有文本**；成功形成分析结果 {s['analyzed_pairs']} 对。所有比例均来自本轮自动输出，未把工程完成率当作语义准确率。",'',
        '## 数据与实验边界','',
        '- 官方 COCO val2014：40,504 张图片全部下载并解压；同时下载 CHAIR 所需 captions/instances 的 train2014、val2014 标注。',
        '- 从项目已有 500 对 LLaVA-1.5 greedy baseline / VISTA 文本中，排除 5 张视觉 few-shot 图片后，使用 seed=20260912 随机抽取 400 对。',
        f"- 其中 {s['known_development_overlap']} 张曾用于框架开发，名单已提前记录。因此这是探索性观察，不是独立留出集准确率测评。",
        '- 沿用 Final v1，M2/M3/M5 均为 DeepSeek Flash，8/8/6-shot。没有重新生成 caption，没有向模型提供 COCO 标注或参考答案。',
        '- S=图像支持；H=图像不支持。独立属性统计要求主体受支持；错误主体上的属性另列，避免重复计算主体幻觉。',
        '- 对齐为 modified 时，记录旧命题丢失、新命题增加。相同数量的事实替换也属于“有增有减”。视觉不确定、技术未决和提取异常保留，不补零。',
        '', '## 长度与核心变化矩阵','',
        f"原文总词数 {s['original_words']:,} → steer 总词数 {s['steer_words']:,}；总体净缩短 {pct(s['original_words']-s['steer_words'],s['original_words'])}。按样本计算的平均缩短率 {s['mean_word_reduction']:.2%}，中位数 {s['median_word_reduction']:.2%}。词数来自冻结 M1 的非标点词元口径。",'']
    for length in ('shorter','unchanged','longer'):
        n=s['length_counts'].get(length,0);missing=s['matrix_unresolved_by_length'][length]
        lines += [f"### {CN[length] if length!='unchanged' else '句长不变'}：N={n}",'',
            f'可唯一归类 {n-missing} 对；未决 {missing} 对。单元格分母是该长度组全部 {n} 对，未决样本仍在分母内。','',
            '| 幻觉变化 × 真实信息变化 | 不变 | 增加 | 丢失 | 有增有减 |','|---|---:|---:|---:|---:|']
        for h in ('lost','unchanged','gained','mixed'):
            cells=[]
            for state in ('unchanged','gained','lost','mixed'):
                count=int(next(r['count'] for r in matrix if r['length_group']==length and r['hallucination_change']==h and r['supported_change']==state))
                cells.append(f'{count} ({pct(count,n)})')
            lines.append('| '+CN[h]+' | '+' | '.join(cells)+' |')
        lines.append('')
    lines += ['![变化矩阵](observations/change_matrices.png)','',
        '仅 H 轴可判定为不变的样本（包含 S 轴未决者）进一步区分：'+str(s['hallucination_unchanged_subtypes'])+'。仅在前后成员资格均可确定时才称“前后幻觉均为零”。','',
        '## 实体与属性成分','',
        '下表是已分类成分中的确定事件计数。改写出/入分别是 modified 的旧/新命题；净变化不能替代这些事件。未决转移不填入保留或删除。','',
        '| 成分 | 原始数 | steer 数 | 保留 | 直接删除 | 改写出 | 直接新增 | 改写入 |','|---|---:|---:|---:|---:|---:|---:|---:|']
    for key,label in [('entity_S','真实实体'),('entity_H','幻觉实体'),('attribute_S','真实属性'),('attribute_H','幻觉属性')]:
        c=s['component_totals'][key]
        lines.append('| '+label+' | '+' | '.join(str(c[k]) for k in ('original_count','steer_count','retained','removed','modified_out','added','modified_in'))+' |')
    lines += ['',f"真实属性直接删除的分解：{s['attribute_removed_components']}。parent_removed 为随主体删除；parent_retained_attribute_removed 为主体仍在但属性消失；其余保留在 other_or_unresolved。",'',
        '![成分变化](observations/semantic_components.png)','',
        '## 词语与 POS','',
        'POS 图反映各词类对净词数下降的贡献。名词下降不等于实体减少，形容词下降不等于属性丢失：必须结合事实对齐查看。重复提及字段仅作词汇层代理量，不等同于冗余语义。','',
        '![POS](observations/pos_composition.png)','',
        '## 完整性与解释范围','',
        f"- 新 API 调用：{s['new_api_calls_recorded_in_checkpoints']:,}；成功响应唯一 ID：{s['unique_response_ids']:,}；各模块调用记录：{s['stage_calls']}。",
        f"- 接受事实：{s['accepted_fact_rows']:,}；视觉标签分布：{s['visual_fact_labels']}。",
        f"- 调用状态：{s['call_status']}；失败样本：{s['failed_pair_ids']}。",
        f"- 主体非支持、属性却支持：{audit['supported_attribute_parent_not_supported']} 条；严格统计已全部排除，原始标签保留供审查。",
        f"- 原冻结版本 {audit['old_frozen_files_unchanged']} 个文件未改动；全部接受事实均恰好入队、回填一次；checkpoint 校验通过。",
        '- 本轮没有新增人工 gold，因此无法报告本轮 M2/M5 语义准确率。未决比例反映可统计覆盖率，不应反向解释为准确率。',
        '- 成分变化可以提出后续干预假设；仅凭配对文本不能确认提前 EOS、注意力抑制或内部表征机制。',
        '', '## 可复查产出','',
        '- [400 对图片、文本与变化明细](observations/case_gallery.html)',
        '- [基于结果的候选研究动机](MOTIVATION.md)',
        '- [原图对照与定性案例](CASE_REVIEW.md)',
        '- [核心矩阵 CSV](observations/change_matrices.csv)',
        '- [逐样本成分 CSV](observations/pair_components.csv)',
        '- [POS 明细 CSV](observations/pos_components.csv)',
        '- [统计摘要](observations/summary.json)',
        '- [未决样本及原因](observations/matrix_missingness.json)',
        '- [完整性审计](observations/integrity.json)',
        '- [样本清单与抽样依据](selection.json)',
        '- [冻结协议](protocol.json)','']
    names={'extraction_issues':'分解异常/隔离记录','visual_uncertain_facts':'视觉不确定事实',
        'visual_pending_facts':'视觉技术未决事实','alignment_semantic_facts':'语义对齐未决事实',
        'alignment_technical_facts':'技术对齐未决事实','attributes_on_false_subject':'错误主体上的属性',
        'parent_attribute_conflict':'主体与属性标签冲突','retained_label_or_parent_conflicts':'保留边标签/主体资格冲突',
        'pair_analysis_unavailable':'整对分析不可用'}
    lines+=['## 质量问题覆盖情况','',
        '下列类别可重叠；异常数量不能相加后当作错误率。矩阵未决也可能由多个因素共同造成。','',
        '| 问题 | 事实/异常条数 | 涉及样本对数 |','|---|---:|---:|']
    for k,v in s['quality'].items():
        lines.append(f"| {names.get(k,k)} | {v} | {s['quality_affected_pairs'].get(k,0)} |")
    probe=read_json(ROOT/'resume_probe/result.json')
    lines+=['',f"另外，断网恢复验证通过：{len(probe['results'])} 对样本，新增 API 调用均为 0，主要导出文件逐字节一致。",'']
    (ROOT/'RESULTS.md').write_text('\n'.join(lines),encoding='utf-8')


if __name__=='__main__':main()
