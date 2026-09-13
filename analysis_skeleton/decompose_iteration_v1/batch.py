"""Bounded fresh calls, per-task checkpoints and deterministic resumable output."""
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from collections import Counter
from decomposition.storage import output_lock
from analysis_skeleton.common import read_json,read_jsonl,write_json,write_jsonl,new_run,check_frozen,digest
from analysis_skeleton.framework_v2.runtime import Checkpoints

def execute(root,stages,validators,files,code,resume=False,workers=4):
    root=Path(root);tasks=read_jsonl(root/'tasks.jsonl');out=root/'run'
    identity={'stages':{k:s.identity for k,s in stages.items()},'workers':workers,'fresh':True}
    if resume:
        manifest=check_frozen(out)
        if manifest['config']!=identity:raise ValueError('resume_identity_changed')
    else:
        new_run(out,'bounded_module_batch',[root/'tasks.jsonl',*files],identity,[__file__,*code]);manifest=read_json(out/'manifest.json')
    def work(t):
        check_frozen(out);cp=Checkpoints(out/'checkpoints',digest(manifest),cache_mode='fresh')
        r=cp.call(t['task_id'],stages[t['condition']],t['input'],lambda raw:validators[t['condition']](raw,t))
        record={k:v for k,v in t.items() if k!='input'}
        record.update(status=r['status'],prediction=r.get('value',{}),audit=r.get('audit',{}))
        if 'diagnostic' in r:record['diagnostic']=r['diagnostic']
        return record,cp.new_api_calls,cp.resumed
    with output_lock(out):
        results={};calls=0;restored=0
        def accept(value):
            nonlocal calls,restored
            r,n,s=value;results[r['task_id']]=r;calls+=n;restored+=s
            ordered=[results[t['task_id']] for t in tasks if t['task_id'] in results]
            write_jsonl(out/'results.jsonl',ordered)
            print(f'{len(results)}/{len(tasks)} {r["task_id"]}: {r["status"]}',flush=True)
        first=work(tasks[0]);accept(first)
        if first[0]['audit'].get('error'):raise RuntimeError('first_transport_failure_preserved')
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for future in as_completed([pool.submit(work,t) for t in tasks[1:]]):accept(future.result())
        write_json(root/('resume_metrics.json' if resume else 'call_metrics.json'),{'new_api_calls':calls,'resumed':restored,'records':len(results),'status':dict(Counter(r['status'] for r in results.values()))})
