"""Keep production facts, reference omissions, and exclusions on separate auditable axes."""
from collections import Counter
from analysis_skeleton.m6_analysis import analyze
from .scoring import correspondences,LemmaScorer


def production(bundle,queue,verification):
    result=analyze(bundle['original'],bundle['steer'],bundle['alignment'],queue,verification)
    truth={(r['side'],r['fact_id']):r['visual_label'] for r in result['facts']}
    ledger=[];isolated=[];lexical=[]
    claims={(r['side'],r['fact_id']):q['claim_id'] for q in queue for r in q['refs']}
    for r in result['facts']:
        doc=bundle[r['side']];fact=next(f for f in doc['facts'] if f['id']==r['fact_id'])
        parent=truth.get((r['side'],'entity_'+r['entity_id']))
        alignment='technical_unresolved' if r['reason'].startswith('technical') else 'semantic_unresolved' if r['status']=='unresolved' else 'decided'
        visual='pending' if r['visual_label']=='pending' else 'uncertain' if r['visual_label']=='uncertain' else 'decided'
        historical=r['visual_label']=='supported' and not r['truth_conflict']
        ledger.append({'pair_id':bundle['pair_id'],'caption_id':doc['caption_id'],**r,'value':fact['value'],
                       'claim_id':claims[(r['side'],r['fact_id'])],'extraction_axis':'accepted',
                       'alignment_axis':alignment,'visual_axis':visual,'parent_visual_label':parent,
                       'binding_unconfirmed':r['type']=='attribute' and parent in ('uncertain','pending',None),
                       'historical_supported_eligible':historical,
                       'strict_parent_supported_eligible':historical and (r['type']=='entity' or parent=='supported'),
                       'reference_truth':None,'reference_status':'not_provided'})
    for side in ('original','steer'):
        doc=bundle[side]
        for group in ('issues','source_audit','excluded'):
            isolated += [{'pair_id':bundle['pair_id'],'caption_id':doc['caption_id'],'side':side,
                          'record_type':group,'record_index':i,'record':r} for i,r in enumerate(doc.get(group,[]))]
        lex=bundle.get('lexical',{}).get(side,{})
        tokens=[t for t in lex.get('tokens',[]) if t.get('word_index') is not None]
        linked={i for q in queue for link in q['token_links'] if link['side']==side for i in link['token_ids']}
        counts=Counter(t['upos'] for t in tokens)
        content=sum(counts[k] for k in ('NOUN','PROPN','VERB','ADJ','ADV','NUM'))
        lexical.append({'pair_id':bundle['pair_id'],'side':side,'word_count':len(tokens),
                        'fact_linked_words':sum(t['token_id'] in linked for t in tokens),
                        'fact_unlinked_words':sum(t['token_id'] not in linked for t in tokens),
                        'content_words':content,'other_words':len(tokens)-content,
                        'pos_counts':dict(counts),'entity_mentions':sum(len(e['mentions']) for e in doc['entities']),
                        'attribute_value_mentions':sum(len(f['value_spans']) for f in doc['facts'] if f['type']=='attribute'),
                        'stop_reason':lex.get('caption',{}).get('stop_reason','unknown')})
    return ledger,isolated,lexical,result['metrics']


def reference_ledger(references,bundles,prediction_ledger,scorer=None):
    """References stay the denominator even when the model omitted the fact."""
    ref_ids=[r['caption_id'] for r in references]
    pred_ids=[b[s]['caption_id'] for b in bundles for s in ('original','steer')]
    if len(ref_ids)!=len(set(ref_ids)) or len(pred_ids)!=len(set(pred_ids)):raise ValueError('duplicate_caption_in_evaluation')
    scorer=scorer or LemmaScorer()
    docs={b[s]['caption_id']:(b['pair_id'],s,b[s]) for b in bundles for s in ('original','steer')}
    lookup={(r['caption_id'],r['fact_id']):r for r in prediction_ledger}
    rows=[];extras=[];scores=[]
    for ref in references:
        cid=ref['caption_id'];entry=docs.get(cid)
        if entry:
            pair,side,pred=entry;match=correspondences(pred,ref,scorer)
        else:
            pair=None;side=None;pred={'entities':[],'facts':[],'issues':[]};match={}
        scores.append({'caption_id':cid,'score':scorer.score(pred,ref)})
        for fact in ref['facts']:
            pid=match.get(fact['id']);observed=lookup.get((cid,pid),{})
            rows.append({'caption_id':cid,'pair_id':pair,'side':side,'reference_fact_id':fact['id'],
                         'type':fact['type'],'slot':fact['slot'],'value':fact['value'],'prediction_fact_id':pid,
                         'extraction_axis':'matched' if pid is not None else 'extraction_missing',
                         'alignment_axis':observed.get('alignment_axis','unavailable'),
                         'visual_axis':observed.get('visual_axis','unavailable'),
                         'predicted_transition':observed.get('status'),
                         'predicted_visual_label':observed.get('visual_label'),
                         'reference_visual_label':None,'reference_status':'assistant_candidate_not_human_gold'})
        extras += [{'caption_id':cid,'prediction_fact_id':f['id'],'type':f['type'],'slot':f['slot'],
                    'value':f['value'],'status':'unmatched_prediction_candidate_review'}
                   for f in pred['facts'] if f['id'] not in set(match.values())]
    return rows,extras,scores
