"""Fresh paired M2-only experiment; references never enter model payloads."""
import argparse,random,json
from pathlib import Path
from analysis_skeleton.common import read_jsonl,write_jsonl,write_json,read_json,sha,check_frozen
from analysis_skeleton.final_v1.decompose import FinalDecomposeStage,normalize_final
from analysis_skeleton.framework_v2.runtime import SafeStage
from analysis_skeleton.framework_v2.contracts import normalize_document
from analysis_skeleton.decompose_iteration_v1.batch import execute
from analysis_skeleton.repair_v1.scoring import LemmaScorer
from analysis_skeleton.metrics import aggregate_documents
from .m2 import NounCenteredStage
from .scoring import diagnostics

ROOT=Path(__file__).parent
def prepare(output):
    root=Path(output)
    if root.exists() and any(root.iterdir()):raise ValueError('new_output_required')
    root.mkdir(parents=True,exist_ok=True)
    refs=[{**r,'partition':'legacy40'} for r in read_jsonl('analysis_skeleton/fixtures/expansion20/decompose_cases.jsonl')]
    refs += [{**r,'partition':'new_development16'} for r in read_jsonl(ROOT/'m2_probes.jsonl')]
    tasks=[{'task_id':r['case_id']+':'+c,'case_id':r['case_id'],'condition':c,'partition':r['partition'],'input':{'text':r['text']}} for r in refs for c in ('baseline','noun')]
    random.Random(20260913).shuffle(tasks)
    write_jsonl(root/'references.jsonl',refs);write_jsonl(root/'tasks.jsonl',tasks)
    write_json(root/'protocol.json',{'cases':len(refs),'calls':len(tasks),'model':'deepseek-flash','shots':8,'calls_per_caption_per_condition':1,
          'factor':'M2 prompt plus eight-shot content as one module-level intervention','normalizer':'unchanged_final_v1','reference_status':'assistant_candidates_not_human_gold',
          'M3_M5_changed':False,'temperature':0,'retries':0,'fresh_both_conditions':True,'primary_metrics':['entity_precision_recall','attribute_precision_recall','ownership_with_judgment_coverage','reference_coverage'],
          'human_text_faithfulness_and_atomicity':'pending_manual_review_not_lexical_pass_rate'})
    print({'prepared_cases':len(refs),'fresh_calls':len(tasks)})

def run(output,config,resume):
    root=Path(output);stages={'baseline':SafeStage(FinalDecomposeStage(config)),'noun':SafeStage(NounCenteredStage(config))}
    validators={c:lambda raw,t:normalize_final(raw,t['input']['text'],t['case_id']) for c in stages}
    files=[root/'references.jsonl',root/'protocol.json',ROOT/'m2_rules.txt',ROOT/'m2_shots.jsonl','analysis_skeleton/prompts/decompose.txt','analysis_skeleton/shots/decompose.jsonl','analysis_skeleton/final_v1/decompose_rules.txt']
    code=[*ROOT.glob('*.py'),'analysis_skeleton/final_v1/decompose.py','analysis_skeleton/decompose_iteration_v1/value_anchor.py','analysis_skeleton/framework_v2/contracts.py','analysis_skeleton/repair_v1/contracts.py','analysis_skeleton/contracts.py','analysis_skeleton/llm.py','analysis_skeleton/framework_v2/runtime.py','decomposition/storage.py']
    execute(root,stages,validators,files,code,resume,workers=4)

def report(output):
    root=Path(output);references={r['case_id']:r for r in read_jsonl(root/'references.jsonl')};scorer=LemmaScorer();scored=[];review=[]
    check_frozen(root/'run')
    results=read_jsonl(root/'run/results.jsonl');tasks=read_jsonl(root/'tasks.jsonl')
    if len(results)!=len(tasks) or {r['task_id'] for r in results}!={r['task_id'] for r in tasks}:raise ValueError('complete_paired_experiment_required')
    for r in results:
        rawref=references[r['case_id']];ref=normalize_document(rawref['reference'],rawref['text'],r['case_id'])
        d=r['prediction'] if r['status']=='complete' else {'entities':[],'facts':[],'issues':[]}
        scored.append({'case_id':r['case_id'],'condition':r['condition'],'partition':r['partition'],'status':r['status'],**diagnostics(d,ref,scorer)})
        for fact in d['facts']:
            owner=next(e for e in d['entities'] if e['id']==fact['entity_id'])
            review.append({'case_id':r['case_id'],'condition':r['condition'],'text':rawref['text'],'fact':fact,'owner':owner,'text_faithful':None,'correct_owner':None,'atomic':None,'reviewer':None})
    metrics={}
    for partition in ('legacy40','new_development16'):
        metrics[partition]={}
        for c in ('baseline','noun'):
            rr=[r for r in scored if r['partition']==partition and r['condition']==c];n=sum(r['ownership_correct']+r['ownership_wrong'] for r in rr);u=sum(r['ownership_unjudged'] for r in rr)
            metrics[partition][c]={'cases':len(rr),'scores':aggregate_documents([r['score'] for r in rr]),'ownership_accuracy_among_judged':sum(r['ownership_correct'] for r in rr)/n if n else None,'ownership_judged':n,'ownership_unjudged':u,'human_text_faithfulness':None,'human_atomicity':None,'technical_failures':sum(r['status']!='complete' for r in rr)}
    write_json(root/'metrics.json',metrics);write_jsonl(root/'per_caption.jsonl',scored);write_jsonl(root/'manual_text_review.jsonl',review)
    print(json.dumps(metrics,ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run','report']);p.add_argument('--output',default='outputs/entity_attribute_v3/m2_ab');p.add_argument('--config',default='decomposition/api_config.local.json');p.add_argument('--resume',action='store_true');a=p.parse_args()
    if a.action=='prepare':prepare(a.output)
    elif a.action=='run':run(a.output,a.config,a.resume)
    else:report(a.output)
