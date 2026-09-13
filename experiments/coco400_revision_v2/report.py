"""Final paired-condition audit. Coverage improvements are never reported as accuracy."""
import json
from collections import Counter
from pathlib import Path
from analysis_skeleton.common import read_json,read_jsonl,write_json,write_jsonl,sha,check_frozen,digest

ROOT=Path('outputs/coco400_revision_v2_guard');SOURCE=Path('outputs/coco400_final_v1')


def main():
    old=read_json(SOURCE/'observations/summary.json');conditions=['A_scope_only','B_alignment','B2_local_and_rebinding','C_reviewed']
    summaries={n:read_json(ROOT/n/'summary.json') for n in conditions}
    records=read_jsonl(ROOT/'C_reviewed/pairs.jsonl');assert len(records)==400
    rows=[r['observation'] for r in records];ledgers=[l for r in records for l in r['ledger']]
    for r in records:
        expected={(s,f['id']) for s in ('original','steer') for f in r['bundle'][s]['facts']}
        refs=[(x['side'],x['fact_id']) for q in r['queue'] for x in q['refs']]
        actual=[(x['side'],x['fact_id']) for x in r['ledger']]
        assert len(refs)==len(set(refs))==len(actual)==len(expected) and set(refs)==set(actual)==expected
        assert {q['claim_id'] for q in r['queue']}=={v['claim_id'] for v in r['verification']}
    assert len(ledgers)==5959
    release=read_json('outputs/final_v1_release/release_manifest.json')
    assert all(sha(p)==h for p,h in release['files'].items())
    response_ids=[];api=0;started=0;checkpoints=0
    call_roots=[Path('outputs/coco400_revision_v2/probe_calls'),Path('outputs/coco400_revision_v2/align_calls'),
        ROOT/'probe_calls',ROOT/'align_calls',ROOT/'review_rebound_calls']
    for base in call_roots:
        check_frozen(base)
        for p in (base/'checkpoints').glob('*.json'):
            x=read_json(p);assert x['checksum']==digest(x['value']);checkpoints+=1
            value=x['value'];a=value.get('audit',{})
            if p.name.endswith('_response.json'):
                response_ids.append(a['response_id']);assert a['response_model']=='deepseek-flash'
            else:
                api+=a.get('api_calls',0);started+=value.get('status')=='started'
    assert len(response_ids)==len(set(response_ids))
    transitions=read_jsonl(ROOT/'C_reviewed/review_transitions.jsonl')
    counters=Counter((x['purpose'],x['before'],x['after']) for x in transitions)
    rawalignment=Counter(l['alignment_axis'] for l in ledgers)
    examples=[r for r in rows if r['length_group']=='shorter' and r['hallucination_change']=='unchanged' and r['supported_change']=='mixed']
    summary={'conditions':summaries,'accepted_facts':len(ledgers),'raw_new_alignment':dict(rawalignment),
        'old_raw_alignment':{'semantic_unresolved':655,'technical_unresolved':111},
        'review_transitions':[{'purpose':a,'before':b,'after':c,'count':n} for (a,b,c),n in sorted(counters.items())],
        'motivation_cell':len(examples),'motivation_cell_subtypes':dict(Counter(r['hallucination_unchanged_subtype'] for r in examples)),
        'confirmed_recorded_new_api_calls':api,'aborted_started_outcome_unknown':started,
        'unique_new_response_ids':len(response_ids),'checksummed_checkpoints':checkpoints,
        'old_framework_files_unchanged':len(release['files']),'semantic_accuracy_measured':False,
        'm3_technical_regression_present':rawalignment['technical_unresolved']>111,
        'release_status':'tested_candidate_not_accuracy_validated'}
    write_json(ROOT/'comparison.json',summary);write_jsonl(ROOT/'C_reviewed/denominator_ledger.jsonl',ledgers)
    lines=['# 框架修改与分步复测','',
        '本次为独立候选版本，原冻结框架和 COCO 400 原结果不覆盖。M2 与 800 条分解输出保持不变，分别测量统计、M3 和 M5 的变化。',
        '', '## 修改内容','',
        '- 统计：排除项记录错误、超出既定语义范围的 state、无原文支持的状态推断，不再直接封锁整对；可能缺失的有效属性按属主/槽位处理。缺失实体仍保守处理。每个 entity/attribute × S/H 成分单独输出状态。',
        '- M3：先判主体身份，再记录等价、泛化、具体化；部分/整体和集合身份不清仍未决。泛化/具体化以 description_changed 输入、modified 事件导出，同时保留 description_change，不能称为完全等价或新增独立物体。',
        '- M3 合同：仅隔离互相矛盾的行和依赖项，不根据某张表猜另一张表应有的答案。',
        '- M5：原图始终保留，可附无增强的局部裁剪；候选区域不作为已验证定位。二轮不展示首轮标签或理由，一次复核后停止；确定标签发生冲突时退回 uncertain。主体非支持的属性继续排除在严格真实属性统计之外。',
        '- 旧共享视觉请求因新对齐而失效时，保留原查询主体自身的标签，给另一侧建立独立命题；不把一个主体的标签复制给另一个主体。',
        '', '## 同一 400 对的分步结果','',
        '| 条件 | 完整矩阵可归类 | 未决 |','|---|---:|---:|','| 原冻结结果 | 187 / 400 (46.75%) | 213 |']
    labels={'A_scope_only':'A：仅修统计传播','B_alignment':'B：新 M3 原始合同结果','B2_local_and_rebinding':'B2：局部隔离 + 安全重绑，尚未补视觉','C_reviewed':'C：一次定向视觉复核完成'}
    for n,s in summaries.items():lines.append(f"| {labels[n]} | {s['matrix_classifiable']} / 400 ({s['matrix_classifiable']/4:.2f}%) | {s['matrix_unresolved']} |")
    lines+=['','B/B2 阶段降低覆盖的一个原因是旧共享视觉结论不再适用，因此先保留未决，再在 C 阶段独立核验。不能跳过这部分直接沿用旧标签。','',
        '## 模块指标与尚存问题','',
        '- 离线合同/统计测试 27 项通过；新端到端入口的断网集成与零新增调用恢复测试 1 项通过。',
        '- M3 合成边界回归：第一次 7/8，发现把位置冲突主体误合并；只加强身份证据冲突提示后同一组 8/8。该组已用于开发，不是独立留出集。',
        '- M3 正式请求 400 次：393 条通过原新增合同，7 条存在局部冲突；保存响应经局部隔离后保留其他合法行，无新增请求。',
        '- M3 原始账本语义未决事实 655 → 349；但技术未决事实 **111 → 214，出现回归**。主要仍是重复 ID、未决主体下的增删声明和一对多形状冲突。不能声称 M3 准确率提高，不能把技术未决重新命名成语义未决来掩盖问题。',
        '- 统计摘要中的技术未决 279 还包含统计层追加的 M2 依赖隔离；与 M3 原始 214 条分开解释。',
        '- M5 请求 506 次，506 条通过合同：418 条二轮复核（含相关主体），88 条新主体绑定。330 条原视觉 uncertain 中，74 条转 supported、43 条转 hallucinated、213 条仍 uncertain。另有 7 条原已确定结论与复核冲突，合并后保留 uncertain。',
        '- 88 条新绑定：82 supported、2 hallucinated、4 uncertain。以上仅为自动判定变化，未测量转换后的真实准确率。',
        '', '## 核心观察','',
        f"你关心的“句子变短、幻觉不变、真实信息有增有减”现在有 **{len(examples)} 对**；细分为 {summary['motivation_cell_subtypes']}。原来是 47 对，但合同已增加描述泛化/具体化事件，因此不能把新增数量全部解释为找到更多真实内容变化。",
        '- 新版识别到 63 条泛化、37 条具体化实体描述事件，单独记录，供后续核查具体程度变化。',
        '- 确定直接删除的真实属性：主体保留 136 条，随主体删除 67 条，其他/未决归属 11 条。',
        '- 未决仍有 131 对；当下重点仍是检查 M3 的多主体和集合示例及已确定结果的质量，不能只以更高覆盖率作为验收标准。',
        '', '## 调用与完整性','',
        f'- 有审计计数的新调用 {api} 次；另有 {started} 个在停止首个候选实验时留下的启动检查点，远端结果未知。它们未自动重发，不混入正式结果。',
        f'- {checkpoints} 个检查点校验通过；{len(response_ids)} 个成功保存的响应 ID 唯一。',
        f'- 原框架 {len(release["files"])} 个冻结文件未变；5,959 条接受事实在最终队列、账本中恰好出现一次。',
        '', '## 文件与使用','',
        '- [机器比较表](comparison.json)',
        '- [最终矩阵 CSV](C_reviewed/matrix.csv)',
        '- [最终矩阵图](C_reviewed/observations/change_matrices.png)',
        '- [最终 400 对图片与文本审查](C_reviewed/observations/case_gallery.html)',
        '- [最终逐样本数据](C_reviewed/pairs.jsonl)',
        '- [最终逐事实账本](C_reviewed/denominator_ledger.jsonl)',
        '- [二轮逐命题变化](C_reviewed/review_transitions.jsonl)',
        '', '新样本入口：','',
        '```powershell',
        '.venv/Scripts/python.exe -m experiments.coco400_revision_v2.end_to_end --pairs <配对输入.jsonl> --output <新的输出目录>',
        '```','',
        '该入口只运行一次原 M2、新 M3、首轮 M5，再对符合条件的命题审查一次。恢复时增加 --resume。默认仍使用 Flash 和原 Final v1 profile；原始结果保存在 first_pass，复核单独保存。此版本为待语义准确率验收的候选，不替换原默认入口。','']
    (ROOT/'RESULTS.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k!='conditions'},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
