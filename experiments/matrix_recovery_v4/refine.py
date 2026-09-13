"""Audited local dependency correction, disjunction safeguard, one format repair."""
import argparse,copy,json,re,threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from collections import Counter
from analysis_skeleton.common import read_jsonl,read_json,write_jsonl,write_json,new_run,check_frozen,digest,sha
from analysis_skeleton.contracts import model_document
from analysis_skeleton.framework_v2.runtime import Checkpoints,SafeStage
from decomposition.storage import output_lock
from . import run
from .json_entry import AlignStage
from .stages import validate

ROOT=Path('outputs/matrix_recovery_v4_refined')
PARENT=Path('outputs/matrix_recovery_v4_json')
LOCAL=threading.local()


def alternatives(doc):
    """Only exact adjacent mention spans separated by explicit or; never guessed objects."""
    edges=[]
    for a in doc['entities']:
        for b in doc['entities']:
            if a['id']==b['id']:continue
            for x in a['mentions']:
                for y in b['mentions']:
                    if not (0<=x.get('start',-1)<x.get('end',-1)<=y.get('start',-1)<y.get('end',-1)<=len(doc['text'])):continue
                    if doc['text'][x['start']:x['end']]!=x['quote'] or doc['text'][y['start']:y['end']]!=y['quote']:continue
                    between=doc['text'][x['end']:y['start']]
                    if re.fullmatch(r'\s+(?:or|and/or)\s+(?:(?:a|an|the)\s+)?',between,re.I):
                        edges.append((a['id'],b['id'],doc['text'][x['start']:y['end']]))
    return sorted(set(edges))


def guarded(raw,original,steer):
    raw=copy.deepcopy(raw);audit=[]
    if not isinstance(raw,dict) or set(raw)!={'entities','attributes'} or any(not isinstance(raw[k],list) for k in raw):
        return validate(raw,original,steer),audit
    touched={s:set() for s in ('original','steer')}
    for s,d in [('original',original),('steer',steer)]:
        for a,b,quote in alternatives(d):
            touched[s].update((a,b));audit.append({'policy':'explicit_disjunction_is_not_two_asserted_objects','side':s,'entities':[a,b],'quote':quote})
    # Quarantine the entire connected correspondence component, preserving all IDs.
    selected=set();changed=True
    while changed:
        changed=False
        for i,e in enumerate(raw['entities']):
            if not isinstance(e,dict):continue
            if any(isinstance(e.get(s),list) and set(x for x in e[s] if isinstance(x,str))&touched[s] for s in touched):
                if i not in selected:selected.add(i);changed=True
                for s in touched:
                    if isinstance(e.get(s),list):touched[s].update(x for x in e[s] if isinstance(x,str))
    if any(touched.values()):
        raw['entities']=[e for i,e in enumerate(raw['entities']) if i not in selected]+[
            {'original':sorted(touched['original']),'steer':sorted(touched['steer']),'status':'unresolved',
             'description_change':'unresolved','reason':'explicit_disjunction_extraction_ambiguity'}]
    uncertain={s:set() for s in touched}
    for e in raw['entities']:
        if isinstance(e,dict) and e.get('status')=='unresolved':
            for s in uncertain:uncertain[s].update(x for x in e.get(s,[]) if isinstance(x,str))
    facts={s:{f['id']:f for f in d['facts']} for s,d in [('original',original),('steer',steer)]}
    for row in raw['attributes']:
        if not isinstance(row,dict) or not all(isinstance(row.get(s),list) for s in touched):continue
        dependent=any(isinstance(fid,str) and facts[s].get(fid,{}).get('entity_id') in uncertain[s] for s in touched for fid in row[s])
        if dependent and row.get('status')!='unresolved':
            audit.append({'policy':'unresolved_owner_requires_unresolved_attribute','before':copy.deepcopy(row)})
            row.update(status='unresolved',reason='subject_identity_unresolved')
    result=validate(raw,original,steer);result['v4_dependency_guard']=audit
    return result,audit


def prepare():
    ROOT.mkdir(exist_ok=False)
    rs=read_jsonl(run.SOURCE);pred={r['id']:r['result'] for r in read_jsonl(PARENT/'align_calls/results.jsonl')}
    tasks=[];local=[];audits=[]
    for r in rs:
        b=r['bundle'];saved=pred[r['pair_id']]
        raw=json.loads(saved['audit']['raw_content']) if saved['status']=='complete' else {'entities':[],'attributes':[]}
        checked,audit=guarded(raw,b['original'],b['steer'])
        local.append({'id':r['pair_id'],'raw':raw,'value':checked});audits.extend({'pair_id':r['pair_id'],**x} for x in audit)
        if any(e['status']=='unresolved' and e.get('reason','').startswith('technical') for e in checked['alignments']):
            tasks.append({'id':r['pair_id'],'input':{s:model_document(b[s]) for s in ('original','steer')},
                'prior_response':raw,'validation_issues':checked['issues']})
    write_jsonl(ROOT/'local_results.jsonl',local);write_jsonl(ROOT/'local_audit.jsonl',audits);write_jsonl(ROOT/'repair_tasks.jsonl',tasks)
    write_json(ROOT/'protocol.json',{'source_sha':sha(run.SOURCE),'first_align_results_sha':sha(PARENT/'align_calls/results.jsonl'),
        'repair_calls':len(tasks),'max_repair_rounds':1,'model':'deepseek-flash','shots':8,
        'selection':'technical unresolved after deterministic dependency correction, not score or gold labels',
        'local_guards':['explicit disjunction quarantine','unresolved owner propagation'],'reference_answers_sent':False})
    print({'local_guards':len(audits),'repair_tasks':len(tasks)},flush=True)


class RepairStage(AlignStage):
    def messages(self,payload):
        out=super().messages(payload)
        out[0]['content']+='\nThis is the only repair pass. The previous response is an untrusted draft, not a reference answer. Correct duplicate/missing IDs, invalid shapes, slot/owner mismatches and invalid source quotes identified by validation. Preserve genuine semantic uncertainty; do not invent correspondence to eliminate validation issues. Return the complete entities and attributes JSON tables, including unaffected IDs.'
        return out
    def __init__(self):
        super().__init__();self.identity.update(repair_rounds=1,repair_code_sha=sha(__file__))


def calls(resume=False):
    out=ROOT/'repair_calls';tasks=read_jsonl(ROOT/'repair_tasks.jsonl')
    if out.exists():
        if not resume:raise ValueError('resume_required')
        manifest=check_frozen(out)
    else:
        new_run(out,'bounded_format_repair',[ROOT/'repair_tasks.jsonl',ROOT/'protocol.json',ROOT/'local_results.jsonl',
            'experiments/entity_attribute_v3/m3_shots.jsonl','experiments/entity_attribute_v3/m3_rules.txt'],
            {'calls':len(tasks),'model':'deepseek-flash','rounds':1},[*Path(__file__).parent.glob('*.py'),
            *Path('experiments/entity_attribute_v3').glob('*.py'),*Path('analysis_skeleton/framework_v2').glob('*.py')])
        manifest=read_json(out/'manifest.json')
    def work(t):
        if not hasattr(LOCAL,'stage'):LOCAL.stage=SafeStage(RepairStage())
        payload={**t['input'],'previous_response':t['prior_response'],'validation_issues':t['validation_issues']}
        cp=Checkpoints(out/'checkpoints',digest(manifest))
        result=cp.call(t['id'],LOCAL.stage,payload,lambda raw:guarded(raw,**t['input'])[0])
        return {'id':t['id'],'result':result,'new_calls':cp.new_api_calls}
    rows=[]
    with output_lock(out),ThreadPoolExecutor(max_workers=8) as pool:
        for f in as_completed([pool.submit(work,t) for t in tasks]):
            rows.append(f.result())
            if len(rows)%20==0 or len(rows)==len(tasks):print('repair',len(rows),'/',len(tasks),flush=True)
    write_jsonl(out/'results.jsonl',rows);write_json(out/'summary.json',{'requests':len(rows),'new_calls':sum(r['new_calls'] for r in rows),'status':dict(Counter(r['result']['status'] for r in rows))})


def build():
    local={r['id']:r['value'] for r in read_jsonl(ROOT/'local_results.jsonl')}
    repair={r['id']:r['result'] for r in read_jsonl(ROOT/'repair_calls/results.jsonl')}
    before=[];final=[]
    for r in read_jsonl(run.SOURCE):
        r['bundle']['alignment']=local[r['pair_id']];baseline=copy.deepcopy(r)
        run.split_queue(baseline);before.append(run.recompute(baseline))
        result=repair.get(r['pair_id'])
        if result and result['status']=='complete':r['bundle']['alignment']=result['value']
        run.split_queue(r);final.append(run.recompute(r))
    run.ROOT=ROOT;run.emit('B_local',before)
    # Reuse the established binding and review-task builder by a frozen normalized result file.
    (ROOT/'align_calls').mkdir(exist_ok=True)
    write_jsonl(ROOT/'align_calls/results.jsonl',[{'id':r['pair_id'],'result':{'status':'complete','value':r['bundle']['alignment']}} for r in final])
    write_json(ROOT/'align_calls/README.json',{'not_model_calls':True,'source':'first 400 predictions, local guards, bounded repair; actual calls stored in parent/align_calls and repair_calls'})
    run.align_result()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','repair','B','visual','C']);p.add_argument('--resume',action='store_true');a=p.parse_args()
    if a.action=='prepare':prepare()
    elif a.action=='repair':calls(a.resume)
    elif a.action=='B':build()
    else:
        run.ROOT=ROOT
        if a.action=='visual':run.calls('visual',a.resume)
        else:run.visual_result()
