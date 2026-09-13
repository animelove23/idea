"""Prepare immutable response selections and answer-hidden development review materials."""
import copy
from collections import Counter
from pathlib import Path
from analysis_skeleton.common import read_json,read_jsonl,write_json,write_jsonl,write_csv,sha,digest,check_frozen
from analysis_skeleton.build_fixtures import D,E,A,q
from .contracts import normalize_document,validate_alignment

DATA=Path('analysis_skeleton/fixtures/expansion20')
OLD=Path('outputs/skeleton_expansion20')
REPAIR=Path('outputs/skeleton_repair_v1')


def boundary_cases():
    cases=[]
    def item(text,raw):
        normalized=normalize_document(raw,text)
        if normalized['issues']:raise ValueError('invalid_boundary_reference')
        return {'text':text,'expected_candidate':raw}
    def add(kind,a,b,rule):
        cases.append({'case_id':f'b{len(cases)+1:02d}','stage':'decompose','boundary':kind,
                      'positive':a,'counter':b,'rule':rule,'reference_status':'authored_synthetic_candidate_not_model_test'})
    values=[('state','open','door'),('state','closed','door'),('state','wet','bench'),('state','dry','towel'),
            ('state','broken','chair'),('state','intact','vase'),('shape','round','table'),('shape','square','tile'),
            ('shape','curved','road'),('material','wood','table'),('material','metal','spoon'),
            ('color','red','car'),('color','blue','shirt'),('size','large','bird'),('size','small','tractor')]
    for slot,value,noun in values:
        text=f'The {value} {noun}.' if slot!='material' else f'The {noun} made of {value}.'
        evidence=f'{value} {noun}' if slot!='material' else f'{noun} made of {value}'
        positive=item(text,D([E('e1',noun,noun)],[A('a1','e1',slot,value,evidence,value)]))
        modifier='moving' if slot=='state' else 'beautiful'
        reason='action' if slot=='state' else 'subjective'
        counter=item(f'The {modifier} {noun}.',D([E('e1',noun,noun)],excluded=[(modifier,reason)]))
        add(slot,positive,counter,'Only the explicit in-scope attribute is counted; action/subjective modifier is excluded.')
    asserted=item('There is a dog.',D([E('e1','dog','dog')]))
    add('speculative_existence',asserted,item('There may be a dog.',D([],excluded=[('may be a dog','nonasserted')])),
        'Speculation over existence does not create an asserted entity.')
    add('negative_existence',asserted,item('There is no dog.',D([],excluded=[('no dog','nonasserted')])),
        'A negated entity is outside this positive-only contract, not automatically a hallucination.')
    add('speculative_attribute',item('There is a red car.',D([E('e1','car','car')],[A('a1','e1','color','red','red car','red')])),
        item('There is a car; it may be red.',D([E('e1','car','car')],excluded=[('may be red','nonasserted')])),
        'Keep the asserted car while excluding only speculative redness.')
    add('repeat_mention',item('A car. The car.',D([E('e1','car','car',q('car',1))])),
        item('A car.',D([E('e1','car','car')])), 'Mention count changes without increasing existence fact count.')
    def shirts(first,second):
        text=f'A {first} shirt beside a {second} shirt.'
        raw=D([E('e1','shirt','shirt'),E('e2','shirt',q('shirt',1))],
              [A('a1','e1','color',first,f'{first} shirt',first),A('a2','e2','color',second,f'{second} shirt',second)],
              excluded=[(f'beside a {second} shirt','relation')])
        return item(text,raw)
    add('two_subject_binding',shirts('red','blue'),shirts('blue','red'),'Two shirt anchors, with colors bound to their own occurrences.')
    # Four fixed-fact alignment controls supplement the natural set's missing modified/gap coverage.
    def doc(color,text=None,attribute=True):
        text=text or f'The {color} chair.'
        return normalize_document(D([E('e1','chair','chair')],[A('a1','e1','color',color,f'{color} chair',color)] if attribute else []),text)
    for kind in ('retained','modified','removed','extraction_gap'):
        original=doc('red');steer=doc('blue') if kind=='modified' else doc('red') if kind=='retained' else doc('red','The chair.',False) if kind=='removed' else doc('red',attribute=False)
        edge={'original':['a1'],'steer':['a1'] if kind in ('retained','modified') else [],
              'status':'unresolved' if kind=='extraction_gap' else kind,'reason':kind}
        if kind=='extraction_gap':edge['opposite_evidence']=q('red chair')
        output={'entities':[{'original':['e1'],'steer':['e1'],'status':'matched','reason':'same_chair'}],
                'alignments':[{'original':['entity_e1'],'steer':['entity_e1'],'status':'retained','reason':'same_chair'},edge]}
        if validate_alignment(output,original,steer)['issues']:raise ValueError('invalid_alignment_boundary')
        cases.append({'case_id':f'b{len(cases)+1:02d}','stage':'align','boundary':kind,
                      'input':{'original':original,'steer':steer},'expected_candidate':output,
                      'rule':'Same definite chair; check the full opposite text and frozen attribute slot.',
                      'reference_status':'authored_synthetic_candidate_not_model_test'})
    return cases


def prepare(root):
    root=Path(root)
    if root.exists() and any(root.iterdir()):raise ValueError('new_audit_directory_required')
    root.mkdir(parents=True,exist_ok=True)
    checks=[OLD/'m2',OLD/'m3_independent',OLD/'m5_independent',REPAIR/'m2_replay',REPAIR/'m3_replay',REPAIR/'visual_ab',REPAIR/'end_to_end']
    for p in checks:check_frozen(p)
    pairs=read_jsonl(DATA/'pairs.jsonl');m2={r['case_id']:r for r in read_jsonl(OLD/'m2/results.jsonl')}
    records=[]
    for i,p in enumerate(pairs):
        pid=p['pair_id'];folder=REPAIR/'end_to_end'/f'pair_{i:04d}'
        for side in ('original','steer'):
            records.append({'task_key':f'{pid}:decompose:{side}','source':str(OLD/'m2/results.jsonl'),
                            'audit':m2[p[side]['caption_id']]['audit']})
        path=folder/'m3.json';records.append({'task_key':f'{pid}:align','source':str(path),'audit':read_json(path)['audit']})
        for query in read_jsonl(folder/'verification_queue.jsonl'):
            path=folder/f'm5_{query["claim_id"]}.json'
            records.append({'task_key':f'{pid}:verify:{query["claim_id"]}','source':str(path),'audit':read_json(path)['audit']})
    write_jsonl(root/'response_cache.jsonl',records)
    boundaries=boundary_cases();write_jsonl(root/'boundary_cases.jsonl',boundaries)
    coverage=[]
    shots={s:read_jsonl(Path('analysis_skeleton/shots')/(s+'.jsonl')) for s in ('decompose','align','verify')}
    for slot in ('color','material','size','shape','state'):
        matching=[s['example_id'] for s in shots['decompose'] if any(a['slot']==slot for a in s['output']['attributes'])]
        coverage.append({'stage':'decompose','boundary':slot,'current_shots':matching,
                         'diagnostic_cases':[b['case_id'] for b in boundaries if b['stage']=='decompose' and b['boundary']==slot],
                         'status':'review_required'})
    for state in ('retained','removed','added','modified','unresolved'):
        coverage.append({'stage':'align','boundary':state,
                         'current_shots':[s['example_id'] for s in shots['align'] if any(e['status']==state for e in s['output']['alignments'])],
                         'diagnostic_cases':[b['case_id'] for b in boundaries if b['stage']=='align' and b['boundary']==state],
                         'status':'review_required'})
    for boundary in ('color','size','material','shape','state','locator_context'):
        coverage.append({'stage':'verify','boundary':boundary,
                         'current_shots':[s['example_id'] for s in shots['verify'] if s['semantic_type']=='attribute'] if boundary=='color' else [],
                         'diagnostic_cases':[],'status':'candidate_only' if boundary=='color' else 'coverage_gap'})
    write_csv(root/'shot_coverage_matrix.csv',list(coverage[0]),coverage)
    visual=[];key=[];text=[]
    contexts={c['case_id']:c['context_input']['entity_context'] for c in read_jsonl('analysis_skeleton/fixtures/repair_v1/visual_ab.jsonl')}
    for c in read_jsonl(DATA/'verify_cases.jsonl'):
        rid=digest(c['case_id'])[:16]
        visual.append({'review_id':rid,'image_path':c['input']['image_path'],'statement':c['input']['statement'],
                       'entity_context':contexts[c['case_id']],'reviewer1_label':None,'reviewer2_label':None,'adjudication':None})
        key.append({'review_id':rid,'source_case_id':c['case_id'],'original_candidate':c['reference_label'],
                    'original_reason':c['reference_reason'],'reference_status':'unchanged_assistant_candidate'})
    for c in read_jsonl(DATA/'decompose_cases.jsonl'):
        text.append({'review_id':digest(c['case_id'])[:16],'text':c['text'],'candidate':c['reference'],
                     'reviewer1':None,'reviewer2':None,'adjudication':None,'reference_status':'unchanged_assistant_candidate'})
    write_jsonl(root/'review_visual_answer_hidden.jsonl',visual);write_jsonl(root/'review_visual_candidate_key.jsonl',key)
    write_jsonl(root/'review_text_candidates.jsonl',text)
    write_json(root/'BASELINE_LOCK.json',{'checked_runs':[str(p) for p in checks],
        'source_manifest_hashes':{str(p/'manifest.json'):sha(p/'manifest.json') for p in checks},
        'source_response_hashes':{r['source']:sha(r['source']) for r in records},
        'prompt_shot_hashes':{str(p):sha(p) for folder in ('prompts','shots') for p in Path('analysis_skeleton',folder).iterdir() if p.is_file()},
        'cache_records':len(records),'new_api_calls':0})
    write_json(root/'split_manifest.json',{'R0':{'image_ids':[p['pair_id'] for p in pairs],'role':'previously_inspected_development'},
        'B1':{'cases':len(boundaries),'role':'authored_synthetic_candidate_diagnostic'},
        'D1':{'status':'not_created_pending_new_data_and_reference'},'T1':{'status':'not_created'},
        'review_warning':'Answer-hidden R0 review is not independent held-out human gold.'})
    return root
