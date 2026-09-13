"""Frozen final comparisons; old references preserved and inputs separated."""
import argparse,copy,json,random
from pathlib import Path
from collections import Counter
from analysis_skeleton.common import read_json,read_jsonl,write_json,write_jsonl,sha,check_frozen
from analysis_skeleton.decompose_iteration_v1.batch import execute as batch_execute
from analysis_skeleton.decompose_iteration_v1.experiment import SplitStage
from analysis_skeleton.framework_v2.runtime import SafeStage
from analysis_skeleton.framework_v2.contracts import normalize_document
from analysis_skeleton.framework_v2.scoring import correspondences
from analysis_skeleton.repair_v1.scoring import LemmaScorer
from analysis_skeleton.metrics import aggregate_documents
from analysis_skeleton.evidence_verifier_v2.experiment import FlashStage
from analysis_skeleton.evidence_verifier_v1.compiler import compile_evidence
from analysis_skeleton.evidence_verifier_v1.experiment import score
from .decompose import FinalDecomposeStage,normalize_final
from .visual import FinalVisualStage,prepare_shots,validate
from .context import enrich_legacy,identity as context_identity

ROOT=Path(__file__).parent

def prepare(root,module):
    root=Path(root)
    if root.exists() and any(root.iterdir()):raise ValueError('new_directory_required')
    root.mkdir(parents=True,exist_ok=True)
    if module=='m2':
        refs=read_jsonl('analysis_skeleton/fixtures/expansion20/decompose_cases.jsonl')
        tasks=[{'task_id':r['case_id']+':'+c,'case_id':r['case_id'],'condition':c,'input':{'text':r['text']}} for r in refs for c in ('control','owner')]
        write_jsonl(root/'shots_control.jsonl',SplitStage('control').shots);write_jsonl(root/'shots_owner.jsonl',FinalDecomposeStage().shots)
        protocol={'module':'M2','conditions':['original eight shots','ownership and coverage candidate'],'cases':40,'new_calls':80,
            'factor':'one module prompt/example candidate; not a causal separation of individual sentences','postprocessing':'same raw outputs rescored independently with final deterministic normalizer on both conditions','acceptance':'joint F1 and entity recall improve, attribute F1 not lower, no technical failure','references_unchanged':True}
    else:
        refs=read_jsonl('outputs/legacy_visual_full_flash_v1/references.jsonl');assert len(refs)==579
        tasks=[]
        for r in refs:
            payload=enrich_legacy(r);payload['claim_type']=r['semantic_type']
            for c in ('context','proposition'):
                tasks.append({'task_id':r['case_id']+':'+c,'case_id':r['case_id'],'image_id':r['image_id'],'semantic_type':r['semantic_type'],'condition':c,'input':copy.deepcopy(payload)})
        write_jsonl(root/'shots_context.jsonl',read_jsonl('outputs/evidence_verifier_v1/shots.jsonl'))
        write_jsonl(root/'shots_proposition.jsonl',prepare_shots())
        protocol={'module':'M5','cases':579,'images':39,'new_calls':1158,'conditions':['restored context with previous evidence contract','same restored context with full proposition contract'],
            'factor':'complete proposition contract; input context identical in both fresh conditions','historical_comparison':'previous 579 fragment-context responses are historical only; not fresh paired context ablation',
            'context_identity':context_identity(),'no_reference_in_query':True,'labels_and_statements_unchanged':True,
            'selection':'same 579 cases and exclusions as previous run; no filtering based on predictions','goal':'entity agreement strictly >90%; all-label macro F1, attribute score and confident errors also reported','not_human_gold':True}
    random.Random(20260920 if module=='m2' else 20260921).shuffle(tasks)
    write_jsonl(root/'references.jsonl',refs);write_jsonl(root/'tasks.jsonl',tasks)
    protocol.update(model='deepseek-flash',workers=4,temperature=0,thinking='disabled',retries=0,development_not_holdout=True)
    write_json(root/'protocol.json',protocol);print({'module':module,'tasks':len(tasks)},flush=True)

def run(root,module,resume=False):
    root=Path(root);files=[root/'references.jsonl',root/'protocol.json'];common=['analysis_skeleton/llm.py','analysis_skeleton/framework_v2/runtime.py']
    if module=='m2':
        stages={'control':SafeStage(SplitStage('control')),'owner':SafeStage(FinalDecomposeStage())}
        validators={c:lambda raw,t:normalize_document(raw,t['input']['text'],t['case_id']) for c in stages}
        files += [root/'shots_control.jsonl',root/'shots_owner.jsonl',ROOT/'decompose_rules.txt','analysis_skeleton/prompts/decompose.txt','analysis_skeleton/shots/decompose.jsonl']
        code=[__file__,ROOT/'decompose.py','analysis_skeleton/decompose_iteration_v1/experiment.py','analysis_skeleton/decompose_iteration_v1/value_anchor.py','analysis_skeleton/framework_v2/contracts.py','analysis_skeleton/contracts.py','analysis_skeleton/repair_v1/contracts.py',*common]
    else:
        stages={'context':SafeStage(FlashStage(root/'shots_context.jsonl','sufficiency')),'proposition':SafeStage(FinalVisualStage(root/'shots_proposition.jsonl'))}
        validators={'context':lambda raw,t:compile_evidence(raw,t['semantic_type']),'proposition':lambda raw,t:validate(raw,t['semantic_type'])}
        files += [root/'shots_context.jsonl',root/'shots_proposition.jsonl',ROOT/'visual_rules.txt','analysis_skeleton/evidence_verifier_v1/prompt.txt','analysis_skeleton/evidence_verifier_v2/sufficiency.txt']
        refs=read_jsonl(root/'references.jsonl');files += list({r['input']['image_path'] for r in refs})+list({r['source_pair_file'] for r in refs})
        files += [r['input']['image_path'] for r in read_jsonl(root/'shots_context.jsonl')]
        code=[__file__,ROOT/'context.py',ROOT/'visual.py','analysis_skeleton/m5_verify.py','analysis_skeleton/evidence_verifier_v1/stage.py','analysis_skeleton/evidence_verifier_v1/compiler.py','analysis_skeleton/evidence_verifier_v2/experiment.py',*common]
    batch_execute(root,stages,validators,files,code,resume)

def report_m2(root,rows):
    refs={r['case_id']:normalize_document(r['reference'],r['text'],r['case_id']) for r in read_jsonl(root/'references.jsonl')};scorer=LemmaScorer();scores=[];docs=[];bad=[]
    for r in rows:
        ref=refs[r['case_id']]
        for processing in ('original','anchors','state','final'):
            d=r['prediction'] if processing=='original' else normalize_final(json.loads(r['audit']['raw_content']),ref['text'],r['case_id'],value_anchors=processing in ('anchors','final'),state_support=processing in ('state','final')) if r['status']=='complete' else {'entities':[],'facts':[]}
            if r['status']!='complete':d={'entities':[],'facts':[]}
            s=scorer.score(d,ref);variant=r['condition']+'_'+processing;scores.append({'case_id':r['case_id'],'variant':variant,'score':s})
            docs.append({'case_id':r['case_id'],'variant':variant,'document':d,'source_response_id':r['audit'].get('response_id')})
            mapping=correspondences(d,ref,scorer)
            for f in ref['facts']:
                if f['id'] not in mapping:bad.append({'case_id':r['case_id'],'variant':variant,'kind':'unmatched_reference','fact':f,'text':ref['text']})
            for f in d['facts']:
                if f['id'] not in mapping.values():bad.append({'case_id':r['case_id'],'variant':variant,'kind':'unmatched_prediction','fact':f,'text':ref['text']})
    metrics={v:aggregate_documents([r['score'] for r in scores if r['variant']==v]) for v in sorted({r['variant'] for r in scores})}
    a,b=metrics['control_final'],metrics['owner_final'];metrics['owner_acceptance_passed']=b['joint']['f1']>a['joint']['f1'] and b['entity']['recall']>a['entity']['recall'] and b['attribute']['f1']>=a['attribute']['f1'] and all(r['status']=='complete' for r in rows)
    write_jsonl(root/'documents.jsonl',docs);write_jsonl(root/'per_caption.jsonl',scores);write_jsonl(root/'disagreements.jsonl',bad)
    return metrics

def report_m5(root,rows):
    refs={r['case_id']:r for r in read_jsonl(root/'references.jsonl')};metrics={};paired=[]
    for c in ('context','proposition'):
        rr=[{**r,'reference_label':refs[r['case_id']]['reference_label']} for r in rows if r['condition']==c]
        metrics[c]={k:score([r for r in rr if k=='all' or r['semantic_type']==k],n) for k,n in [('all',579),('entity',508),('attribute',71)]}
        metrics[c]['entity_above_90']=metrics[c]['entity']['agreement']>0.9
        for partition in ('previous_20_image_development','additional_legacy_images'):
            subset=[r for r in rr if refs[r['case_id']]['partition']==partition]
            metrics[c][partition]={k:score([r for r in subset if k=='all' or r['semantic_type']==k],sum(k=='all' or r['semantic_type']==k for r in subset)) for k in ('all','entity','attribute')}
    for cid,ref in refs.items():
        group={r['condition']:r for r in rows if r['case_id']==cid};a,b=group['context'],group['proposition'];assert a['audit']['input']==b['audit']['input']
        paired.append({'case_id':cid,'semantic_type':ref['semantic_type'],'reference':ref['reference_label'],'context':a['prediction'].get('label'),'proposition':b['prediction'].get('label')})
    write_jsonl(root/'paired.jsonl',paired)
    write_jsonl(root/'bad_cases.jsonl',[{**r,'reference':refs[r['case_id']]} for r in rows if r['prediction'].get('label')!=refs[r['case_id']]['reference_label']])
    return metrics

def report(root,module):
    root=Path(root);check_frozen(root/'run');rows=read_jsonl(root/'run/results.jsonl');assert len(rows)==(80 if module=='m2' else 1158)
    metrics=(report_m2 if module=='m2' else report_m5)(root,rows)
    metrics['call_metrics']=read_json(root/'call_metrics.json');metrics['models']=[{'requested':a,'returned':b,'count':n} for (a,b),n in Counter((r['audit']['identity']['model'],r['audit'].get('response_model')) for r in rows).items()]
    metrics['reference_status']='unchanged_assistant_candidates_not_human_gold';write_json(root/'metrics.json',metrics)
    print(json.dumps(metrics,ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run','report']);p.add_argument('--module',choices=['m2','m5'],required=True);p.add_argument('--output',required=True);p.add_argument('--resume',action='store_true');a=p.parse_args()
    if a.action=='run':run(a.output,a.module,a.resume)
    else:globals()[a.action](a.output,a.module)
