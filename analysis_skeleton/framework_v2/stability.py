"""Evaluation only: independent repeats are not cache replays or extra independent images."""
from itertools import combinations
from analysis_skeleton.common import digest,ratio
from analysis_skeleton.m5_verify import score_labels


def visual_metrics(records):
    result=score_labels(records)
    decided=[r for r in records if r.get('prediction',{}).get('label') in {'supported','hallucinated'}]
    gold_decided=[r for r in records if r['reference_label'] in {'supported','hallucinated'}]
    result['decided_error_rate']=ratio(sum(r['prediction']['label']!=r['reference_label'] for r in decided),len(decided))
    result['gold_decidable_coverage']=ratio(sum(r.get('prediction',{}).get('label') in {'supported','hallucinated'} for r in gold_decided),len(gold_decided))
    return result


def repeat_metrics(records,case_ids,replicate_ids):
    if len(replicate_ids)!=3 or len(set(replicate_ids))!=3:raise ValueError('three_distinct_replicates_required')
    if len(case_ids)!=len(set(case_ids)):raise ValueError('duplicate_case')
    index={};response_ids=set();conditions=set();queries={}
    for r in records:
        key=(r['case_id'],r['replicate_id'])
        if key in index or r['case_id'] not in case_ids or r['replicate_id'] not in replicate_ids:raise ValueError('duplicate_or_unknown_repeat_record')
        a=r.get('audit',{})
        if not r.get('query_hash') or not isinstance(a.get('identity'),dict):raise ValueError('query_and_model_identity_required')
        signature=(r['query_hash'],digest(a['identity']),r.get('image_id'))
        if r['case_id'] in queries and queries[r['case_id']]!=signature:raise ValueError('repeat_input_or_model_changed')
        queries[r['case_id']]=signature
        if a.get('cache_hit') or r.get('cache_mode')=='replay':raise ValueError('replay_is_not_independent_repeat')
        rid=a.get('response_id')
        if rid and rid in response_ids:raise ValueError('response_reused_across_repeats')
        if rid:response_ids.add(rid)
        if r.get('status')=='complete' and ('signature' not in r or not rid):raise ValueError('complete_repeat_requires_signature_and_response_id')
        conditions.add(r.get('condition_id'));index[key]=r
    if len(conditions)>1:raise ValueError('conditions_must_be_reported_separately')
    complete=[]
    for cid in case_ids:
        rows=[index.get((cid,r),{}) for r in replicate_ids]
        if all(r.get('status')=='complete' for r in rows):complete.append(rows)
    comparisons=[(a,b) for rows in complete for a,b in combinations(rows,2)]
    changes=sum(a['signature']!=b['signature'] for a,b in comparisons)
    sh=sum({a.get('label'),b.get('label')}=={'supported','hallucinated'} for a,b in comparisons)
    return {'cases':len(case_ids),'complete_three_repeat_cases':len(complete),
            'complete_coverage':ratio(len(complete),len(case_ids)),
            'pairwise_disagreement':ratio(changes,len(comparisons)),
            'pairwise_supported_hallucinated_flip':ratio(sh,len(comparisons)),
            'any_change_case_rate':ratio(sum(len({r['signature'] for r in rows})>1 for rows in complete),len(complete)),
            'unsuccessful_or_missing_requests':3*len(case_ids)-sum(r.get('status')=='complete' for r in records),
            'independent_images':len({r['image_id'] for r in records if r.get('image_id') is not None}),
            'stability_gate_evaluable':len(case_ids)>0 and len(complete)/len(case_ids)>=.99}


def document_signature(doc,scorer):
    entities={e['id']:(scorer.name(e['name']),tuple(sorted((m['start'],m['end']) for m in e['mentions']))) for e in doc['entities']}
    facts=[(entities[f['entity_id']],f['type'],f['slot'],scorer.name(f['value']) if f['type']=='entity' else f['value'].casefold()) for f in doc['facts']]
    return digest(sorted(facts))
