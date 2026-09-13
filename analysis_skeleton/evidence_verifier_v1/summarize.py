"""Preserve first-run scores, isolate compiler fix, and report every routed follow-up."""
import copy,json,html,base64
from pathlib import Path
from analysis_skeleton.common import read_json,read_jsonl,write_json,write_jsonl,check_frozen
from .compiler import compile_evidence
from .experiment import score

def main(root):
    root=Path(root);check_frozen(root/'run');check_frozen(root/'roi_run')
    rows=read_jsonl(root/'run/results.jsonl');ref={r['case_id']:r for r in read_jsonl(root/'references.jsonl')}
    control=[r for r in rows if r['condition']=='control'];raw=[r for r in rows if r['condition']=='evidence'];compiled=[];repairs=[]
    for r in raw:
        new=copy.deepcopy(r)
        try:
            new['prediction']=compile_evidence(json.loads(r['audit']['raw_content']),r['semantic_type']);new['status']='complete'
        except (ValueError,TypeError,KeyError):new['prediction']={};new['status']='technical_failure'
        if new['status']!=r['status'] or new['prediction'].get('label')!=r['prediction'].get('label'):
            repairs.append({'case_id':r['case_id'],'old_status':r['status'],'new_status':new['status'],'old_label':r['prediction'].get('label'),'new_label':new['prediction'].get('label'),'compiler_note':new['prediction'].get('compiler_note'),'new_api_calls':0})
        compiled.append(new)
    followups=read_jsonl(root/'roi_run/results.jsonl');variants={'control':control,'evidence_raw_v1':raw,'evidence_compiler_v2':compiled}
    for condition in ('full_repeat','roi'):
        fmap={r['case_id']:r for r in followups if r['condition']==condition};variant=[]
        for r in compiled:
            new=copy.deepcopy(r)
            if r['case_id'] in fmap:
                selected=fmap[r['case_id']];new.update(prediction=selected['prediction'],status=selected['status'],followup_audit=selected['audit'])
            variant.append(new)
        variants[condition]=variant
    metrics={}
    for name,rr in variants.items():
        labeled=[{**r,'reference_label':ref[r['case_id']]['reference_label']} for r in rr]
        metrics[name]={'all':score(labeled,60),'entity':score([r for r in labeled if r['semantic_type']=='entity'],41),'attribute':score([r for r in labeled if r['semantic_type']=='attribute'],19)}
    metrics['note']='Compiler correction reuses exactly the same raw outputs; ROI and full-repeat policies replace all selected cases, never pick best labels. Variant score usage fields describe retained first-stage audit only; actual calls are reported separately.'
    metrics['actual_new_calls']=read_json(root/'call_metrics.json')['new_api_calls']+read_json(root/'roi_calls.json')['new_api_calls']
    metrics['candidate_90_percent_reached']=metrics['roi']['entity']['correct']>=37
    metrics['accepted_as_production_default']=False
    metrics['deployment_reason']='Entity gate >=37/41 not met; evidence and bbox are not independently verified.'
    write_json(root/'final_metrics.json',metrics);write_jsonl(root/'compiler_repairs.jsonl',repairs)
    write_jsonl(root/'final_results.jsonl',variants['roi'])
    cm={r['case_id']:r for r in control};fm={r['case_id']:r for r in variants['roi']};paired=[]
    for cid,r in ref.items():
        a,b=cm[cid],fm[cid];gold=r['reference_label']
        paired.append({'case_id':cid,'semantic_type':a['semantic_type'],'reference':gold,'control':a['prediction'].get('label'),'final':b['prediction'].get('label'),'improved':a['prediction'].get('label')!=gold and b['prediction'].get('label')==gold,'regressed':a['prediction'].get('label')==gold and b['prediction'].get('label')!=gold})
    write_jsonl(root/'final_paired.jsonl',paired)
    inputs={r['case_id']:r for r in read_jsonl(root/'inputs.jsonl')};cards=[]
    for p in paired:
        if p['control']==p['reference'] and p['final']==p['reference']:continue
        cid=p['case_id'];r=fm[cid];e=r['prediction'].get('evidence',{});data=base64.b64encode(Path(inputs[cid]['input']['image_path']).read_bytes()).decode('ascii');b=e.get('bbox')
        overlay='' if not b else f'<svg viewBox="0 0 1000 1000" preserveAspectRatio="none"><rect x="{b[0]}" y="{b[1]}" width="{b[2]-b[0]}" height="{b[3]-b[1]}" fill="none" stroke="#ee4258" stroke-width="5"/></svg>'
        esc=html.escape
        text=f'<h2>{esc(cid)}</h2><p>{esc(inputs[cid]["input"]["statement"])}</p><p>参考 {p["reference"]} · 原版 {p["control"]} · 新版 {p["final"]}</p><p>原理由：{esc(cm[cid]["prediction"].get("reason",""))}</p><p>新版证据：{esc(e.get("visible_cues",""))}</p><p>对象：{esc(e.get("observed_category",""))}；状态：{esc(e.get("candidate_status",""))}；区域：{esc(e.get("region_status",""))}；限制：{esc(e.get("limitation",""))}</p><p>搜索范围：{esc(e.get("scope",""))}</p><p>参考理由：{esc(ref[cid]["reference_reason"])}</p>'
        cards.append(f'<article><div class="picture"><img src="data:image/jpeg;base64,{data}">{overlay}</div><div>{text}</div></article>')
    (root/'BAD_CASES.html').write_text('<!doctype html><html lang="zh"><meta charset="utf-8"><title>视觉证据复核</title><style>body{font-family:system-ui;max-width:1250px;margin:auto;background:#f5f6fa;padding:24px}article{display:grid;grid-template-columns:48% 1fr;gap:22px;background:white;padding:20px;margin:22px 0}p{line-height:1.6}.picture{position:relative;align-self:start}img{width:100%;display:block}svg{position:absolute;inset:0;width:100%;height:100%}@media(max-width:700px){article{grid-template-columns:1fr}}</style><h1>原图、视觉证据与标签复核</h1><p>红框是模型返回值按声明的0..1000原图坐标投影，不是已验证主体框。框可能偏移或使用错误坐标单位；只作审计，不能直接当作真值。参考是旧助手候选，未修改。</p>'+''.join(cards)+'</html>',encoding='utf-8')
    print(json.dumps({k:{t:metrics[k][t]['correct'] for t in ('all','entity','attribute')} for k in variants},ensure_ascii=False))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();main(a.output)
