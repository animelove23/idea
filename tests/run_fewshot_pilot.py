"""Frozen, image-disjoint API pilot: same rules, 0 vs 8 shots, four repeats.

Prepare is offline. Execute is explicit, uses the configured official DeepSeek
endpoint, and sends only frozen neutral examples plus caption text.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
from pathlib import Path
import random
import threading

from decomposition.config import API_CONFIG_PATH, PROMPT_VERSION, load_api_config, load_prompt
from decomposition.schemas import validate_document
from decomposition.semantic_decomposer import DeepSeekDecomposer, DecompositionError
from decomposition.storage import digest, write_json, write_jsonl

OUT=Path('outputs/fewshot_v1_pilot')
QUESTIONS={
4:'blue suitcase; walk/pass-by; appears walking away and possible leaving/preparing pick-up; no actual pickup inferred',
5:'man/mirror/phone; bathroom/sink/toilet/shower; several bottles and separate subgroups; no decorative affect',
7:'Santa Claus, fire truck, reindeer; ride/on/accompaniment; do not replace with float or generic person',
8:'young woman; white shirt and tie; vintage black-white photograph properties; bun hairstyle; smile not inferred emotion',
14:'three men; individual watch bearer vs group; hand/foot crossed; posing speculative; no invented colors or extra men',
15:'man, mirror/sink, toothbrush/hair dryer/bottle; black jacket; initial asserted self-photo and later speculative selfie; do not invent phone',
17:'girl not person; white shirt, tie around neck, long hair, smile at camera; no inferred happiness',
18:'person holds plate, cake piece on plate; no inferred person holds cake or specific sex',
20:'red fire truck and large Santa Claus FLOAT; Christmas decorations; several people and multiple spatial subgroups; no extra inferred counts',
21:'blue suitcase/handle; sidewalk; man wears jacket/jeans; exact repeated walk-past not double counted',
24:'rice AND beans; broccoli pieces several; larger/smaller comparisons and center/edge scope; no appetizing appraisal',
25:'three older men, white concrete bench; resting and possible observing/waiting/related work; truck parked; no enjoy/atmosphere',
26:'white bowl FULL of food; tabletop, rice, broccoli; no invented beans or sitting action for bowl',
29:'cake on plate AND directly stated cake on table; knife use, multiple forks/subgroups, two bowls left/right; no inferred plate on table',
}

def prepare(out):
    out.mkdir(exist_ok=False)
    frozen=json.loads(Path('annotation/v4/eight_shot_curation/frozen_v1/manifest.json').read_text(encoding='utf-8'))
    records=[json.loads(x) for x in Path('annotation/v4/supervised_batch_30/selected_captions.jsonl').read_text(encoding='utf-8').splitlines()]
    records=[{**r,'batch_number':i} for i,r in enumerate(records,1) if r['image_id'] not in frozen['image_ids']]
    assert len(records)==14 and {r['batch_number'] for r in records}==set(QUESTIONS)
    assert not ({r['image_id'] for r in records}&set(frozen['image_ids']))
    prompts={str(n):load_prompt(shots=n) for n in (0,8)}
    for n,p in prompts.items(): (out/f'prompt_{n}.txt').write_text(p,encoding='utf-8')
    write_jsonl(out/'inputs.jsonl',records)
    jobs=[{'job_id':f'{r["batch_number"]:02}_s{shots}_r1','sample_id':r['sample_id'],'shots':shots,'repeat':1} for r in records for shots in [0,8]]
    jobs.extend({'job_id':f'{r["batch_number"]:02}_s8_r2','sample_id':r['sample_id'],'shots':8,'repeat':2} for r in records if r['batch_number'] in [4,14,24,29])
    random.Random(20260910).shuffle(jobs)
    write_json(out/'jobs.json',jobs)
    write_json(out/'semantic_review_plan.json',{'status':'predeclared_assistant_review_criteria_not_human_gold','criteria':QUESTIONS})
    c=load_api_config(API_CONFIG_PATH,timeout=120,retries=1)
    if c.base_url.rstrip('/')!='https://api.deepseek.com': raise ValueError('Pilot is restricted to the configured official DeepSeek endpoint')
    protocol={'prompt_version':PROMPT_VERSION,'prompt_digests':{n:digest(p) for n,p in prompts.items()},'shots_manifest_digest':digest(frozen),
              'inputs_digest':digest(records),'jobs_digest':digest(jobs),'model':c.model,'base_url':c.base_url,'max_tokens':c.max_tokens,
              'thinking':'disabled','temperature':0,'timeout':120,'retries':1,'max_workers':4,'primary_inputs':14,'images':7,
              'planned_logical_calls':32,'maximum_http_attempts':64,'repeat_batch_numbers':[4,14,24,29],'no_cache':True,
              'scope':'Development pilot, disjoint from few-shot image IDs; all cases previously seen during assistant annotation, not a blind human-gold test.'}
    write_json(out/'protocol.json',protocol)
    (out/'checkpoints').mkdir()
    print(json.dumps(protocol,ensure_ascii=False),flush=True)

def report(out):
    jobs=json.loads((out/'jobs.json').read_text(encoding='utf-8'))
    saved={j['job_id']:json.loads((out/'checkpoints'/f'{j["job_id"]}.json').read_text(encoding='utf-8')) for j in jobs if (out/'checkpoints'/f'{j["job_id"]}.json').exists()}
    stats={}
    for shots in [0,8]:
        primary=[r for r in saved.values() if r['shots']==shots and r['repeat']==1]
        ok=[r for r in primary if r['status']=='success']
        stats[str(shots)]={'completed':len(primary),'success':len(ok),'failed':len(primary)-len(ok),
                           'first_attempt_valid':sum(len(r['audit'].get('attempts',[]))==1 for r in ok),
                           'facts':sum(len(r['document']['facts']) for r in ok),'entities':sum(len(r['document']['entities']) for r in ok),
                           'type_counts':dict(Counter(f['type'] for r in ok for f in r['document']['facts']))}
    repeats=[]
    for r in saved.values():
        if r['repeat']==2:
            first=next((x for x in saved.values() if x['sample_id']==r['sample_id'] and x['shots']==8 and x['repeat']==1),None)
            if first and first['status']==r['status']=='success':
                repeats.append({'sample_id':r['sample_id'],'literal_document_equal':first['document']==r['document'],
                                'first_facts':len(first['document']['facts']),'second_facts':len(r['document']['facts'])})
    attempts=[a for r in saved.values() for a in r.get('audit',{}).get('attempts',[])]
    summary={'planned_jobs':len(jobs),'completed_jobs':len(saved),'primary':stats,'repeats':repeats,
             'http_attempts':len(attempts),'prompt_tokens':sum((a.get('usage') or {}).get('prompt_tokens',0) for a in attempts),
             'completion_tokens':sum((a.get('usage') or {}).get('completion_tokens',0) for a in attempts),
             'first_attempt_errors':[{'job':r['job_id'],'error':r['audit']['attempts'][0]['error']} for r in saved.values() if r.get('audit',{}).get('attempts') and r['audit']['attempts'][0].get('error')],
             'all_success':len(saved)==len(jobs) and all(r['status']=='success' for r in saved.values()),
             'meaning':'Structural validity and literal repeatability only, NOT semantic accuracy. Manual semantic review is separate.'}
    write_json(out/'summary.json',summary)
    write_jsonl(out/'results.jsonl',list(saved.values()))
    print(json.dumps(summary,ensure_ascii=False),flush=True)

def execute(out):
    protocol=json.loads((out/'protocol.json').read_text(encoding='utf-8'))
    jobs=json.loads((out/'jobs.json').read_text(encoding='utf-8'))
    records=[json.loads(x) for x in (out/'inputs.jsonl').read_text(encoding='utf-8').splitlines()]
    assert digest(jobs)==protocol['jobs_digest'] and digest(records)==protocol['inputs_digest']
    records={r['sample_id']:r for r in records}
    prompts={n:(out/f'prompt_{n}.txt').read_text(encoding='utf-8') for n in ['0','8']}
    for n,p in prompts.items(): assert digest(p)==protocol['prompt_digests'][n] and p==load_prompt(shots=int(n))
    c=load_api_config(API_CONFIG_PATH,timeout=protocol['timeout'],retries=protocol['retries'])
    assert c.base_url==protocol['base_url']=='https://api.deepseek.com' and c.model==protocol['model'] and c.max_tokens==protocol['max_tokens']
    stop=threading.Event()
    def run(job):
        path=out/'checkpoints'/f'{job["job_id"]}.json'
        if path.exists(): return job['job_id'],'existing'
        if stop.is_set(): return job['job_id'],'cancelled_before_request'
        caption=records[job['sample_id']]['caption']
        client=DeepSeekDecomposer(c,prompt=prompts[str(job['shots'])],bypass_cache=True)
        result={**job,'started_at':datetime.now(timezone.utc).isoformat()}
        try:
            d,a=client.decompose(caption)
            validate_document(d,expected_text=caption,expected_id='caption')
            result.update(status='success',document=d,audit=a)
        except DecompositionError as e:
            result.update(status='failed',error=str(e),audit=getattr(e,'audit',{'attempts':e.attempts}))
            if str(e) in {'API HTTP 400','API HTTP 401','API HTTP 403','API HTTP 404'}: stop.set()
        result['finished_at']=datetime.now(timezone.utc).isoformat()
        write_json(path,result)
        return job['job_id'],result['status']
    pending=[j for j in jobs if not (out/'checkpoints'/f'{j["job_id"]}.json').exists()]
    if pending:
        # One canary before parallel dispatch catches authentication/configuration errors.
        print(*run(pending[0]),flush=True)
        if not stop.is_set():
            with ThreadPoolExecutor(max_workers=protocol['max_workers']) as pool:
                futures=[pool.submit(run,j) for j in pending[1:]]
                for fut in as_completed(futures): print(*fut.result(),flush=True)
    report(out)

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('mode',choices=['prepare','execute','report']); parser.add_argument('--output',type=Path,default=OUT)
    args=parser.parse_args(); {'prepare':prepare,'execute':execute,'report':report}[args.mode](args.output)
