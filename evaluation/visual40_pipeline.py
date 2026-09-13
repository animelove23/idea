"""Frozen text-only v6 -> Coverage -> v1.3 Alignment for the 40-image visual audit."""
import argparse
import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from decomposition.config import API_CONFIG_PATH, load_api_config
from decomposition.storage import digest, output_lock, write_json, write_jsonl
from decomposition.v6.pipeline import DecomposerV6, V6Failure, prompt
from .alignment_core import PairAligner, fallback_alignments
from .common import JsonStage, StageFailure
from .coverage import CoverageAudit
from .fewshot_experiment import read_lines
from .run import checkpoint

ROOT=Path('outputs/visual40_v1')


def freeze():
    assert not (ROOT/'manifest.json').exists(), 'Already frozen'
    for d in ('decomposition','coverage','entities','alignments','started','frozen','pairs','labels'):
        (ROOT/d).mkdir(exist_ok=True)
    files=list(Path('evaluation').glob('*.py'))+list(Path('evaluation/prompts').glob('*.txt'))+list(Path('evaluation/examples').glob('*.jsonl'))
    files += [p for p in Path('decomposition/v6').glob('*') if p.is_file()]
    files += [Path('decomposition/config.py'),Path('decomposition/semantic_decomposer.py'),Path('decomposition/storage.py')]
    hashes={}
    for p in files:
        hashes[str(p)]=digest(p.read_text(encoding='utf-8'))
        dest=ROOT/'frozen'/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
    rows=read_lines(ROOT/'selected.jsonl');assert len(rows)==40
    write_json(ROOT/'manifest.json',dict(selection_digest=digest(rows),files=hashes,images=40,captions=80,
               stages='v6 decomposition -> one Coverage pass -> entity alignment -> v1.3 fact alignment',
               workers=4,normal_max_requests=240,absolute_max_requests=320,thinking='disabled',
               destination='https://api.deepseek.com',images_sent=False,visual_labels_sent=False,
               verification='assistant visual inspection of original images, not DeepSeek'))
    (ROOT/'decomposer_prompt.txt').write_text(prompt(8),encoding='utf-8')
    print('Frozen 40 image pairs / 80 captions; normal 240, maximum 320 text-only requests.')


def report():
    all_rows=read_lines(ROOT/'selected.jsonl');pairs=[];alignments=[];usage=Counter();calls=0;states={}
    for p in (ROOT/'pairs').glob('*.json'):pairs.append(json.loads(p.read_text(encoding='utf-8')))
    for name in ('decomposition','coverage','entities','alignments'):
        items=[json.loads(p.read_text(encoding='utf-8')) for p in (ROOT/name).glob('*.json')]
        states[name]=dict(Counter(x['status'] for x in items))
        for item in items:
            a=item.get('audit',{});calls+=a.get('api_calls',0)
            usages=[r.get('usage',{}) for r in a.get('attempts',[])] if name=='decomposition' else [a.get('usage',{})]
            for u in usages:usage.update({k:v for k,v in u.items() if type(v)==int})
        if name=='alignments':alignments=items
    write_jsonl(ROOT/'pairs.jsonl',pairs);write_jsonl(ROOT/'alignment.jsonl',alignments)
    write_json(ROOT/'pipeline_status.json',dict(pairs_completed=len(pairs),alignment_completed=len(alignments),planned=len(all_rows),
               api_calls=calls,usage=dict(usage),states=states))


def run():
    manifest=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
    selected=read_lines(ROOT/'selected.jsonl');assert digest(selected)==manifest['selection_digest']
    for name,h in manifest['files'].items():assert digest(Path(name).read_text(encoding='utf-8'))==h,name
    config=load_api_config(API_CONFIG_PATH,timeout=120)
    assert config.base_url.rstrip('/')==manifest['destination']
    write_json(ROOT/'execution_config.json',dict(model=config.model,temperature=0,thinking='disabled',workers=4,max_tokens=config.max_tokens))
    examples={s:read_lines(Path(f'evaluation/examples/{s}.jsonl')) for s in ('coverage','entities','alignment_core')}
    def worker(row):
        pid=row['pair_id'];stage=JsonStage(config,examples=examples)
        decomposer=DecomposerV6(config,shots=8,frozen_prompt=(ROOT/'decomposer_prompt.txt').read_text(encoding='utf-8'))
        coverage=CoverageAudit(stage);aligner=PairAligner(stage);docs={};failed=False
        for side in ('original','steer'):
            key=pid+'_'+side;text=row[side+'_text']
            def decompose():
                try:
                    doc,audit=decomposer.decompose(text);doc['id']=key
                    return dict(status=doc['status'],document=doc,audit=audit)
                except V6Failure as exc:
                    return dict(status='failed',document=dict(id=key,text=text,facts=[]),error=str(exc),audit=exc.audit)
            result=checkpoint(ROOT,'decomposition',key,decompose)
            if result['status']=='failed':docs[side]=result['document'];failed=True;continue
            cov=checkpoint(ROOT,'coverage',key,lambda:coverage.run(result['document']))
            docs[side]=cov['augmented_document']
        pair=dict(pair_id=pid,image_id=row['image_id'],image_path=str(ROOT/'images'/f'{pid}.jpg'),**docs)
        write_json(ROOT/'pairs'/f'{pid}.json',pair)
        def entities():
            if failed:return dict(pair_id=pid,status='failed',error='decomposition failed',audit={'api_calls':0})
            try:return dict(pair_id=pid,**aligner.entities(docs['original'],docs['steer']))
            except StageFailure as exc:return dict(pair_id=pid,status='failed',error=str(exc),audit=exc.audit)
        e=checkpoint(ROOT,'entities',pid,entities)
        def facts():
            if e['status']=='failed':return dict(pair_id=pid,status='failed',error=e['error'],fact_alignment=fallback_alignments(docs['original'],docs['steer']),audit={'api_calls':0})
            try:return aligner.facts(pid,docs['original'],docs['steer'],e)
            except StageFailure as exc:return dict(pair_id=pid,status='failed',error=str(exc),fact_alignment=fallback_alignments(docs['original'],docs['steer']),audit=exc.audit)
        a=checkpoint(ROOT,'alignments',pid,facts)
        print(pid,'done',a['status'],len(docs['original']['facts']),len(docs['steer']['facts']),flush=True)
    with output_lock(ROOT):
        with ThreadPoolExecutor(max_workers=4) as pool:
            for f in as_completed([pool.submit(worker,r) for r in selected]):f.result();report()
    report();assert json.loads((ROOT/'pipeline_status.json').read_text(encoding='utf-8'))['api_calls']<=320
    print('DONE',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['freeze','run','report']);args=p.parse_args();globals()[args.mode]()
