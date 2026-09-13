"""Paired, balanced-order visual context experiment; unchanged labels and six shots."""
import argparse
import copy
import random
from pathlib import Path
from analysis_skeleton.common import read_jsonl,write_jsonl,new_run,check_frozen,report
from analysis_skeleton.m5_verify import VisualStage,validate_label,score_labels
from analysis_skeleton.pipeline import call
from .context import SourceLocator

DATA=Path('analysis_skeleton/fixtures/expansion20')
CASES=Path('analysis_skeleton/fixtures/repair_v1/visual_ab.jsonl')
OUT=Path('outputs/skeleton_repair_v1/visual_ab')


def prepare():
    if CASES.exists():raise ValueError('Frozen A/B roster already exists')
    cases=read_jsonl(DATA/'verify_cases.jsonl')
    docs={c[s]['caption_id']:c[s] for c in read_jsonl(DATA/'align_cases.jsonl') for s in ('original','steer')}
    locator=SourceLocator();orders=['control','context']*(len(cases)//2)
    if len(cases)%2:orders.append('control')
    random.Random(1994).shuffle(orders);rows=[]
    for c,first in zip(cases,orders):
        doc=docs[c['source_caption_id']]
        fact=next(f for f in doc['facts'] if f['id']==c['source_fact_id'])
        entity=next(e for e in doc['entities'] if e['id']==fact['entity_id'])
        enriched=copy.deepcopy(c['input'])
        enriched['entity_context']=locator.context(doc,entity,c['input']['entity_context'])
        assert {k:v for k,v in enriched.items() if k!='entity_context'}=={k:v for k,v in c['input'].items() if k!='entity_context'}
        rows.append({**c,'control_input':c['input'],'context_input':enriched,
                     'order':[first,'context' if first=='control' else 'control']})
    CASES.parent.mkdir(parents=True,exist_ok=True)
    write_jsonl(CASES,rows)
    print(f'Frozen {len(rows)} paired cases; only entity_context differs; balanced order seed=1994')


def execute():
    cases=read_jsonl(CASES);stage=VisualStage()
    shot_images={e['input']['image_sha256'] for e in stage.shots}
    assert not any(c['input']['image_sha256'] in shot_images for c in cases)
    images={c['input']['image_path'] for c in cases}|{e['input']['image_path'] for e in stage.shots}
    out=new_run(OUT,'M5_context_AB',[CASES,stage.rules_path,stage.shots_path,*sorted(images)],
        {'identity':stage.identity,'only_variable':'entity_context exact source window + mention marker',
         'order_seed':1994,'replicates_per_condition':1,'query_references_sent':False},
        [__file__,Path(__file__).with_name('context.py'),Path('analysis_skeleton/m5_verify.py'),Path('analysis_skeleton/llm.py'),Path('analysis_skeleton/pipeline.py')])
    records=[]
    for c in cases:
        for condition in c['order']:
            check_frozen(out)
            response=call(stage,c[condition+'_input'],out/(c['case_id']+'_'+condition+'.json'),validate_label)
            record={k:c[k] for k in ('case_id','image_id','semantic_type','reference_label')}
            record.update(condition=condition,audit=response['audit'])
            if 'value' in response:record['prediction']=response['value']
            records.append(record)
            write_jsonl(out/'results.jsonl',records)
            print(f'M5 A/B {len(records)}/{2*len(cases)} {c["case_id"]} {condition}: {record.get("prediction",{}).get("label","technical_failure")}',flush=True)
    metrics={};by_id={}
    for condition in ('control','context'):
        selected=[r for r in records if r['condition']==condition]
        metrics[condition]=score_labels(selected)
        metrics[condition]['agreement']=sum(r.get('prediction',{}).get('label')==r['reference_label'] for r in selected)/len(selected)
        for r in selected:by_id.setdefault(r['case_id'],{})[condition]=r.get('prediction',{}).get('label','technical_failure')
    paired=[]
    for c in cases:
        p=by_id[c['case_id']];g=c['reference_label']
        paired.append({'case_id':c['case_id'],'reference_label':g,**p,
                       'improved':p['control']!=g and p['context']==g,'regressed':p['control']==g and p['context']!=g})
    metrics['paired']={'improved':sum(p['improved'] for p in paired),'regressed':sum(p['regressed'] for p in paired),
                      'label_changed':sum(p['control']!=p['context'] for p in paired)}
    write_jsonl(out/'paired.jsonl',paired)
    report(out,'M5 主体语境单变量同期对照',metrics,
        ['60个固定候选标签，双条件各一次；不是人工准确率，也不宣称跨重复稳定。',
         '图片、命题、模型、温度、系统规则、6-shot相同；只改变query的entity_context。',
         'source window是定位线索，不是视觉真值证据；不将原文关系加入计分事实。'])


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--prepare',action='store_true');a=p.parse_args()
    prepare() if a.prepare else execute()
