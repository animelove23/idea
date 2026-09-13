"""Replace one of eight demonstrations to teach explicit referent partitioning."""
import argparse,copy,json,random
from pathlib import Path
from collections import Counter
from analysis_skeleton.common import read_json,read_jsonl,write_json,write_jsonl,sha,check_frozen
from analysis_skeleton.llm import FewShotStage
from analysis_skeleton.framework_v2.runtime import SafeStage
from analysis_skeleton.framework_v2.contracts import normalize_document
from analysis_skeleton.framework_v2.scoring import correspondences
from analysis_skeleton.repair_v1.scoring import LemmaScorer
from analysis_skeleton.metrics import aggregate_documents
from .batch import execute

ROOT=Path(__file__).parent
MODEL='deepseek-flash'
CASE_PATH=Path('analysis_skeleton/fixtures/expansion20/decompose_cases.jsonl')

def new_shots(original):
    result=copy.deepcopy(original);old=result[6];assert old['example_id']=='d7'
    text='Two dogs stand beside a beautiful car. One dog is black, and the other dog is white.'
    def mention(q):return {'quote':q,'occurrence':0}
    old['input']={'text':text}
    old['output']={'entities':[
        {'id':'e1','name':'dog','mentions':[mention('One dog')]},
        {'id':'e2','name':'dog','mentions':[mention('other dog')]},
        {'id':'e3','name':'car','mentions':[mention('car')]}],
        'attributes':[
            {'id':'a1','entity_id':'e1','slot':'color','value':'black','evidence':[mention('One dog is black')],'value_quotes':[mention('black')]},
            {'id':'a2','entity_id':'e2','slot':'color','value':'white','evidence':[mention('other dog is white')],'value_quotes':[mention('white')]}],
        'excluded':copy.deepcopy(original[6]['output']['excluded'])}
    assert not normalize_document(old['output'],text)['issues']
    return result

class SplitStage(FewShotStage):
    def __init__(self,condition,config='decomposition/api_config.local.json',transport=None):
        super().__init__('decompose',config,transport=transport,model=MODEL)
        if condition not in ('control','split_shot'):raise ValueError('condition')
        if condition=='split_shot':self.shots=new_shots(self.shots)
        from analysis_skeleton.common import digest
        self.identity.update(shots_sha=digest(self.shots),condition=condition,iteration_code_sha=sha(__file__))

def prepare(root):
    root=Path(root)
    if root.exists() and any(root.iterdir()):raise ValueError('new_directory_required')
    root.mkdir(parents=True);cases=read_jsonl(CASE_PATH);assert len(cases)==40
    shots=read_jsonl('analysis_skeleton/shots/decompose.jsonl')
    for c in cases:
        assert not normalize_document(c['reference'],c['text'],c['case_id'])['issues']
        assert c['text'] not in {s['input']['text'] for s in shots+new_shots(shots)}
    write_jsonl(root/'references.jsonl',cases);write_jsonl(root/'shots_control.jsonl',shots);write_jsonl(root/'shots_candidate.jsonl',new_shots(shots))
    tasks=[{'task_id':c['case_id']+':'+cond,'case_id':c['case_id'],'condition':cond,'input':{'text':c['text']}} for c in cases for cond in ('control','split_shot')]
    random.Random(20260918).shuffle(tasks);write_jsonl(root/'tasks.jsonl',tasks)
    write_json(root/'protocol.json',{'factor':'replace only d7 with same opening plus explicit one/other referents and their separate color attributes','unchanged':['system prompt','7 other examples','8-shot count','40 captions','candidate references','normalizer','lemma scorer'],'model':MODEL,'calls':80,'workers':4,'retries':0,'development_not_holdout':True,'acceptance':'joint F1 improves over fresh control, entity recall improves, attribute F1 does not decline, no technical failures; semantic review remains necessary','no_reference_in_request':True})
    historical=read_jsonl('outputs/framework_v2_stage1_release/m2_disagreement_review.jsonl')
    write_json(root/'pre_run_data_audit.json',{'historical_unmatched':{str(k):v for k,v in Counter((r['case_type'],r['fact']['type']) for r in historical).items()},'unmatched_is_not_automatically_an_extraction_error':True,'hypothesis':'explicit local referents often collapsed into a plural entity; d7 currently demonstrates only a plural group','not_changed':['reference labels','canonical entity names','property value matching','visual semantics']})
    print('Prepared M2: 40 captions x 2 conditions.',flush=True)

def run(root,resume=False):
    root=Path(root);stages={c:SafeStage(SplitStage(c)) for c in ('control','split_shot')}
    files=[root/n for n in ('references.jsonl','shots_control.jsonl','shots_candidate.jsonl','protocol.json')]+[CASE_PATH,Path('analysis_skeleton/prompts/decompose.txt'),Path('analysis_skeleton/shots/decompose.jsonl')]
    code=[__file__,'analysis_skeleton/llm.py','analysis_skeleton/framework_v2/runtime.py','analysis_skeleton/framework_v2/contracts.py','analysis_skeleton/repair_v1/contracts.py','analysis_skeleton/contracts.py','analysis_skeleton/repair_v1/scoring.py','analysis_skeleton/framework_v2/scoring.py']
    validators={c:lambda raw,t:normalize_document(raw,t['input']['text'],t['case_id']) for c in stages}
    execute(root,stages,validators,files,code,resume)

def report(root):
    root=Path(root);check_frozen(root/'run');rows=read_jsonl(root/'run/results.jsonl');cases=read_jsonl(root/'references.jsonl')
    assert len(rows)==80 and len({r['task_id'] for r in rows})==80
    refs={c['case_id']:normalize_document(c['reference'],c['text'],c['case_id']) for c in cases};scorer=LemmaScorer();scored=[];bad=[]
    for row in rows:
        ref=refs[row['case_id']];doc=row['prediction'] if row['status']=='complete' else {'entities':[],'facts':[]}
        s=scorer.score(doc,ref);scored.append({'case_id':row['case_id'],'condition':row['condition'],'score':s})
        mapping=correspondences(doc,ref,scorer)
        for f in ref['facts']:
            if f['id'] not in mapping:bad.append({'case_id':row['case_id'],'condition':row['condition'],'kind':'unmatched_reference','fact':f,'text':ref['text']})
        for f in doc['facts']:
            if f['id'] not in mapping.values():bad.append({'case_id':row['case_id'],'condition':row['condition'],'kind':'unmatched_prediction','fact':f,'text':ref['text']})
    metrics={c:aggregate_documents([r['score'] for r in scored if r['condition']==c]) for c in ('control','split_shot')}
    metrics['technical_failures']={c:sum(r['status']!='complete' for r in rows if r['condition']==c) for c in ('control','split_shot')}
    a,b=metrics['control'],metrics['split_shot'];metrics['acceptance_passed']=b['joint']['f1']>a['joint']['f1'] and b['entity']['recall']>a['entity']['recall'] and b['attribute']['f1']>=a['attribute']['f1'] and metrics['technical_failures']['split_shot']==0
    metrics['new_api_calls']=read_json(root/'call_metrics.json')['new_api_calls'];metrics['reference_status']='assistant_candidate_not_human_gold'
    write_json(root/'metrics.json',metrics);write_jsonl(root/'per_caption.jsonl',scored);write_jsonl(root/'disagreements.jsonl',bad)
    print(json.dumps(metrics,ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run','report']);p.add_argument('--output',required=True);p.add_argument('--resume',action='store_true');a=p.parse_args()
    if a.action=='run':run(a.output,a.resume)
    else:globals()[a.action](a.output)
