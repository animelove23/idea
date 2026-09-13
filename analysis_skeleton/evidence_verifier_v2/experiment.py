"""One prompt clarification factor; fresh paired Flash calls and frozen artifacts."""
import argparse,copy,json,random
from collections import Counter
from pathlib import Path
from decomposition.storage import output_lock
from analysis_skeleton.common import read_json,read_jsonl,write_json,write_jsonl,new_run,check_frozen,sha,digest
from analysis_skeleton.m5_verify import VisualStage
from analysis_skeleton.framework_v2.runtime import SafeStage,Checkpoints
from analysis_skeleton.evidence_verifier_v1.stage import EvidenceStage,make_evidence_shots
from analysis_skeleton.evidence_verifier_v1.compiler import compile_evidence
from analysis_skeleton.evidence_verifier_v1.experiment import score

ROOT=Path(__file__).parent
MODEL='deepseek-flash'
OLD=Path('analysis_skeleton/evidence_verifier_v1')

class FlashStage(EvidenceStage):
    def __init__(self,shots_path,condition,config_path='decomposition/api_config.local.json',transport=None):
        if condition not in ('control','sufficiency'):raise ValueError('unknown_condition')
        VisualStage.__init__(self,config_path,transport=transport,model=MODEL)
        self.rules_path=OLD/'prompt.txt';self.rules=self.rules_path.read_text(encoding='utf-8')
        rows=read_jsonl(shots_path)
        if rows!=make_evidence_shots(self.shots):raise ValueError('demonstrations_changed')
        self.shots=rows;self.shots_path=shots_path
        if condition=='sufficiency':self.rules+='\n'+(ROOT/'sufficiency.txt').read_text(encoding='utf-8')
        self.identity.update(prompt_sha=digest(self.rules),shots_sha=sha(shots_path),
                             evidence_contract='evidence_verifier_v1',compiler_sha=sha(OLD/'compiler.py'),
                             experiment_code_sha=sha(__file__),condition=condition,explicit_model=MODEL)

def prepare(root):
    root=Path(root)
    if (root/'protocol.json').exists():raise ValueError('already_prepared')
    root.mkdir(parents=True,exist_ok=True)
    source=Path('outputs/evidence_verifier_v1')
    for name in ('inputs.jsonl','references.jsonl','shots.jsonl'):
        write_jsonl(root/name,read_jsonl(source/name))
    rows=read_jsonl(root/'inputs.jsonl');shots=read_jsonl(root/'shots.jsonl')
    assert len(rows)==60 and len(shots)==6
    assert not {r['input']['image_sha256'] for r in rows}&{r['input']['image_sha256'] for r in shots}
    order=[(r['case_id'],c) for r in rows for c in ('control','sufficiency')]
    random.Random(20260917).shuffle(order);write_json(root/'order.json',order)
    write_json(root/'protocol.json',{'factor':'prompt clarification of claim-specific evidence sufficiency and absence scope',
        'explicit_model':MODEL,'conditions':['control','sufficiency'],'fresh_calls':120,
        'unchanged':['60 queries','reference labels','six image/question/answer demonstrations','evidence schema','compiler v2','original image only','temperature=0','thinking=disabled'],
        'no_roi':True,'development_not_holdout':True,'references_are_assistant_candidates':True,
        'acceptance':{'entity_correct_minimum':37,'entity_denominator':41,'confident_entity_errors_no_increase':True,'attribute_correct_no_decrease':True,'technical_failures':0},
        'model_comparison':False,'reason':'Previous visual requests already explicitly used Flash; this compares prompt versions on Flash.'})
    print('Prepared 60 fixed queries, 6 unchanged shots, 120 calls.',flush=True)

def run(root,resume=False):
    root=Path(root);stages={c:SafeStage(FlashStage(root/'shots.jsonl',c)) for c in ('control','sufficiency')}
    rows=read_jsonl(root/'inputs.jsonl');lookup={r['case_id']:r for r in rows};order=read_json(root/'order.json')
    inputs=[root/n for n in ('inputs.jsonl','references.jsonl','shots.jsonl','protocol.json','order.json')]+[ROOT/'sufficiency.txt',OLD/'prompt.txt',Path('analysis_skeleton/shots/verify.jsonl')]
    inputs += [r['input']['image_path'] for r in rows]+[r['input']['image_path'] for r in read_jsonl(root/'shots.jsonl')]
    code=[__file__,OLD/'stage.py',OLD/'compiler.py',OLD/'experiment.py','analysis_skeleton/m5_verify.py','analysis_skeleton/llm.py','analysis_skeleton/framework_v2/runtime.py','decomposition/config.py','decomposition/semantic_decomposer.py']
    identity={c:s.identity for c,s in stages.items()};out=root/'run'
    if resume:
        manifest=check_frozen(out)
        if manifest['config']!=identity:raise ValueError('resume_identity_changed')
    else:
        new_run(out,'evidence_verifier_v2',inputs,identity,code);manifest=read_json(out/'manifest.json')
    with output_lock(out):
        cp=Checkpoints(out/'checkpoints',digest(manifest),cache_mode='fresh');results=[]
        for i,(cid,c) in enumerate(order):
            check_frozen(out);r=lookup[cid];payload={**copy.deepcopy(r['input']),'claim_type':r['semantic_type']}
            result=cp.call(cid+':'+c,stages[c],payload,lambda raw,kind=r['semantic_type']:compile_evidence(raw,kind))
            record={k:r[k] for k in ('case_id','image_id','semantic_type')}
            record.update(condition=c,status=result['status'],prediction=result.get('value',{}),audit=result.get('audit',{}))
            if 'diagnostic' in result:record['diagnostic']=result['diagnostic']
            results.append(record);write_jsonl(out/'results.jsonl',results)
            print(f'{i+1}/120 {cid} {c}: {record["prediction"].get("label",record["status"])}',flush=True)
            if i==0 and record['status']!='complete':raise RuntimeError('first_call_failed')
        write_json(root/('resume_metrics.json' if resume else 'call_metrics.json'),{'new_api_calls':cp.new_api_calls,'resumed':cp.resumed,'records':len(results),'status':dict(Counter(r['status'] for r in results))})

def report(root):
    root=Path(root);check_frozen(root/'run');rows=read_jsonl(root/'run/results.jsonl')
    refs={r['case_id']:r for r in read_jsonl(root/'references.jsonl')}
    if len(rows)!=120 or len({(r['case_id'],r['condition']) for r in rows})!=120:raise ValueError('incomplete_pairs')
    metrics={};pairs=[]
    for c in ('control','sufficiency'):
        rr=[{**r,'reference_label':refs[r['case_id']]['reference_label']} for r in rows if r['condition']==c]
        metrics[c]={k:score([r for r in rr if k=='all' or r['semantic_type']==k],n) for k,n in [('all',60),('entity',41),('attribute',19)]}
    for cid,ref in refs.items():
        group={r['condition']:r for r in rows if r['case_id']==cid};a,b=group['control'],group['sufficiency']
        assert a['audit']['input']==b['audit']['input']
        pairs.append({'case_id':cid,'semantic_type':a['semantic_type'],'reference':ref['reference_label'],
            'control':a['prediction'].get('label'),'sufficiency':b['prediction'].get('label'),
            'control_evidence':a['prediction'].get('evidence'),'sufficiency_evidence':b['prediction'].get('evidence')})
    a,b=metrics['control'],metrics['sufficiency']
    metrics['acceptance_passed']=b['entity']['correct']>=37 and b['entity']['confident_errors']<=a['entity']['confident_errors'] and b['attribute']['correct']>=a['attribute']['correct'] and b['all']['technical_failures']==0
    metrics['actual_new_api_calls']=read_json(root/'call_metrics.json')['new_api_calls']
    metrics['model_audit']=[{'requested':k[0],'returned':k[1],'count':v} for k,v in Counter((r['audit']['identity']['model'],r['audit'].get('response_model')) for r in rows).items()]
    metrics['unique_response_ids']=len({r['audit'].get('response_id') for r in rows})
    write_json(root/'metrics.json',metrics);write_jsonl(root/'paired.jsonl',pairs)
    print(json.dumps({c:{k:metrics[c][k]['correct'] for k in ('all','entity','attribute')} for c in ('control','sufficiency')}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run','report']);p.add_argument('--output',required=True);p.add_argument('--resume',action='store_true');a=p.parse_args()
    if a.action=='run':run(a.output,a.resume)
    else:globals()[a.action](a.output)
