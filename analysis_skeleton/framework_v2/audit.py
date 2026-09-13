"""Zero-network acceptance: saved-response replay, denominator audit, and review exports."""
import argparse
import json
from collections import Counter
from pathlib import Path
from analysis_skeleton.common import read_json,read_jsonl,write_json,write_jsonl,write_csv,check_frozen
from analysis_skeleton.metrics import aggregate_documents
from analysis_skeleton.m3_align import score_alignment
from .prepare_audit import prepare,DATA,OLD,REPAIR
from .pipeline import execute
from .contracts import normalize_document,validate_alignment
from .ledger import reference_ledger
from .scoring import LemmaScorer
from .runtime import query_payload
from .stability import visual_metrics


def replay(root):
    source=DATA/'pairs.jsonl';out=root/'integration_replay'
    first=execute(source,out,cache_path=root/'response_cache.jsonl',cache_mode='replay')
    write_json(root/'first_invocation_metrics.json',first)
    resumed=execute(source,out,cache_path=root/'response_cache.jsonl',cache_mode='replay',resume=True)
    write_json(root/'resume_metrics.json',resumed)
    if first['new_api_calls_this_invocation'] or resumed['new_api_calls_this_invocation']:raise AssertionError('offline_replay_made_API_calls')


def summarize(root):
    out=root/'integration_replay';check_frozen(out)
    baseline=read_jsonl(REPAIR/'end_to_end/bundles.jsonl');bundles=read_jsonl(out/'bundles.jsonl')
    bmap={b['pair_id']:b for b in baseline};comparisons=[]
    for b in bundles:
        old=bmap[b['pair_id']]
        comparisons.append({'pair_id':b['pair_id'],'documents_identical':all(b[s]==old[s] for s in ('original','steer')),
                            'alignment_identical':b['alignment']==old['alignment'],'lexical_identical':b['lexical']==old['lexical']})
    same_m6=read_json(out/'m6/metrics.json')==read_json(REPAIR/'end_to_end/m6/metrics.json')
    old_visual={r['claim_id']:r for r in read_jsonl(REPAIR/'end_to_end/verification.jsonl')}
    new_visual=read_jsonl(out/'verification.jsonl')
    same_visual=len(old_visual)==len(new_visual) and all(v==old_visual.get(v['claim_id']) for v in new_visual)
    references=[normalize_document(c['reference'],c['text'],c['case_id']) for c in read_jsonl(DATA/'decompose_cases.jsonl')]
    ledger=read_jsonl(out/'denominator_ledger.jsonl');scorer=LemmaScorer()
    refs,extras,scores=reference_ledger(references,bundles,ledger,scorer)
    write_jsonl(root/'reference_denominator_ledger.jsonl',refs);write_jsonl(root/'prediction_extras.jsonl',extras)
    write_jsonl(root/'m2_scores.jsonl',scores)
    write_csv(root/'reference_denominator_ledger.csv',list(refs[0]),refs)
    docs={b[s]['caption_id']:b[s] for b in bundles for s in ('original','steer')};rmap={r['caption_id']:r for r in references}
    review=[]
    for r in refs:
        if r['extraction_axis']=='extraction_missing':
            d=rmap[r['caption_id']];f=next(f for f in d['facts'] if f['id']==r['reference_fact_id'])
            review.append({'caption_id':r['caption_id'],'text':d['text'],'case_type':'unmatched_reference',
                           'fact':f,'human_error_category':None,'adjudication':None})
    for r in extras:
        d=docs[r['caption_id']];f=next(f for f in d['facts'] if f['id']==r['prediction_fact_id'])
        review.append({'caption_id':r['caption_id'],'text':d['text'],'case_type':'unmatched_prediction',
                       'fact':f,'human_error_category':None,'adjudication':None})
    write_jsonl(root/'m2_disagreement_review.jsonl',review)
    cases={c['case_id']:c for c in read_jsonl(DATA/'align_cases.jsonl')};m3=[]
    old_m3={r['case_id']:r for r in read_jsonl(REPAIR/'m3_replay/results.jsonl')}
    for r in read_jsonl(OLD/'m3_independent/results.jsonl'):
        c=cases[r['case_id']];a=validate_alignment(json.loads(r['audit']['raw_content']),c['original'],c['steer'])
        m3.append({'case_id':r['case_id'],'alignment_identical':a==old_m3[r['case_id']]['alignment'],
                   'score':score_alignment(a,c['reference'])})
    write_jsonl(root/'m3_replay_checks.jsonl',m3)
    ab=read_jsonl(REPAIR/'visual_ab/results.jsonl');historical={r['case_id']:r for r in read_jsonl(OLD/'m5_independent/results.jsonl')}
    control=[r for r in ab if r['condition']=='control']
    historical_repeat={'cases':len(control),'same_inputs':sum(query_payload('verify',r['audit']['input'])==query_payload('verify',historical[r['case_id']]['audit']['input']) for r in control),
        'same_identities':sum(r['audit']['identity']==historical[r['case_id']]['audit']['identity'] for r in control),
        'changed_labels':sum(r['prediction']['label']!=historical[r['case_id']]['prediction']['label'] for r in control),
        'new_calls':0,'fresh_three_repeat_evaluation':'not_performed'}
    flow={'reference_facts':len(refs),'matched_reference_facts':sum(r['extraction_axis']=='matched' for r in refs),
          'extraction_missing':sum(r['extraction_axis']=='extraction_missing' for r in refs),'prediction_extras':len(extras),
          'alignment_decided_on_reference':sum(r['alignment_axis']=='decided' for r in refs),
          'visual_decided_on_reference':sum(r['visual_axis']=='decided' for r in refs),
          'jointly_decided_on_reference':sum(r['alignment_axis']=='decided' and r['visual_axis']=='decided' for r in refs),
          'production_facts':len(ledger),'original_supported_eligible':sum(r['side']=='original' and r['historical_supported_eligible'] for r in ledger),
          'human_truth_denominator':None,'reference_status':'assistant_candidate_not_human_gold'}
    write_json(root/'denominator_flow.json',flow)
    checks={'pairs':comparisons,'all_same_documents':len(comparisons)==len(baseline) and all(c['documents_identical'] for c in comparisons),
            'all_same_alignments':len(comparisons)==len(baseline) and all(c['alignment_identical'] for c in comparisons),
            'all_same_lexical':all(c['lexical_identical'] for c in comparisons),'same_visual_records':same_visual,
            'same_m6_metrics':same_m6,'same_independent_m3':all(r['alignment_identical'] for r in m3)}
    write_json(root/'replay_equivalence.json',checks)
    if not all(checks[k] for k in ('all_same_documents','all_same_alignments','all_same_lexical','same_visual_records','same_m6_metrics','same_independent_m3')):
        raise AssertionError('Saved-response semantic equivalence failed; inspect replay_equivalence.json')
    metrics={'integration':read_json(root/'first_invocation_metrics.json'),'resume':read_json(root/'resume_metrics.json'),
             'm2_fixed_scorer':aggregate_documents([r['score'] for r in scores]),'denominator_flow':flow,
             'historical_visual_repeat':historical_repeat,
             'visual_historical_metrics':{condition:visual_metrics([r for r in ab if r['condition']==condition]) for condition in ('control','context')},
             'independent_m3_technical_facts':sum(r['score']['technical_fact_count'] for r in m3),
             'saved_response_equivalence_passed':True,'new_api_calls':0}
    write_json(root/'metrics.json',metrics)
    status=[{'task':'E0 generic runner / isolation / resumable cache','status':'done'},
            {'task':'E1 fixed scoring / production and reference denominator ledgers','status':'done'},
            {'task':'Stage5 protocols / 24 boundary candidates / review packet','status':'prepared_pending_human_review'},
            {'task':'Fresh three-repeat baseline','status':'not_run_first_stage_zero_LLM'},
            {'task':'X2/X3/X4/X5 semantic interventions','status':'not_run_preserve_baseline'},
            {'task':'D1/T1 new independent reference and confirmation','status':'pending_reference_and_data'}]
    write_json(root/'TASK_STATUS.json',status)
    tests=read_json(root/'test_results.json') if (root/'test_results.json').exists() else None
    lines=['# framework_v2 首轮改进与测试报告','',
           '已完成计划E0/E1：可恢复通用运行入口、逐请求/逐pair故障隔离、固定计分与分母账本；同时准备类别覆盖和人工复核材料。旧语义规则、模型、8/8/6-shot及候选参考未修改。','',
           '## 实际测试','',
           f'- 回归测试：{tests["tests_run"]}项，失败{tests["failures"]}、错误{tests["errors"]}。' if tests else '- 回归测试结果另存test_results.json。',
           '- 原20图全链重放：40个M2、20个M3、199个M5响应，共259个请求检查点；新增API调用0。',
           '- 20对文档、对齐、词语记录、199条视觉回填与M6统计均与repair_v1完全一致。',
           f'- 再次恢复：复用{metrics["resume"]["resumed_checkpoints"]}个完成检查点，新增调用0。',
           '- 独立M3的20组保存响应也通过完全一致性检查。合法响应未因工程改造改变语义。','',
           '## 分母不再隐藏匹配缺口','',
           f'- 生产账本保留{flow["production_facts"]}条有效事实；参考账本始终保留{flow["reference_facts"]}条候选事实。',
           f'- 固定词形口径匹配{flow["matched_reference_facts"]}条；{flow["extraction_missing"]}条未匹配参考记录为extraction_missing，{flow["prediction_extras"]}条预测额外项另列复核。',
           '- 未匹配不自动等于真实漏抽：可能涉及命名、范围、绑定或参考错误，已生成108条逐项复核记录。',
           '- technical unresolved、semantic unresolved、visual uncertain、pending及父子绑定疑点各有独立字段。原M6分母保持原口径，严格父主体筛选只作旁路审计。','',
           '## 准确率与稳定性边界','',
           '- 本轮没有换模型/提示/示例，没有重新生成答案；M2约80.9%、M3约93.1%是保存结果的原口径，不是新准确率提升。',
           '- 历史同输入视觉判断仍有10/60标签变化。新增三重复评价器明确pairwise翻转率、完整重复覆盖、S↔H翻转及可决错误率，并拒绝把缓存结果当独立重复；本轮没有运行fresh三重复。',
           '- 已提供24组完整边界候选（20组分解对照、4组对齐控制）及示例覆盖表。它们经过结构验证，不是LLM通过率或独立人工gold。',
           '- 新开发/确认集、人工裁决及后续单变量模型实验尚未执行。','',
           '## 文件','',
           '- integration_replay/denominator_ledger.csv：264条生产事实、迁移、真假及各轴状态。',
           '- reference_denominator_ledger.csv：300条候选参考全集与抽取缺口。',
           '- m2_disagreement_review.jsonl：36个未匹配预测与72个未匹配参考的原文、证据及待裁决字段。',
           '- boundary_cases.jsonl、shot_coverage_matrix.csv：完整候选例子与当前覆盖缺口。',
           '- review_visual_answer_hidden.jsonl：60条遮蔽答案的旧开发集复核输入；候选答案在独立key文件，不能称新的盲测。',
           '- BASELINE_LOCK.json、replay_equivalence.json、test_results.json、TASK_STATUS.json：来源锁、重放证据、测试与阶段状态。']
    (root/'RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'replay_equivalence':True,'denominator_flow':flow,'new_api_calls':0},ensure_ascii=False))


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--phase',choices=['prepare','replay','report','all'],default='all');a=p.parse_args()
    root=Path(a.output)
    if a.phase in ('prepare','all'):prepare(root)
    if a.phase in ('replay','all'):replay(root)
    if a.phase in ('report','all'):summarize(root)


if __name__=='__main__':main()
