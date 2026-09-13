"""Frozen, alternating zero/eight-shot downstream comparison with three fresh repeats."""
import argparse
import itertools
import json
from collections import Counter
from pathlib import Path
from decomposition.storage import digest, write_json, write_jsonl
from .run import prepare, execute, load_pairs
from .common import require


def freeze(pairs_path, out):
    require(not out.exists(), 'Use a new experiment directory')
    pairs=load_pairs(pairs_path)
    sources=[json.loads(x) for x in Path('evaluation/examples/synthetic_sources.jsonl').read_text(encoding='utf-8').splitlines()]
    texts={p[s]['text'].strip().casefold() for p in pairs for s in ['original','steer']}
    demonstrations={p[s]['text'].strip().casefold() for p in sources for s in ['original','steer']}
    require(len(sources)==8 and len(demonstrations)==16 and not texts & demonstrations,'examples/test leakage')
    out.mkdir(parents=True)
    write_jsonl(out/'pairs.jsonl',pairs)
    schedule=[]
    # Alternate order across repetitions to reduce a simple order/time confound.
    for repeat in range(1,4):
        for shots in ([0,8] if repeat%2 else [8,0]):
            name=f's{shots}_r{repeat}'
            prepare(pairs_path,out/name,shots=shots)
            schedule.append(dict(run=name,shots=shots,repeat=repeat))
    write_json(out/'experiment.json',dict(schedule=schedule,maximum_requests=96,
        fresh_pipeline_runs=6,examples_per_stage=8,synthetic_caption_count=16,test_caption_count=len(texts),
        model_policy='same configured model, temperature 0, thinking disabled, no automatic retries',
        comparison='end-to-end downstream: examples change Coverage AND both Alignment stages; not an isolated Aligner ablation',
        author='assistant-authored examples; no human alignment gold',
        development_set=True,prior_failure_informed_design=True,
        repeated_runs='independent network requests; no cross-run cache reuse; same original decomposer outputs',
        accuracy_metrics='not available without human gold',
        original_fact_stability='per original fact, exact status plus partner semantic signatures; technical failures reported separately and not counted as consistent semantic success',
        enrollment='all four pairs in every run; failed pairs remain in denominators',
        example_test_caption_overlap=0))
    print('Frozen 6 runs; maximum 96 requests; no image or visual verification calls.',flush=True)


def run_all(out):
    plan=json.loads((out/'experiment.json').read_text(encoding='utf-8'))
    for run in plan['schedule']:
        print('RUN',run['run'],flush=True)
        execute(out/run['run'])
        compare(out)


def read_lines(path):
    return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()] if path.exists() else []


def inspect_run(path,pairs):
    if not (path/'summary.json').exists(): return None
    stats=json.loads((path/'summary.json').read_text(encoding='utf-8'))
    covs={c['input_digest']:c for c in read_lines(path/'coverage.jsonl')}
    aligns={a['pair_id']:a for a in read_lines(path/'alignment.jsonl')}
    signature={}; details=[]; errors=Counter(); semantic=0; technical=0; main_total=0
    for pair in pairs:
        if pair['pair_id'] not in aligns: continue
        alignment=aligns[pair['pair_id']]
        docs={s:covs[digest(pair[s])]['augmented_document'] for s in ['original','steer']}
        facts={s:{f['id']:f for f in doc['facts']} for s,doc in docs.items()}
        rows=alignment['fact_alignment']
        for r in rows:
            if r['status']=='ambiguous': errors[r['reason']]+=1
        for side in ['original','steer']:
            other='steer' if side=='original' else 'original'
            for f in pair[side]['facts']:
                if f['type']=='other': continue
                matching=[r for r in rows if f['id'] in r[side+'_fact_ids']]
                require(len(matching)==1,'original fact not assigned exactly once')
                r=matching[0]
                key=f"{pair['pair_id']}:{side}:{f['id']}"
                is_technical=r['reason'] in ['stage_failed','alignment_validation_error']
                partners=sorted(tuple(facts[other][fid].get(k,'') for k in ['type','fact','assertion','polarity']) for fid in r[other+'_fact_ids'])
                signature[key]=None if is_technical else {'status':r['status'],'partners':partners}
                main_total+=1
                technical+=is_technical
                semantic+=not is_technical
                details.append(dict(pair_id=pair['pair_id'],side=side,fact_id=f['id'],fact=f['fact'],status=r['status'],reason=r['reason'],partner_fact_ids=r[other+'_fact_ids'],technical_failure=is_technical))
    return dict(summary=stats,signatures=signature,original_main_facts=main_total,technical_original_main_facts=technical,
                semantic_output_original_main_facts=semantic,ambiguous_reason_counts=dict(errors),details=details)


def compare(out):
    plan=json.loads((out/'experiment.json').read_text(encoding='utf-8'))
    pairs=load_pairs(out/'pairs.jsonl')
    results={}; conditions={}
    for spec in plan['schedule']:
        record=inspect_run(out/spec['run'],pairs)
        if record is not None: results[spec['run']]=record
    for shots in [0,8]:
        group=[results[f's{shots}_r{r}'] for r in range(1,4) if f's{shots}_r{r}' in results]
        pairwise=[]
        for (i,a),(j,b) in itertools.combinations(enumerate(group,1),2):
            keys=set(a['signatures']) & set(b['signatures'])
            valid=[k for k in keys if a['signatures'][k] is not None and b['signatures'][k] is not None]
            agree=sum(a['signatures'][k]==b['signatures'][k] for k in valid)
            states=sum(a['signatures'][k]['status']==b['signatures'][k]['status'] for k in valid)
            pairwise.append(dict(repeats=[i,j],original_main_facts=len(keys),both_nontechnical=len(valid),
                exact_agree=agree,status_agree=states,strict_agreement_all=agree/len(keys) if keys else None,
                strict_agreement_nontechnical=agree/len(valid) if valid else None))
        conditions[str(shots)]=dict(runs_observed=len(group),
            requests=sum(g['summary']['api_calls'] for g in group),
            coverage_added=[g['summary']['coverage_added'] for g in group],
            entity_status=dict(sum((Counter(g['summary']['entity_status']) for g in group),Counter())),
            alignment_status=dict(sum((Counter(g['summary']['alignment_status']) for g in group),Counter())),
            main_alignment_rows=dict(sum((Counter(g['summary']['alignment_rows_main']) for g in group),Counter())),
            ambiguous_reason_counts=dict(sum((Counter(g['ambiguous_reason_counts']) for g in group),Counter())),
            original_main_fact_assignments=sum(g['original_main_facts'] for g in group),
            technical_original_main_fact_assignments=sum(g['technical_original_main_facts'] for g in group),
            pairwise_stability=pairwise)
    write_json(out/'comparison.json',dict(conditions=conditions,accuracy=None,human_gold=False,
        caution='Development-set end-to-end comparison; exact semantic-string partner signatures can undercount equivalent rewordings; consistent errors remain possible. Technical failures cannot earn semantic consistency credit.'))
    write_jsonl(out/'original_fact_comparison.jsonl',[dict(run=name,**d) for name,r in results.items() for d in r['details']])
    lines=['# 下游 0-shot / 8-shot 对照','',
        '使用4对既有真实caption；每组3次独立请求运行。例子为助手编写的另外16条合成caption，每阶段8个示例。没有改Decomposer、原始事实或语义规则。当前是已见开发集，不是独立泛化测试。','',
        '没有人工gold，因此不报告准确率、Precision/Recall/F1。此处比较技术可用性、状态分布、重复一致性；具体语义仍需审核。','',
        '| 条件 | 已运行轮数 | 请求数 | Coverage新增/轮 | Entity状态 | Alignment状态 |','| --- | --- | --- | --- | --- | --- |']
    for s,c in conditions.items():
        lines.append(f"| {s}-shot | {c['runs_observed']} | {c['requests']} | {c['coverage_added']} | {c['entity_status']} | {c['alignment_status']} |")
    lines += ['', '## 重复一致性','',
        '只比较固定的原始主线事实，不因Coverage追加数量变化改变原始分母。比较状态及对侧完整事实签名；技术失败不计作语义一致。严格签名会把同义改写算作不同，不能当语义准确率。','']
    for s,c in conditions.items():
        lines += [f'### {s}-shot','', '```json',json.dumps(c,ensure_ascii=False,indent=2),'```','']
    lines += ['## 逐条可审核对照','', '| pair / side / fact | 原始事实 | 0-shot r1/r2/r3 | 8-shot r1/r2/r3 |','| --- | --- | --- | --- |']
    detailmaps={name:{(d['pair_id'],d['side'],d['fact_id']):d for d in r['details']} for name,r in results.items()}
    keys=sorted(set().union(*(set(m) for m in detailmaps.values()))) if detailmaps else []
    for key in keys:
        d=next(m[key] for m in detailmaps.values() if key in m)
        states=[]
        for s in [0,8]:
            parts=[]
            for r in range(1,4):
                x=detailmaps.get(f's{s}_r{r}',{}).get(key)
                parts.append('未完成' if x is None else x['status']+'/'+x['reason']+' → '+','.join(x['partner_fact_ids']))
            states.append('<br>'.join(parts))
        lines.append('| '+' | '.join(v.replace('|','\\|') for v in ['/'.join(key),d['fact'],*states])+' |')
    (out/'COMPARISON_REPORT.md').write_text('\n'.join(lines),encoding='utf-8')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('mode',choices=['freeze','run','compare'])
    parser.add_argument('--pairs',type=Path,default=Path('outputs/downstream_v1/pairs.jsonl'))
    parser.add_argument('--output',type=Path,default=Path('outputs/downstream_fewshot_v1'))
    args=parser.parse_args()
    if args.mode=='freeze': freeze(args.pairs,args.output)
    elif args.mode=='run': run_all(args.output)
    else: compare(args.output)
