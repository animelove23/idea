"""Author predeclared references from captions only, before inspecting model predictions."""
import random
from pathlib import Path
from analysis_skeleton.common import read_jsonl,write_jsonl,write_json,sha
from analysis_skeleton.build_fixtures import E,A,D,q
from analysis_skeleton.contracts import normalize_document,quote_span
from analysis_skeleton.m3_align import validate_alignment
from .reference_specs import SPECS,AMBIGUITIES

ROOT=Path('analysis_skeleton/fixtures/expansion20')


def raw_document(text,spec):
    entities=[];keys={}
    for key,name,mention in spec[0]:
        eid=f'e{len(entities)+1}';keys[key]=eid
        entities.append(E(eid,name,mention))
    attrs=[]
    for key,slot,value,evidence,value_quote in spec[1]:
        attr=A(f'a{len(attrs)+1}',keys[key],slot,value,evidence,value_quote)
        source=quote_span(text,q(evidence))
        occurrence=0
        while True:
            span=quote_span(text,q(value_quote,occurrence))
            if source['start']<=span['start'] and span['end']<=source['end']:break
            occurrence+=1
        attr['value_quotes']=[q(value_quote,occurrence)]
        attrs.append(attr)
    raw=D(entities,attrs)
    assert not normalize_document(raw,text)['issues'],normalize_document(raw,text)['issues']
    return raw,keys


def alignment_reference(docs,keys,ambiguous):
    ent=[];facts=[];covered={s:set() for s in docs}
    for group in ambiguous:
        ids={s:[keys[s][key] for key in group.get(s,[]) if key in keys[s]] for s in docs}
        if not any(ids.values()):continue
        ent.append({**ids,'status':'unresolved','reason':'identity_or_granularity_unclear'})
        fs={s:[f['id'] for f in docs[s]['facts'] if f['entity_id'] in ids[s]] for s in docs}
        facts.append({**fs,'status':'unresolved','reason':'identity_or_granularity_unclear'})
        for s in docs:covered[s].update(ids[s])
    all_keys=sorted(set(keys['original'])|set(keys['steer']))
    for key in all_keys:
        ids={s:[keys[s][key]] if key in keys[s] and keys[s][key] not in covered[s] else [] for s in docs}
        if not any(ids.values()):continue
        status='matched' if all(ids.values()) else 'original_only' if ids['original'] else 'steer_only'
        ent.append({**ids,'status':status,'reason':'prewritten_caption_reference'})
        fs={s:[f for f in docs[s]['facts'] if f['entity_id'] in ids[s]] for s in docs}
        if status!='matched':
            for s in docs:
                for f in fs[s]:facts.append({'original':[f['id']] if s=='original' else [],'steer':[f['id']] if s=='steer' else [],
                                             'status':'removed' if s=='original' else 'added','reason':'prewritten_absence_reference'})
            continue
        for slot in ('existence','color','material','size','shape','state'):
            a=[f for f in fs['original'] if f['slot']==slot];b=[f for f in fs['steer'] if f['slot']==slot]
            used=set()
            for f in a:
                candidates=[g for g in b if g['id'] not in used and (slot=='existence' or f['value']==g['value'])]
                if candidates:
                    g=candidates[0];used.add(g['id'])
                    facts.append({'original':[f['id']],'steer':[g['id']],'status':'retained','reason':'prewritten_same_proposition'})
                elif len(a)==len(b)==1 and slot!='existence':
                    used.add(b[0]['id'])
                    facts.append({'original':[f['id']],'steer':[b[0]['id']],'status':'modified','reason':'prewritten_same_slot_change'})
                else:facts.append({'original':[f['id']],'steer':[],'status':'removed','reason':'prewritten_absence_reference'})
            for g in b:
                if g['id'] not in used:facts.append({'original':[],'steer':[g['id']],'status':'added','reason':'prewritten_absence_reference'})
    result={'entities':ent,'alignments':facts}
    checked=validate_alignment(result,docs['original'],docs['steer'])
    assert not checked['issues'],checked['issues']
    return result


def build():
    if (ROOT/'selection.json').exists():raise ValueError('Never overwrite prepared evaluation')
    roster=read_jsonl('outputs/skeleton_v1/m0_resolved/pairs.jsonl')
    lengths={r['caption']['caption_id']:r['caption']['word_len'] for r in read_jsonl('outputs/skeleton_v1/m1/lexical.jsonl')}
    excluded={'3501','8775','54627','212603','275717','337055','150639','360487','397351'}
    pool=[p for p in roster if p['image_sha256'] and p['pair_id'] not in excluded]
    pool.sort(key=lambda p:(lengths[p['original']['caption_id']],int(p['pair_id'])))
    rng=random.Random(1994);selected=[];selection=[]
    for i in range(4):
        bucket=pool[i*len(pool)//4:(i+1)*len(pool)//4]
        for p in rng.sample(bucket,5):
            selected.append(p)
            selection.append({'pair_id':p['pair_id'],'length_stratum':i+1,'stratum_population':len(bucket),
                              'original_words':lengths[p['original']['caption_id']],'steer_words':lengths[p['steer']['caption_id']]})
    assert set(SPECS)=={p['pair_id'] for p in selected}
    ROOT.mkdir(parents=True,exist_ok=True)
    write_jsonl(ROOT/'pairs.jsonl',selected)
    m2=[];m3=[]
    for p in selected:
        docs={};keys={}
        for s in ('original','steer'):
            c=p[s];raw,keys[s]=raw_document(c['text'],SPECS[p['pair_id']][s])
            docs[s]=normalize_document(raw,c['text'],c['caption_id'])
            m2.append({'case_id':c['caption_id'],'text':c['text'],'reference':raw,'split':'real_development_expansion',
                       'reference_status':'assistant_caption_only_candidate_pre_prediction','family':p['pair_id']})
        m3.append({'case_id':p['pair_id'],**docs,'reference':alignment_reference(docs,keys,AMBIGUITIES.get(p['pair_id'],[])),
                   'reference_status':'assistant_candidate_pre_prediction','split':'real_development_fixed_reference_facts'})
    write_jsonl(ROOT/'decompose_cases.jsonl',m2);write_jsonl(ROOT/'align_cases.jsonl',m3)
    write_json(ROOT/'selection.json',{'seed':1994,'eligible_images':len(pool),'excluded_previous_ids':sorted(excluded),
               'selection':selection,'interpretation':'Stratified developmental diagnostic set, not random population or held-out test.',
               'no_prediction_in_reference_authoring':True,
               'protected_stage_files':{str(p):sha(p) for p in Path('analysis_skeleton/prompts').glob('*.txt')}|
                                       {str(p):sha(p) for p in Path('analysis_skeleton/shots').glob('*.jsonl')}})


if __name__=='__main__':build()
