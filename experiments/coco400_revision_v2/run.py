"""A: deterministic scope; B: fresh alignment; C: targeted independent visual review."""
import argparse,copy,json,threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from analysis_skeleton.common import read_json,read_jsonl,write_json,write_jsonl,write_csv,sha,new_run,check_frozen,digest
from analysis_skeleton.contracts import model_document
from analysis_skeleton.framework_v2.runtime import Checkpoints,SafeStage
from analysis_skeleton.framework_v2.ledger import production
from decomposition.storage import output_lock
from .alignment import AlignStage,validate
from .observation import analyze_pair
from .visual import ReviewStage,validate_typed,merge

SOURCE=Path('outputs/coco400_final_v1');ROOT=Path('outputs/coco400_revision_v2');CODE=Path(__file__).parent
LOCAL=threading.local()


def source_pairs():
    manifest=read_json(SOURCE/'result_manifest.json')['files']
    for p in read_jsonl(SOURCE/'pairs.jsonl'):
        base=SOURCE/'runs'/p['pair_id'];data={}
        for name in ('bundles','verification_queue','verification','denominator_ledger'):
            path=base/(name+'.jsonl');assert sha(path)==manifest[str(path.resolve())]
            data[name]=read_jsonl(path)
        yield p,data


def emit(name,records):
    out=ROOT/name;out.mkdir(exist_ok=True);write_jsonl(out/'pairs.jsonl',records)
    rows=[r['observation'] for r in records];write_jsonl(out/'observation_pairs.jsonl',rows)
    matrices=[]
    for length in ('shorter','unchanged','longer'):
        group=[r for r in rows if r['length_group']==length]
        for h in ('lost','unchanged','gained','mixed'):
            for s in ('unchanged','gained','lost','mixed'):
                ids=[r['pair_id'] for r in group if r['hallucination_change']==h and r['supported_change']==s]
                matrices.append({'length_group':length,'H':h,'S':s,'count':len(ids),'denominator':len(group),
                    'fraction':len(ids)/len(group) if group else None,'pair_ids':ids})
    write_csv(out/'matrix.csv',list(matrices[0]),matrices)
    summary={'pairs':len(rows),'matrix_classifiable':sum(r['matrix_classifiable'] for r in rows),
        'matrix_unresolved':sum(not r['matrix_classifiable'] for r in rows),
        'component_classifiable':{k:sum(len(r['component_states'][k])==1 for r in rows) for k in ('entity_S','entity_H','attribute_S','attribute_H')},
        'quality':dict(sum((Counter(r['quality']) for r in rows),Counter())),
        'attribute_removal':dict(sum((Counter(r['attribute_removal_components']) for r in rows),Counter())),
        'description_changes':dict(Counter(e['change'] for r in records for e in r['bundle']['alignment'].get('description_transitions',[]))),
        'source_labels':'automatic_not_human_gold','semantic_accuracy_measured':False}
    write_json(out/'summary.json',summary);print(name,json.dumps(summary,ensure_ascii=False),flush=True)


def prepare():
    ROOT.mkdir(exist_ok=False);records=[];tasks=[];visual=[]
    for p,data in source_pairs():
        b=data['bundles'][0];ob,ev=analyze_pair(b,data['denominator_ledger'])
        records.append({'pair_id':p['pair_id'],'bundle':b,'queue':data['verification_queue'],'verification':data['verification'],
            'ledger':data['denominator_ledger'],'observation':ob,'events':ev})
        tasks.append({'id':p['pair_id'],'input':{s:model_document(b[s]) for s in ('original','steer')}})
        q={x['claim_id']:x for x in data['verification_queue']};v={x['claim_id']:x for x in data['verification']}
        byref={(ref['side'],ref['fact_id']):x['claim_id'] for x in q.values() for ref in x['refs']}
        targets={k for k,x in v.items() if x['label']=='uncertain'}
        for r in data['denominator_ledger']:
            if r['type']=='attribute' and (r['claim_id'] in targets or (r['visual_label']=='supported' and r['parent_visual_label']!='supported')):
                targets.add(r['claim_id']);parent=byref.get((r['side'],'entity_'+r['entity_id']))
                if parent:targets.add(parent)
        for cid in sorted(targets):
            item=q[cid];evidence=v[cid].get('evidence',{})
            payload={k:copy.deepcopy(item[k]) for k in ('image_path','image_sha256','statement','entity_context','claim_type')}
            payload.update(review_bbox=evidence.get('bbox'),review_focus='locate the intended referent in full image' if item['claim_type']=='entity' else 'resolve the owner, then inspect '+item['slot'])
            visual.append({'id':p['pair_id']+':'+cid,'pair_id':p['pair_id'],'claim_id':cid,'input':payload})
    write_jsonl(ROOT/'align_tasks.jsonl',tasks);write_jsonl(ROOT/'review_tasks.jsonl',visual)
    emit('A_scope_only',records)
    write_json(ROOT/'protocol.json',{'pairs':400,'source_manifest_sha':sha(SOURCE/'result_manifest.json'),
        'stages':['A_scope_only','B_alignment','C_visual_review'],'align_calls':400,'visual_review_calls':len(visual),
        'model':'deepseek-flash','workers':8,'visual_review_rounds':1,'references_sent':False,
        'new_shots':'8 synthetic M3 demonstrations; original 6 visual demonstrations',
        'review_targets':'first-pass uncertain plus their parents and supported-attribute parent conflicts',
        'first_round_raw_labels_immutable':True,'measurements':'coverage is not accuracy; changed semantic contract not directly comparable to old F1'})


def run_calls(kind,resume=False):
    path=ROOT/(kind+'_calls')
    if kind=='probe':tasks=[{'id':x['example_id'],'input':x['input']} for x in read_jsonl(CODE/'align_probes.jsonl')]
    else:tasks=read_jsonl(ROOT/('align_tasks.jsonl' if kind=='align' else 'review_tasks.jsonl'))
    if path.exists():
        if not resume:raise ValueError('existing_run_requires_resume')
        manifest=check_frozen(path)
    else:
        new_run(path,kind,[ROOT/'protocol.json',CODE/'align_shots.jsonl',CODE/'align.txt',CODE/'align_probes.jsonl',
            *([ROOT/('align_tasks.jsonl' if kind=='align' else 'review_tasks.jsonl')] if kind!='probe' else [])],
            {'model':'deepseek-flash','workers':8},list(CODE.glob('*.py')))
        manifest=read_json(path/'manifest.json')
    def work(t):
        if not hasattr(LOCAL,kind):setattr(LOCAL,kind,ReviewStage('outputs/final_v1_release/visual_routes.json') if kind=='review' else SafeStage(AlignStage()))
        stage=getattr(LOCAL,kind);cp=Checkpoints(path/'checkpoints',digest(manifest))
        validator=(lambda raw:validate_typed(raw,t['input']['claim_type'])) if kind=='review' else (lambda raw:validate(raw,**t['input']))
        rec=cp.call(t['id'],stage,t['input'],validator)
        return {'id':t['id'],'result':rec,'new_calls':cp.new_api_calls}
    results=[]
    with output_lock(path),ThreadPoolExecutor(max_workers=8) as pool:
        for f in as_completed([pool.submit(work,t) for t in tasks]):
            results.append(f.result())
            if len(results)%20==0 or len(results)==len(tasks):print(kind,len(results),'/',len(tasks),flush=True)
    write_jsonl(path/'results.jsonl',results)
    print({'kind':kind,'status':dict(Counter(r['result']['status'] for r in results)),'new_calls':sum(r['new_calls'] for r in results)},flush=True)


def rebuild(visual=False):
    aligned={r['id']:r['result'] for r in read_jsonl(ROOT/'align_calls/results.jsonl')}
    reviews={r['id']:r['result'] for r in read_jsonl(ROOT/'review_calls/results.jsonl')} if visual else {}
    result=[];review_audit=[]
    for original in read_jsonl(ROOT/'A_scope_only/pairs.jsonl'):
        r=copy.deepcopy(original);pid=r['pair_id'];b=r['bundle'];ar=aligned[pid]
        if ar['status']=='complete':b['alignment']=ar['value']
        else:b['alignment']=validate({'entities':[],'alignments':[]},b['original'],b['steer'])
        for v in r['verification']:
            key=pid+':'+v['claim_id']
            if key in reviews:
                old=v.get('label');merged=merge(v,reviews[key]);v.update(merged)
                review_audit.append({'pair_id':pid,'claim_id':v['claim_id'],'before':old,'after':v['label'],'review_status':reviews[key]['status']})
        # A formerly shared query cannot establish truth for two newly non-equivalent referents.
        for q in r['queue']:
            if len(q['refs'])<2:continue
            refs={(x['side'],x['fact_id']) for x in q['refs']}
            safe=any(e['status']=='retained' and refs=={(s,f) for s in ('original','steer') for f in e[s]} for e in b['alignment']['alignments'])
            if not safe:
                v=next(v for v in r['verification'] if v['claim_id']==q['claim_id'])
                v.update(label='uncertain',reason='old_shared_visual_query_requires_independent_rebinding')
        ledger,_,_,_=production(b,r['queue'],r['verification']);r['ledger']=ledger
        r['observation'],r['events']=analyze_pair(b,ledger);result.append(r)
    emit('C_visual_review' if visual else 'B_alignment',result)
    if visual:write_jsonl(ROOT/'C_visual_review/review_transitions.jsonl',review_audit)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','probe','align','review','B','C']);p.add_argument('--resume',action='store_true');a=p.parse_args()
    if a.action=='prepare':prepare()
    elif a.action in ('probe','align','review'):run_calls(a.action,a.resume)
    else:rebuild(a.action=='C')
