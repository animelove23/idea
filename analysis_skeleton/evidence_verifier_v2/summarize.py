"""Local report and original-image audit; no model calls or label changes."""
import base64,html,json
from pathlib import Path
from collections import Counter
from analysis_skeleton.common import read_json,read_jsonl,write_json,check_frozen,sha
from .experiment import report

def main(root):
    root=Path(root);report(root);m=read_json(root/'metrics.json');pairs=read_jsonl(root/'paired.jsonl')
    rows=read_jsonl(root/'run/results.jsonl');inputs={r['case_id']:r for r in read_jsonl(root/'inputs.jsonl')}
    refs={r['case_id']:r for r in read_jsonl(root/'references.jsonl')};cards=[];changes=[]
    for p in pairs:
        g=p['reference'];a=p['control'];b=p['sufficiency']
        if a!=b:changes.append({'case_id':p['case_id'],'type':p['semantic_type'],'old':a,'new':b,'reference':g,'improved':a!=g and b==g,'regressed':a==g and b!=g})
        if a==g and b==g:continue
        query=inputs[p['case_id']]['input'];data=base64.b64encode(Path(query['image_path']).read_bytes()).decode('ascii');esc=html.escape
        details=esc(json.dumps({'old':p['control_evidence'],'new':p['sufficiency_evidence']},ensure_ascii=False,indent=2))
        cards.append(f'<article><img src="data:image/jpeg;base64,{data}"><section><h2>{esc(p["case_id"])}</h2><p>{esc(query["statement"])}</p><p>旧 {a} → 新 {b}；候选参考 {g}</p><p>{esc(refs[p["case_id"]]["reference_reason"])}</p><pre>{details}</pre></section></article>')
    (root/'BAD_CASES.html').write_text('<!doctype html><html lang="zh"><meta charset="utf-8"><title>Flash证据充分性对照</title><style>body{font-family:system-ui;max-width:1300px;margin:auto;padding:24px;background:#f4f5f8}article{display:grid;grid-template-columns:45% 1fr;gap:20px;background:white;padding:20px;margin:20px 0}img{width:100%}pre{white-space:pre-wrap;font-size:12px}p{line-height:1.6}@media(max-width:700px){article{grid-template-columns:1fr}}</style><h1>Flash 同模型新旧规则复核</h1><p>原始图片与全部持续分歧/变化样本。参考标签未改；证据字段和框均是模型预测，不是真值。</p>'+''.join(cards)+'</html>',encoding='utf-8')
    write_json(root/'changes.json',changes)
    old=read_json('outputs/evidence_verifier_v1/final_metrics.json')
    def cell(v):return f'{v["correct"]}/{v["cases"]}（{100*v["agreement"]:.1f}%）'
    lines=['# Flash 证据充分性迭代报告','',
      '## 模型核查','',
      '通用配置原为deepseek-v4-pro，已改为deepseek-flash。上轮M5代码显式覆盖通用配置，120条正式请求/返回均是deepseek-flash；本轮也是同一模型，因此不能把变化解释成从Pro换到Flash的效果。M2/M3的通用默认已改变，本轮没有重测这两个模块。','',
      '## 实验边界','',
      '仅追加针对命题的证据充分性说明：区分不影响识别的模糊与真正阻断识别的模糊；缺席判断必须检查相关区域。引用原六个示例解释边界，六个示例本身完全不改。两组共120次新请求，随机交错，固定60条、原图、上下文、compiler、温度0及thinking disabled；均无ROI。样本已用于开发，参考仍是助手候选。','',
      '## 结果','',
      '| 条件 | 实体 | 属性 | 整体 | 实体错误确定判断 |',
      '|---|---:|---:|---:|---:|']
    for name,v in [('上轮直接标签基线（历史）',old['control']),('上轮证据＋ROI（历史）',old['roi']),('本轮旧证据规则（新请求）',m['control']),('本轮追加充分性说明（新请求）',m['sufficiency'])]:
        lines.append('| '+name+' | '+' | '.join(cell(v[k]) for k in ('entity','attribute','all'))+' | '+str(v['entity']['confident_errors'])+' |')
    lines += ['',f'预先固定的本轮验收通过：{m["acceptance_passed"]}。不自动提升为生产默认。',
      '历史结果供背景比较；判断本次说明的作用应比较本轮两组。不能用历史ROI组与本轮无ROI组直接归因。',
      '',f'本轮改变标签{len(changes)}条；改善{sum(x["improved"] for x in changes)}条，退化{sum(x["regressed"] for x in changes)}条。','',
      '| case | 类型 | 旧→新 | 参考 | 变化 |','|---|---|---|---|---|']
    for x in changes:lines.append(f'| {x["case_id"]} | {x["type"]} | {x["old"]} → {x["new"]} | {x["reference"]} | '+('改善' if x['improved'] else '退化' if x['regressed'] else '仍分歧')+' |')
    tests=read_json(root/'test_results.json')
    lines += ['', '## 验证与局限','',f'- 离线测试{tests["tests_run"]}项，失败{tests["failures"]}，错误{tests["errors"]}。',
      f'- 正式联网实验{m["actual_new_api_calls"]}次请求，唯一响应ID数{m["unique_response_ids"]}；请求/返回模型分布见metrics.json。',
      '- 另有受限环境的一次URLError，无响应ID，远端结果未知，独立保留在outputs/evidence_verifier_v2_flash，不进入正式配对分数；总计121次客户端调用尝试。',
      '- 原图、参考、示例、代码和输出均可追踪；断点恢复与原始响应重算核查见validation.json。',
      '- 本轮没有新增裁剪、模型投票、修改参考标签或增加重试。没有执行decompose/align端到端重跑。',
      '- 单次配对开发实验不能证明稳定提升或泛化准确率；原参考中存在待独立复核的模糊边界。','',
      '[查看原图和证据差异](BAD_CASES.html) · [逐项分数](metrics.json) · [逐项变化](changes.json)','']
    (root/'RESULTS.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps({'changes':len(changes),'improved':sum(x['improved'] for x in changes),'regressed':sum(x['regressed'] for x in changes),'gate':m['acceptance_passed']}))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();main(a.output)
