"""Fixed 400-pair sequential intervention, with frozen M2 and separately scored M3/M5."""
import argparse, copy, json, threading
from pathlib import Path
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from analysis_skeleton.common import read_jsonl,read_json,write_jsonl,write_json,new_run,check_frozen,digest,sha
from analysis_skeleton.contracts import model_document
from analysis_skeleton.framework_v2.runtime import Checkpoints,SafeStage
from analysis_skeleton.framework_v2.ledger import production
from analysis_skeleton.final_v1.pipeline import enrich_queue
from analysis_skeleton.final_v1.routing import routing_inputs,validate_typed
from analysis_skeleton.m4_queue import statement
from decomposition.storage import output_lock
from experiments.coco400_revision_v2.visual import merge
from experiments.coco400_revision_v2.observation import analyze_pair
from experiments.coco400_revision_v2 import run as exporter
from .stages import AlignStage,VisualStage,validate

ROOT=Path('outputs/matrix_recovery_v4')
SOURCE=Path('outputs/coco400_revision_v2_guard/C_reviewed/pairs.jsonl')
ROUTES='outputs/final_v1_release/visual_routes.json'
CODE=Path(__file__).parent
LOCAL=threading.local()


def prepare():
    ROOT.mkdir(exist_ok=False)
    rs=read_jsonl(SOURCE)
    assert len(rs)==400 and len({r['pair_id'] for r in rs})==400
    write_jsonl(ROOT/'align_tasks.jsonl',[{'id':r['pair_id'],'input':{s:model_document(r['bundle'][s]) for s in ('original','steer')}} for r in rs])
    probes=read_jsonl('experiments/entity_attribute_v3/m3_probes.jsonl')
    write_jsonl(ROOT/'probe_tasks.jsonl',[{'id':r['example_id'],'input':r['input']} for r in probes])
    write_json(ROOT/'protocol.json',{'source':str(SOURCE),'source_sha':sha(SOURCE),'pairs':400,'target':360,
        'baseline_classifiable':269,'model':'deepseek-flash','M2':'frozen previous 800 decompositions',
        'M3':'all 400 new calls, eight fixed v3 shots, single entity decision plus completeness/identity rules',
        'M5':'one new-condition blind review per uncertain/pending/conflicting claim, and newly split visual bindings',
        'visual_shots':6,'per_condition_automatic_retries':0,'references_sent':False,
        'statistics':'unchanged strict v2 matrix rules; no uncertain-to-negative coercion; all 400 denominator',
        'accuracy':'coverage is not independent semantic accuracy; development dataset reused'})
    print({'prepared':400,'probes':len(probes)},flush=True)


def calls(kind,resume=False):
    taskfile=ROOT/(kind+'_tasks.jsonl');tasks=read_jsonl(taskfile);out=ROOT/(kind+'_calls')
    if out.exists():
        if not resume:raise ValueError('existing_calls_require_resume')
        manifest=check_frozen(out)
    else:
        inputs=[taskfile,ROOT/'protocol.json',SOURCE,
            'experiments/entity_attribute_v3/m3_rules.txt','experiments/entity_attribute_v3/m3_shots.jsonl',*routing_inputs(ROUTES)]
        deps=[*CODE.glob('*.py'),*Path('experiments/entity_attribute_v3').glob('*.py'),
            *Path('experiments/coco400_revision_v2').glob('*.py'),*Path('analysis_skeleton/framework_v2').glob('*.py'),
            *Path('analysis_skeleton/final_v1').glob('*.py'),*Path('analysis_skeleton/evidence_verifier_v1').glob('*.py'),
            *Path('analysis_skeleton/evidence_verifier_v2').glob('*.py'),Path('analysis_skeleton/llm.py'),
            Path('analysis_skeleton/m5_verify.py'),Path('experiments/coco400_v1/observe.py')]
        new_run(out,kind,inputs,{'workers':8,'calls':len(tasks),'model':'deepseek-flash'},deps)
        manifest=read_json(out/'manifest.json')
    def work(t):
        if not hasattr(LOCAL,kind):setattr(LOCAL,kind,VisualStage(ROUTES) if kind=='visual' else SafeStage(AlignStage()))
        stage=getattr(LOCAL,kind);cp=Checkpoints(out/'checkpoints',digest(manifest))
        validator=(lambda raw:validate_typed(raw,t['input']['claim_type'])) if kind=='visual' else (lambda raw:validate(raw,**t['input']))
        rec=cp.call(t['id'],stage,t['input'],validator)
        return {'id':t['id'],'result':rec,'new_calls':cp.new_api_calls,'resumed':cp.resumed}
    rows=[]
    with output_lock(out),ThreadPoolExecutor(max_workers=8) as pool:
        for future in as_completed([pool.submit(work,t) for t in tasks]):
            rows.append(future.result())
            if len(rows)%25==0 or len(rows)==len(tasks):print(kind,len(rows),'/',len(tasks),flush=True)
    rows.sort(key=lambda r:r['id']);write_jsonl(out/'results.jsonl',rows)
    summary={'requests':len(rows),'new_calls':sum(r['new_calls'] for r in rows),'status':dict(Counter(r['result']['status'] for r in rows))}
    write_json(out/'summary.json',summary);print(summary,flush=True)


def emit(name,rows):
    exporter.ROOT=ROOT;exporter.emit(name,rows)


def split_queue(r):
    """Only the exact original query referent may retain a previous visual response."""
    b=r['bundle'];vs={v['claim_id']:v for v in r['verification']};qq=[];vv=[]
    for q in r['queue']:
        refs={(x['side'],x['fact_id']) for x in q['refs']}
        safe=len(refs)==1 or any(e['status']=='retained' and refs=={(s,f) for s in ('original','steer') for f in e[s]} for e in b['alignment']['alignments'])
        if safe:qq.append(q);vv.append(vs[q['claim_id']]);continue
        source=q.get('final_context_audit',{}).get('query_source_ref')
        for ref in q['refs']:
            nq=copy.deepcopy(q);nq['refs']=[ref];nq['claim_id']=digest({'pair':r['pair_id'],'v4_refs':[ref]})[:24]
            d=b[ref['side']];f=next(f for f in d['facts'] if f['id']==ref['fact_id']);e=next(e for e in d['entities'] if e['id']==f['entity_id'])
            nq['statement']=statement(f,e);nq['token_links']=[t for t in q['token_links'] if t['side']==ref['side'] and t['fact_id']==ref['fact_id']]
            nq=enrich_queue([nq],{s:b[s] for s in ('original','steer')})[0]
            v=copy.deepcopy(vs[q['claim_id']]);v.update(claim_id=nq['claim_id'],source_old_claim_id=q['claim_id'])
            same=ref==source and nq['statement']==q['statement'] and nq['entity_context']==q['entity_context']
            if not same:v.update(label=None,reason='new_independent_binding_required',needs_rebinding=True)
            qq.append(nq);vv.append(v)
    r['queue']=qq;r['verification']=vv


def recompute(r):
    r['ledger'],_,_,_=production(r['bundle'],r['queue'],r['verification'])
    r['observation'],r['events']=analyze_pair(r['bundle'],r['ledger'])
    return r


def align_result():
    saved={r['id']:r['result'] for r in read_jsonl(ROOT/'align_calls/results.jsonl')}
    source=read_jsonl(SOURCE)
    assert set(saved)=={r['pair_id'] for r in source}
    rows=[];tasks=[]
    for r in source:
        result=saved[r['pair_id']]
        r['bundle']['alignment']=result['value'] if result['status']=='complete' else validate({'entities':[],'attributes':[]},r['bundle']['original'],r['bundle']['steer'])
        split_queue(r);recompute(r);rows.append(r)
        qm={q['claim_id']:q for q in r['queue']};vm={v['claim_id']:v for v in r['verification']}
        byref={(ref['side'],ref['fact_id']):q['claim_id'] for q in r['queue'] for ref in q['refs']}
        targets={k for k,v in vm.items() if v['label'] in ('uncertain','pending',None)}
        for e in r['events']:
            if e['action']=='retained_conflict':targets.update(byref[tuple(ref)] for ref in e['refs'])
        for l in r['ledger']:
            if l['type']=='attribute' and (l['claim_id'] in targets or (l['visual_label']=='supported' and l['parent_visual_label']!='supported')):
                targets.add(l['claim_id']);parent=byref.get((l['side'],'entity_'+l['entity_id']))
                if parent:targets.add(parent)
        for cid in sorted(targets):
            q=qm[cid];v=vm[cid]
            payload={k:copy.deepcopy(q[k]) for k in ('image_path','image_sha256','statement','entity_context','claim_type')}
            payload.update(review_bbox=None if v.get('needs_rebinding') else v.get('evidence',{}).get('bbox'),
                review_focus='inspect requested entity identity, independent of neighboring assertions' if q['claim_type']=='entity' else 'locate owner and inspect '+q['slot'])
            tasks.append({'id':r['pair_id']+':'+cid,'pair_id':r['pair_id'],'claim_id':cid,'purpose':'new_binding' if v.get('needs_rebinding') else 'new_condition_review','input':payload})
    emit('B_alignment',rows);write_jsonl(ROOT/'visual_tasks.jsonl',tasks)
    print({'visual_tasks':len(tasks),'images':len({t['pair_id'] for t in tasks})},flush=True)


def visual_result():
    tasks=read_jsonl(ROOT/'visual_tasks.jsonl');saved={r['id']:r['result'] for r in read_jsonl(ROOT/'visual_calls/results.jsonl')}
    assert set(saved)=={t['id'] for t in tasks}
    rows=read_jsonl(ROOT/'B_alignment/pairs.jsonl');transitions=[]
    for r in rows:
        for v in r['verification']:
            key=r['pair_id']+':'+v['claim_id']
            if key not in saved:continue
            before=v['label'];first=copy.deepcopy(v)
            if first['label']=='pending':first['label']='uncertain'
            merged=merge(first,saved[key]);v.update(merged)
            v['v4_review_audit']=saved[key].get('audit',{})
            transitions.append({'pair_id':r['pair_id'],'claim_id':v['claim_id'],'before':before,'after':v['label'],'status':saved[key]['status']})
        recompute(r)
    emit('C_visual',rows);write_jsonl(ROOT/'C_visual/transitions.jsonl',transitions)


def report():
    old={r['pair_id']:r for r in read_jsonl(SOURCE)};rows=read_jsonl(ROOT/'C_visual/pairs.jsonl')
    changes=[];bad=[]
    for r in rows:
        prev=old[r['pair_id']];o=r['observation'];b=r['bundle']
        changes.append({'pair_id':r['pair_id'],'before':prev['observation']['matrix_classifiable'],'after':o['matrix_classifiable'],
            'H_before':prev['observation']['hallucination_change'],'H_after':o['hallucination_change'],
            'S_before':prev['observation']['supported_change'],'S_after':o['supported_change']})
        if not o['matrix_classifiable']:
            bad.append({'pair_id':r['pair_id'],'original':b['original']['text'],'steer':b['steer']['text'],
                'candidate_states':o['candidate_states'],'quality':o['quality'],'missing_components':o['missing_component_types'],
                'unresolved_alignment':[e for e in b['alignment']['alignments'] if e['status']=='unresolved'],
                'uncertain_visual':[{'claim_id':v['claim_id'],'label':v['label'],'reason':v.get('reason'),'evidence':v.get('evidence')} for v in r['verification'] if v['label'] in ('uncertain','pending',None)],
                'M2_issues':{s:b[s]['issues'] for s in ('original','steer')}})
    summary={'pairs':400,'before':269,'after':sum(x['after'] for x in changes),'target':360,
        'recovered':sum(not x['before'] and x['after'] for x in changes),'regressed':sum(x['before'] and not x['after'] for x in changes),
        'both_decided_cell_changed':sum(x['before'] and x['after'] and (x['H_before'],x['S_before'])!=(x['H_after'],x['S_after']) for x in changes),
        'facts':sum(len(r['ledger']) for r in rows),'independent_accuracy_measured':False}
    summary['rate']=summary['after']/400;summary['target_reached']=summary['after']>=360
    summary['calls']={k:read_json(ROOT/(k+'_calls/summary.json')) for k in ('probe','align','visual')}
    for k in ('probe','align','visual'):check_frozen(ROOT/(k+'_calls'))
    write_json(ROOT/'comparison.json',summary);write_jsonl(ROOT/'pair_transitions.jsonl',changes);write_jsonl(ROOT/'remaining_cases.jsonl',bad)
    print(summary,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','probe','align','visual','B','C','report']);p.add_argument('--resume',action='store_true');a=p.parse_args()
    if a.action=='prepare':prepare()
    elif a.action in ('probe','align','visual'):calls(a.action,a.resume)
    elif a.action=='B':align_result()
    elif a.action=='C':visual_result()
    else:report()
