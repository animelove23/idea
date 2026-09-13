"""Generate a full bad-case gallery and scope-aware evaluation report locally."""
import base64,html,json
from collections import Counter
from pathlib import Path
from analysis_skeleton.common import read_json,read_jsonl,write_json,write_jsonl
from .legacy_visual import report

def main(root):
    root=Path(root);report(root);m=read_json(root/'metrics.json');bad=read_jsonl(root/'bad_cases.jsonl');protocol=read_json(root/'protocol.json')
    summaries=[];cards=[];assets={};esc=html.escape
    for r in bad:
        ref=r['reference'];pred=r['prediction'];cid=r['case_id'];path=ref['input']['image_path'];e=pred.get('evidence',{})
        if path not in assets:assets[path]=base64.b64encode(Path(path).read_bytes()).decode('ascii')
        summaries.append({'case_id':cid,'image_id':r['image_id'],'type':r['semantic_type'],'reference':ref['reference_label'],'prediction':pred.get('label'),'status':r['status'],'statement':ref['input']['statement'],'partition':ref['partition'],'possible_composite_entity_claim':ref['possible_composite_entity_claim'],'visible_cues':pred.get('reason'),'limitation':e.get('limitation'),'candidate_status':e.get('candidate_status')})
        info=esc(json.dumps(e,ensure_ascii=False,indent=2))
        cards.append(f'<article data-kind="{r["semantic_type"]}"><img loading="lazy" src="data:image/jpeg;base64,{assets[path]}"><section><h2>{esc(cid)}</h2><p>{esc(ref["input"]["statement"])}</p><p>旧参考：{ref["reference_label"]}；Flash：{pred.get("label",r["status"])}</p><p>输入语境：{esc(ref["input"]["entity_context"]["source_window"])}</p><p>旧图像复核备注（未发送模型）：{esc(ref["image_review_notes"])}</p><pre>{info}</pre><p>来源：{esc(ref["source_label_file"])}</p></section></article>')
    (root/'BAD_CASES.html').write_text('<!doctype html><html lang="zh"><meta charset="utf-8"><title>完整旧标注Flash复测</title><style>body{font-family:system-ui;max-width:1400px;margin:auto;padding:24px;background:#f3f5fa}article{display:grid;grid-template-columns:45% 1fr;gap:22px;background:white;padding:20px;margin:20px 0}img{width:100%;align-self:start}pre{white-space:pre-wrap;font-size:12px}p{line-height:1.6}button{padding:8px 16px;margin:8px}@media(max-width:800px){article{grid-template-columns:1fr}}</style><h1>旧标注全量复测：全部分歧样本</h1><p>图片为原图；参考标签未经修改。旧完整命题可能含数量、颜色、位置等限定。复核备注只展示给审核者，不曾发给模型。</p><button onclick="filter(\'all\')">全部</button><button onclick="filter(\'entity\')">实体</button><button onclick="filter(\'attribute\')">属性</button>'+''.join(cards)+"<script>function filter(k){document.querySelectorAll('article').forEach(a=>a.style.display=k==='all'||a.dataset.kind===k?'':'none')}</script></html>",encoding='utf-8')
    write_jsonl(root/'bad_case_summary.jsonl',summaries)
    def cell(x):return f'{x["correct"]}/{x["cases"]}（{x["agreement"]*100:.2f}%）'
    lines=['# 旧视觉标注完整复用测评','',
      '本轮实际测试39张COCO图片、579条保留命题，显式请求DeepSeek Flash，使用冻结的evidence_verifier_v2充分性说明和六个图文示例，每条一次。无ROI、无投票、无额外判官。不是按每图抽3条，全部保留命题均进入分母。','',
      '## 数据范围','',
      '旧40图逐事实标注筛选后有635条实体/非数量属性。按当前五种属性槽复核，42条不属于当前范围；与few-shot重合的275717图14条全部排除，因此测试579条（508实体、71属性）。两项排除无重复计数，全部清单在第一次预测前冻结。原标签和原始命题均未改。',
      '旧标签是Codex看图记录，human_reviewed=false；这里报告与旧标签的一致率，不是独立人工gold准确率。实体字段中的数量/颜色/位置限定仍属于旧完整命题，不能把其指标直接称作纯object识别准确率。',
      '', '| 范围 | 实体一致率 | 属性一致率 | 总体一致率 |','|---|---:|---:|---:|']
    for key,title in [('all_retained','全部保留事实'),('previous_20_image_development','此前20图内的16张旧图'),('additional_legacy_images','另外23张旧图')]:
        lines.append('| '+title+' | '+' | '.join(cell(m[key][k]) for k in ('entity','attribute','all'))+' |')
    overall=m['all_retained']
    m['always_supported_baseline']={k:overall[k]['by_label']['supported']['reference']/overall[k]['cases'] for k in ('all','entity','attribute')}
    write_json(root/'metrics.json',m)
    lines += ['',f'实体是否严格超过90%：{m["entity_above_90"]}。整体Macro-F1：{overall["all"]["macro_f1"]*100:.2f}%；实体Macro-F1：{overall["entity"]["macro_f1"]*100:.2f}%；属性Macro-F1：{overall["attribute"]["macro_f1"]*100:.2f}%。',
      f'技术失败：{overall["all"]["technical_failures"]}；实体错误确定判断：{overall["entity"]["confident_errors"]}条。未发现明显限定词的实体诊断子集：{cell(m["unflagged_entity_diagnostic"])}，该规则子集并非人工裁决后的纯实体gold，不替代完整分母。','',
      '## 标签混淆','', '| 原参考 → 模型 | 实体 | 属性 |','|---|---:|---:|']
    for a in ('supported','hallucinated','uncertain'):
        for b in ('supported','hallucinated','uncertain'):
            if a==b:continue
            lines.append(f'| {a} → {b} | '+ ' | '.join(str(sum(x['reference']==a and x['prediction']==b and x['type']==k for x in summaries)) for k in ('entity','attribute'))+' |')
    lines += ['', '## 类别不平衡与指标解释','',
      f'若所有事实一律回答supported，总体也有{100*m["always_supported_baseline"]["all"]:.2f}%一致率，实体{100*m["always_supported_baseline"]["entity"]:.2f}%，属性{100*m["always_supported_baseline"]["attribute"]:.2f}%。因此属性88.73%不能单独证明三分类能力强，它恰好与全答supported的属性一致率相同。',
      '旧参考为supported的实体，模型找回386/413（93.46%）；旧参考hallucinated找回33/52（63.46%）；旧参考uncertain只找回8/43（18.60%）。主要失衡是把不确定判成确定标签，以及少量真目标漏检/类别混淆。旧参考证据标准尚未独立裁决，不能把所有分歧归为模型错误。','',
      '## 已逐图核查的问题','',
      '- **上下文丢失及词义选择：332570的menu。** 输入只保留“a menu”，模型将其解释成餐厅菜单；原图手机屏幕确有Menu入口，旧备注明确指向界面菜单。下一项应只补原caption中可验证的上下文窗口，再测试词义消歧，不能把旧参考答案或备注放进请求。',
      '- **小目标与遮挡：381925小狗、519838远车。** 仍有漏认或过强的缺席判断。小目标问题不因扩大到完整旧数据就自动消失。',
      '- **玩具细类别：399741。** 模型把黑斑毛绒玩具识别成teddy bear，旧备注认为是cow。原图可见黑斑和突出的口鼻；旧cow与模型bear都应按明确可见特征复核，不应假定任一标签天然正确。本轮没有改参考。',
      '- **存在证据门槛：110196的highway。** 高架结构、指示牌可见，模型因未见路面/车道线就否定highway，旧标签根据整体结构支持；这是可见结构与类别定义边界，不只是有没有物体。',
      '- **细粒度人物称谓：388829的man。** 人物存在明确，旧标签对细分类别保持不确定，模型直接支持man。应分开审视人物存在与细分类别证据，不能用person容易识别推断man命题必然正确。',
      '- **数据接口仍有缺口。** 旧命题的source_window常只是名词片段，无法提供多主体指代；完整命题的旧标签也不能未经审核转移到删除限定词后的新命题。此轮保留标签，不以改题目方式提高分数。','',
      '## 产物与验证','',
      '- [全部原图分歧复核页](BAD_CASES.html)，以及`bad_cases.jsonl`、`bad_case_summary.jsonl`。',
      '- `references.jsonl`保留来源事实、旧标签、对齐关系及类型审计；`tasks.jsonl`不含这些参考答案。',
      '- `metrics.json`、`protocol.json`、`excluded.jsonl`分别记录完整分数、冻结口径和排除原因。',
      '- `run/`保存所有原始响应及检查点，`validation.json`记录实际模型核验、恢复和完整性检查。',
      '- 本轮未重新测align或整条decompose→align→verify链；没有将单个模块分数拼成端到端准确率。','']
    (root/'RESULTS.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps({'bad_cases':len(bad),'entity':cell(overall['entity']),'attribute':cell(overall['attribute']),'all':cell(overall['all'])},ensure_ascii=False))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();main(a.output)
