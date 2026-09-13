"""Run the unchanged Final v1 independently for each fixed pair, with bounded concurrency."""
import argparse
import concurrent.futures as cf
import json
import threading
import time
from collections import Counter
from pathlib import Path
from analysis_skeleton.common import read_json,read_jsonl,write_json,new_run,check_frozen,sha
from analysis_skeleton.final_v1.pipeline import execute,make_stages
from analysis_skeleton.m1_lexical import LexicalRecorder
from decomposition.storage import output_lock

ROOT=Path('outputs/coco400_final_v1')
LOCAL=threading.local()


def work(pair):
    if not hasattr(LOCAL,'parser'):
        LOCAL.parser=LexicalRecorder()
        LOCAL.stages=make_stages(read_json(ROOT/'profile.json'),'decomposition/api_config.local.json')
    out=ROOT/'runs'/pair['pair_id']
    try:
        check_frozen(ROOT/'orchestration')
        m=execute(ROOT/'pairs.jsonl',out,[pair['pair_id']],profile=ROOT/'profile.json',
            stages=LOCAL.stages,parser=LOCAL.parser,resume=(out/'manifest.json').exists(),
            condition_id='coco400_greedy_baseline_vs_vista',replicate_id='r1')
        return {'pair_id':pair['pair_id'],'status':'exported','metrics':m}
    except Exception as exc:
        # Preserve all checkpoints. Never delete a started request or resend it.
        return {'pair_id':pair['pair_id'],'status':'runner_exception','exception_type':type(exc).__name__,
                'message':str(exc)[:300] if isinstance(exc,ValueError) else 'see preserved run artifacts'}


def main(resume=False):
    pairs=read_jsonl(ROOT/'pairs.jsonl');assert len(pairs)==400
    protocol=read_json(ROOT/'protocol.json');assert protocol['workers']==8
    if not (ROOT/'orchestration/manifest.json').exists():
        if resume:raise ValueError('no_run_to_resume')
        new_run(ROOT/'orchestration','coco400_frozen_framework_orchestration',
            [ROOT/n for n in ['pairs.jsonl','selection.json','protocol.json','profile.json']],
            {'workers':8,'profile_sha256':sha(ROOT/'profile.json')},[__file__,Path(__file__).with_name('prepare.py')])
    elif not resume:raise ValueError('use_resume_for_existing_run')
    check_frozen(ROOT/'orchestration')
    results=[];started=time.time();log=ROOT/('resume_events.jsonl' if resume else 'run_events.jsonl')
    with output_lock(ROOT/'orchestration'),log.open('a',encoding='utf-8') as stream:
        def accept(record):
            results.append(record)
            stream.write(json.dumps(record,ensure_ascii=False)+'\n');stream.flush()
            print(json.dumps({'complete_pairs':len(results),'total_pairs':400,'pair_id':record['pair_id'],
                'status':record['status'],'new_calls':record.get('metrics',{}).get('new_api_calls_this_invocation'),
                'elapsed_seconds':round(time.time()-started)},ensure_ascii=False),flush=True)
        first=work(pairs[0]);accept(first)
        if first['status']!='exported':raise RuntimeError('first_pair_failure_preserved')
        for checkpoint in (ROOT/'runs'/pairs[0]['pair_id']/'checkpoints').glob('*.json'):
            saved=read_json(checkpoint)['value']
            if saved.get('audit',{}).get('error'):raise RuntimeError('first_pair_transport_failure_preserved')
        with cf.ThreadPoolExecutor(max_workers=8) as pool:
            futures=[pool.submit(work,p) for p in pairs[1:]]
            for f in cf.as_completed(futures):
                accept(f.result())
    summary={'pairs':len(results),'status':dict(Counter(r['status'] for r in results)),
             'new_api_calls':sum(r.get('metrics',{}).get('new_api_calls_this_invocation',0) for r in results),
             'elapsed_seconds':time.time()-started,'runner_exceptions':[r for r in results if r['status']!='exported']}
    write_json(ROOT/('resume_summary.json' if resume else 'run_summary.json'),summary)
    print(json.dumps(summary,ensure_ascii=False),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--resume',action='store_true');a=p.parse_args();main(a.resume)
