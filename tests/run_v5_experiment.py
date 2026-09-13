"""Frozen v5 pilot; 45 decompositions / 90 normal API stage calls, max 180."""
import argparse
import itertools
import json
import random
import shutil
from collections import Counter,defaultdict
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
from pathlib import Path
from decomposition.config import API_CONFIG_PATH,load_api_config
from decomposition.storage import digest,write_json,write_jsonl
from decomposition.v5.pipeline import DecomposerV5,V5Failure,prompts
from decomposition.v5.metrics import compare,prf,change_score
from decomposition.v5.schema import TYPES
from decomposition.v5 import VERSION

OUT=Path('outputs/five_dim_v5/experiment_v1')

def prepare(out):
    out.mkdir(parents=True,exist_ok=False);(out/'checkpoints').mkdir();(out/'frozen').mkdir()
    refs=[json.loads(x) for x in Path('annotation/v5/references.jsonl').read_text(encoding='utf-8').splitlines()]
    manifest=json.loads(Path('annotation/v5/manifest.json').read_text(encoding='utf-8'))
    assert digest(refs)==manifest['references_digest']
    jobs=[]
    for r in refs:
        for shots in ([0,8] if r['kind']=='holdout' else [8]):
            jobs.append({'job_id':f"{r['id']}_s{shots}_r1",'id':r['id'],'kind':r['kind'],'shots':shots,'repeat':1,'text':r.get('text',r.get('document',{}).get('text'))})
    for sample in ['415015_vista','299573_vanilla','417586_vista']:
        base=next(j for j in jobs if j['id']==sample and j['shots']==8)
        for rep in [2,3]:jobs.append({**base,'job_id':f'{sample}_s8_r{rep}','repeat':rep})
    dev=[json.loads(x) for x in Path('outputs/fewshot_v1_pilot/inputs.jsonl').read_text(encoding='utf-8').splitlines()]
    for r in dev:jobs.append({'job_id':f"dev_{r['batch_number']:02}_s8_r1",'id':f"dev_{r['batch_number']:02}",'kind':'regression','shots':8,'repeat':1,'text':r['caption']})
    random.Random(5102026).shuffle(jobs);assert len(jobs)==45
    ps={str(n):prompts(n) for n in [0,8]};config=load_api_config(API_CONFIG_PATH,timeout=120,retries=1)
    assert config.base_url.rstrip('/')=='https://api.deepseek.com'
    for p in Path('decomposition/v5').glob('*'):
        if p.is_file():shutil.copy2(p,out/'frozen'/p.name)
    write_jsonl(out/'references.jsonl',refs);write_json(out/'jobs.json',jobs);write_json(out/'prompts.json',ps)
    protocol={'version':'five-dim-v5.0-pilot1','created_at':datetime.now(timezone.utc).isoformat(),'model':config.model,'base_url':config.base_url,'max_tokens':config.max_tokens,'timeout':120,'thinking':'disabled','temperature':0,'workers':4,'decompositions':45,'normal_stage_calls':90,'maximum_http_requests':180,'prompts_digest':digest(ps),'references_digest':digest(refs),'jobs_digest':digest(jobs),'files':{p.name:digest(p.read_text(encoding='utf-8')) for p in (out/'frozen').iterdir()},'label_origin':manifest['label_origin'],'holdout_images':manifest['holdout_images'],'repeat_policy':'three independent uncached runs on three captions; nine pair comparisons','metric_policy':'entity metadata-only one-to-one alignment; frozen lexical registry; type/roles/units/group binding/modality/polarity/event scope; failures count as empty predictions for holdout end-to-end recall','scope':'8 synthetic demonstrations; 8 image-disjoint holdout captions; 14 old development regressions; 4 paraphrases; 5 controlled variants; 6 extra repeat runs. Gold holdout labels are not sent.'}
    protocol['version']=VERSION+'-pilot';write_json(out/'protocol.json',protocol);print(json.dumps(protocol,ensure_ascii=False),flush=True)

def execute(out):
    protocol=json.loads((out/'protocol.json').read_text(encoding='utf-8'));jobs=json.loads((out/'jobs.json').read_text(encoding='utf-8'));ps=json.loads((out/'prompts.json').read_text(encoding='utf-8'))
    assert digest(jobs)==protocol['jobs_digest'] and digest(ps)==protocol['prompts_digest']
    for name,h in protocol['files'].items():assert digest(Path('decomposition/v5',name).read_text(encoding='utf-8'))==h
    c=load_api_config(API_CONFIG_PATH,timeout=protocol['timeout'],retries=1)
    assert c.base_url==protocol['base_url']=='https://api.deepseek.com' and c.model==protocol['model'] and c.max_tokens==protocol['max_tokens']
    import threading
    stop=threading.Event()
    def run(j):
        path=out/'checkpoints'/f"{j['job_id']}.json"
        if path.exists():return j['job_id'],'existing'
        if stop.is_set():return j['job_id'],'cancelled'
        r={**j,'started_at':datetime.now(timezone.utc).isoformat()}
        try:
            document,audit=DecomposerV5(c,shots=j['shots'],frozen_prompts=ps[str(j['shots'])]).decompose(j['text'])
            r.update(status='success',document=document,audit=audit)
        except V5Failure as e:
            r.update(status='failed',error=str(e),audit=e.audit)
            if any(f'HTTP Error {code}' in str(e) for code in [400,401,403,404]):stop.set()
        r['finished_at']=datetime.now(timezone.utc).isoformat();write_json(path,r)
        return j['job_id'],r['status']
    pending=[j for j in jobs if not (out/'checkpoints'/f"{j['job_id']}.json").exists()]
    if pending:
        print(*run(pending[0]),flush=True)
        if not stop.is_set():
            with ThreadPoolExecutor(max_workers=protocol['workers']) as pool:
                for f in as_completed([pool.submit(run,j) for j in pending[1:]]):print(*f.result(),flush=True)
    report(out)

def aggregate(scores,key=None):
    xs=[x[key] if key else x for x in scores]
    return prf(*(sum(x[k] for x in xs) for k in ['tp','fp','fn']))

def report(out):
    # Always score historic runs with their own frozen registry and scorer.
    import importlib.util
    import importlib
    import sys
    package='_v5_report_'+digest(str(out.resolve()))[:12]
    if package not in sys.modules:
        spec=importlib.util.spec_from_file_location(package,out/'frozen'/'__init__.py',submodule_search_locations=[str((out/'frozen').resolve())])
        module=importlib.util.module_from_spec(spec);sys.modules[package]=module;spec.loader.exec_module(module)
    scorer=importlib.import_module(package+'.metrics')
    compare,change_score=scorer.compare,scorer.change_score
    jobs=json.loads((out/'jobs.json').read_text(encoding='utf-8'));refs=[json.loads(x) for x in (out/'references.jsonl').read_text(encoding='utf-8').splitlines()]
    rows={p.stem:json.loads(p.read_text(encoding='utf-8')) for p in (out/'checkpoints').glob('*.json')};refmap={r['id']:r for r in refs}
    def doc(r):return r.get('document',{'entities':[],'facts':[]}) if r else {'entities':[],'facts':[]}
    def result(id,shots=8,repeat=1):return rows.get(f'{id}_s{shots}_r{repeat}')
    summary={'planned':len(jobs),'completed':len(rows),'structural':{},'holdout':{},'repeats':[],'paraphrases':[],'known_changes':[],'coverage':{}}
    attempts=[a for r in rows.values() for a in r.get('audit',{}).get('attempts',[])]
    summary['http_requests']=len(attempts);summary['prompt_tokens']=sum((a.get('usage') or {}).get('prompt_tokens',0) for a in attempts);summary['completion_tokens']=sum((a.get('usage') or {}).get('completion_tokens',0) for a in attempts)
    details={}
    for shots in [0,8]:
        rr=[r for r in rows.values() if r['shots']==shots];ok=[r for r in rr if r['status']=='success']
        summary['structural'][str(shots)]={'completed':len(rr),'raw_valid':sum(r['audit']['raw_valid'] for r in ok),'repaired_success':sum(r['audit']['repaired'] for r in ok),'final_success':len(ok),'failed':len(rr)-len(ok)}
        evaluated=[]
        for ref in refs:
            if ref['kind']!='holdout':continue
            r=result(ref['id'],shots)
            if r is None:continue
            score=compare(doc(r),ref['document']);evaluated.append((ref,score));details[r['job_id']]=score
        summary['holdout'][str(shots)]={'n':len(evaluated),'overall':aggregate([s for _,s in evaluated],'overall'),'by_type':{t:aggregate([s['by_type'][t] for _,s in evaluated]) for t in TYPES},'entity_alignment':aggregate([s['entity_alignment'] for _,s in evaluated]),'action_roles':aggregate([s['action_roles'] for _,s in evaluated]),'by_method':{m:aggregate([s['overall'] for r,s in evaluated if r['method']==m]) for m in ['vanilla','vista']}}
    for id in ['415015_vista','299573_vanilla','417586_vista']:
        for a,b in itertools.combinations([1,2,3],2):
            ra,rb=result(id,repeat=a),result(id,repeat=b)
            if not ra or not rb:continue
            score=compare(doc(rb),doc(ra))['overall']
            summary['repeats'].append({'id':id,'runs':[a,b],'both_valid':ra['status']==rb['status']=='success',**score})
    for ref in refs:
        if ref['kind']=='paraphrase':
            a,b=result(ref['base']),result(ref['id'])
            if a and b:
                s=compare(doc(b),doc(a))['overall'];summary['paraphrases'].append({'id':ref['id'],'both_valid':a['status']==b['status']=='success',**s,'false_disappearance_rate':s['fn']/(s['tp']+s['fn']) if s['tp']+s['fn'] else None})
        if ref['kind']=='controlled' and ref['change']!='base':
            a,b=result('probe_base'),result(ref['id'])
            if a and b:
                summary['known_changes'].append({'id':ref['id'],'both_valid':a['status']==b['status']=='success',**change_score(doc(a),doc(b),refmap['probe_base']['document'],ref['document'])})
    summary['repeat_micro']=aggregate(summary['repeats']);summary['paraphrase_micro']=aggregate(summary['paraphrases']);summary['known_change_micro']=aggregate(summary['known_changes'])
    rates=[r['false_disappearance_rate'] for r in summary['paraphrases'] if r['false_disappearance_rate'] is not None]
    if rates:
        rng=random.Random(510);boot=sorted(sum(rng.choices(rates,k=len(rates)))/len(rates) for _ in range(2000))
        summary['false_disappearance']={'mean_caption_rate':sum(rates)/len(rates),'caption_cluster_bootstrap_95':[boot[49],boot[1949]],'n_image_pairs':len(rates),'caveat':'tiny development diagnostic; no steering-effect claim or significance conclusion'}
    for name,select in [('all',lambda r:True),('vanilla',lambda r:r['id'] in refmap and refmap[r['id']].get('method')=='vanilla'),('vista',lambda r:r['id'] in refmap and refmap[r['id']].get('method')=='vista')]:
        rr=[r for r in rows.values() if r['shots']==8 and r['repeat']==1 and select(r)];ds=[doc(r) for r in rr];fs=[f for d in ds for f in d.get('facts',[])]
        unresolved=sum(bool(d.get('unresolved')) for d in ds);unknown=sum(len(d.get('registry_queue',[])) for d in ds)
        summary['coverage'][name]={'captions':len(rr),'failed':sum(r['status']!='success' for r in rr),'unresolved_captions':unresolved,'unresolved_caption_rate':unresolved/len(rr) if rr else None,'unresolved_records':sum(len(d.get('unresolved',[])) for d in ds),'excluded_records':sum(len(d.get('excluded',[])) for d in ds),'facts':len(fs),'known_registry_fact_rate':1-unknown/len(fs) if fs else None,'unknown_by_type':dict(Counter(q.get('type') for d in ds for q in d.get('registry_queue',[]))),'warning_count':sum(len(d.get('warnings',[])) for d in ds),'caveat':'registry coverage is not semantic recall; unresolved records may span multiple dimensions, so no invented type denominator'}
    summary['meaning']='Reference-matched structure P/R/F1 against assistant-authored frozen labels, not independently verified human accuracy. All completed failures enter holdout as empty predictions. Unknown predicates and warnings are not silently removed.'
    write_json(out/'metrics.json',summary);write_json(out/'metric_details.json',details);write_jsonl(out/'results.jsonl',list(rows.values()))
    print(json.dumps(summary,ensure_ascii=False),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','execute','report']);p.add_argument('--output',type=Path,default=OUT);a=p.parse_args();globals()[a.mode](a.output)
