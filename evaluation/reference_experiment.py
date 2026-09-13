"""Fixed-fact 30-pair Alignment test; references never enter a network payload."""
import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
from pathlib import Path
from decomposition.storage import digest, write_json, write_jsonl, output_lock
from decomposition.config import API_CONFIG_PATH, load_api_config
from .run import prepare, load_pairs, checkpoint
from .common import JsonStage, StageFailure
from .alignment import PairAligner, fallback_alignments
from .fewshot_experiment import read_lines
from .reference_metrics import compute

SOURCE=Path('annotation/alignment_v1/batch30')
OUT=Path('outputs/alignment_reference30_v1')


def freeze():
    prepare(SOURCE/'pairs.jsonl',OUT,shots=8)
    reference=read_lines(SOURCE/'reference.jsonl')
    pairs=load_pairs(OUT/'pairs.jsonl')
    demos=read_lines(Path('evaluation/examples/synthetic_sources.jsonl'))
    caption_texts={p[s]['text'].strip().casefold() for p in pairs for s in ('original','steer')}
    demo_texts={p[s]['text'].strip().casefold() for p in demos for s in ('original','steer')}
    assert not caption_texts&demo_texts
    write_jsonl(OUT/'reference.jsonl',reference)
    manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
    manifest.update(maximum_requests=60,workers=2,reference_digest=digest(reference),
                    coverage_policy='not executed; identical fixed assistant-annotated facts for prediction and reference',
                    test_repeats=1,example_test_exact_caption_overlap=0,human_reviewed=False)
    for path in sorted(SOURCE.glob('*')):
        if not path.is_file():continue
        manifest['files'][str(path)]=digest(path.read_text(encoding='utf-8'))
        dest=OUT/'frozen'/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(path.read_bytes())
    write_json(OUT/'manifest.json',manifest)
    print('Frozen 30 real pairs, 60 captions; 8-shot; max 60 requests; Alignment only.',flush=True)


def report():
    pairs=load_pairs(OUT/'pairs.jsonl');gold=read_lines(OUT/'reference.jsonl')
    predictions=[json.loads(p.read_text(encoding='utf-8')) for p in sorted((OUT/'alignments').glob('*.json'))]
    metrics,errors,false_removals=compute(gold,predictions)
    metrics['complete']=len(predictions)==len(pairs)
    metrics['stage_status']={s:dict(Counter(json.loads(p.read_text(encoding='utf-8'))['status'] for p in (OUT/s).glob('*.json'))) for s in ('entities','alignments')}
    usage=Counter();calls=0;response_count=0
    for stage in ('entities','alignments'):
        for p in (OUT/stage).glob('*.json'):
            a=json.loads(p.read_text(encoding='utf-8')).get('audit',{})
            calls+=a.get('api_calls',0)
            if a.get('usage'):
                response_count+=1;usage.update({k:v for k,v in a['usage'].items() if type(v)==int})
    metrics.update(api_calls=calls,usage=dict(usage),responses_with_usage=response_count)
    write_json(OUT/'metrics.json',metrics);write_jsonl(OUT/'alignment.jsonl',predictions)
    write_jsonl(OUT/'errors.jsonl',errors);write_jsonl(OUT/'false_removal_audit.jsonl',false_removals)
    per_pair=[]
    pm={p['pair_id']:p for p in predictions}
    for g in gold:
        m,_,_=compute([g],[pm[g['pair_id']]] if g['pair_id'] in pm else [])
        per_pair.append(dict(pair_id=g['pair_id'],edge=m['alignment_edge'],joint=m['joint_edge_status'],status_macro_f1=m['status_macro_f1'],technical=m['technical_failure']))
    write_jsonl(OUT/'per_pair_metrics.jsonl',per_pair)
    fmt=lambda x:'N/A' if x is None else f'{x:.2%}'
    lines=['# 30 对 Alignment 参考标注测试','',
        f"完成 {len(predictions)}/30 对；API 请求 {calls}/60。固定助手标注的事实输入，8-shot不变，不运行Decomposer或Coverage。参考由助手起草，未经用户审核。",'',
        '| 指标 | Precision | Recall | F1 |','| --- | --- | --- | --- |']
    for key in ('alignment_edge','joint_edge_status','two_sided_edges_only'):
        m=metrics[key];lines.append('| '+' | '.join([key,*[fmt(m[k]) for k in ('precision','recall','f1')]])+' |')
    lines+=['','无标签Edge使用两侧fact ID集合（含∅）作为边；联合指标另要求状态相同。多对多按整组一条边，不展开成笛卡尔积。技术失败计入分母但不获TP。two_sided为仅含两侧事实的辅助指标，不涵盖单侧删除/新增和技术回退。','',
            '| 状态（逐事实） | Reference support | Precision | Recall | F1 |','| --- | --- | --- | --- | --- |']
    for s,m in metrics['status_per_class'].items():lines.append('| '+' | '.join([s,str(m['reference']),*[fmt(m[k]) for k in ('precision','recall','f1')]])+' |')
    lines += ['',f"Status Macro-F1：{fmt(metrics['status_macro_f1'])}。每个固定fact计一次；它不检查对应目标，因此必须与Edge F1一起读。",'',
        f"误删除率 FRR（确认仍完整表达）：{metrics['false_removal']['confirmed_false']}/{metrics['false_removal']['predicted_removed']} = {fmt(metrics['false_removal']['rate'])}。部分保留 {metrics['false_removal']['partial_overlap']} 条、不可裁决 {metrics['false_removal']['uncertain']} 条；把二者都算作误删除的上界为 {fmt(metrics['false_removal']['upper_bound'])}。",'',
        'Removed Precision 检查参考状态是否为 removed；FRR 只检查原事实是否仍在对侧原句完整表达，因此二者不是无条件互补。modified、partial overlap 和身份不可裁决分别保留，不强行当作完整保留。','',
        f"技术失败：{metrics['technical_failure']['facts']}/{metrics['facts']} = {fmt(metrics['technical_failure']['rate'])}。",'',
        '所有错误保存在 errors.jsonl；每条预测removed的审核依据在 false_removal_audit.jsonl；原始请求响应在entities/alignments中。参考不发送给DeepSeek。只运行一次，不能据此估计重复稳定性。']
    (OUT/'TEST_REPORT.md').write_text('\n'.join(lines),encoding='utf-8')


def run():
    manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
    pairs=load_pairs(OUT/'pairs.jsonl')
    assert digest(pairs)==manifest['pairs_digest']
    assert digest(read_lines(OUT/'reference.jsonl'))==manifest['reference_digest']
    for name,h in manifest['files'].items():assert digest(Path(name).read_text(encoding='utf-8'))==h,name
    config=load_api_config(API_CONFIG_PATH,timeout=120)
    assert config.base_url.rstrip('/')=='https://api.deepseek.com'
    identity=dict(model=config.model,max_tokens=config.max_tokens,temperature=0,thinking='disabled',timeout=120,base_url=config.base_url,workers=2)
    identity_path=OUT/'execution_config.json'
    if identity_path.exists():assert json.loads(identity_path.read_text(encoding='utf-8'))==identity
    else:write_json(identity_path,identity)
    examples={s:read_lines(Path(f'evaluation/examples/{s}.jsonl')) for s in ('entities','alignment')}
    assert all(len(x)==8 for x in examples.values())
    def worker(pair):
        pid=pair['pair_id'];o,s=pair['original'],pair['steer'];key=digest(pid)
        aligner=PairAligner(JsonStage(config,examples=examples))
        def get_entities():
            try:return dict(pair_id=pid,**aligner.entities(o,s))
            except StageFailure as exc:return dict(pair_id=pid,status='failed',error=str(exc),audit=exc.audit)
        e=checkpoint(OUT,'entities',key,get_entities)
        print(pid,'entities',e['status'],flush=True)
        def get_facts():
            if e['status']=='failed':return dict(pair_id=pid,status='failed',error='entity stage failed',fact_alignment=fallback_alignments(o,s),audit={'api_calls':0})
            try:return aligner.facts(pid,o,s,e)
            except StageFailure as exc:return dict(pair_id=pid,status='failed',error=str(exc),fact_alignment=fallback_alignments(o,s),audit=exc.audit)
        a=checkpoint(OUT,'alignments',key,get_facts)
        print(pid,'facts',a['status'],flush=True)
        return pid
    with output_lock(OUT):
        with ThreadPoolExecutor(max_workers=2) as pool:
            for future in as_completed([pool.submit(worker,pair) for pair in pairs]):
                future.result();report()
    report()
    print('DONE',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['freeze','run','report']);args=p.parse_args();globals()[args.mode]()
