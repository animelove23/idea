"""Reference-based owner diagnostics, separate from unmeasured human entailment."""
from analysis_skeleton.metrics import matching,overlap,normal,prf

def diagnostics(pred,ref,scorer):
    # Ambiguous owner matches remain unscored; color/material cannot choose owners.
    candidates={e['id']:[g['id'] for g in ref['entities'] if scorer.name(e['name'])==scorer.name(g['name']) and overlap(e['mentions'],g['mentions'])] for e in pred['entities']}
    # If the reference splits one predicted kind into more referents, a unique
    # span overlap still cannot prove equivalent group/subgroup scope.
    pred_names={e['id']:scorer.name(e['name']) for e in pred['entities']}
    ref_names=[scorer.name(e['name']) for e in ref['entities']]
    partition_ambiguous={eid for eid,name in pred_names.items() if ref_names.count(name)>list(pred_names.values()).count(name)}
    owner={p:gs[0] for p,gs in candidates.items() if p not in partition_ambiguous and len(gs)==1 and sum(gs[0] in vs for vs in candidates.values())==1}
    attrs=[f for f in pred['facts'] if f['type']=='attribute'];gold=[f for f in ref['facts'] if f['type']=='attribute']
    decisions=[]
    for f in attrs:
        compatible=[g for g in gold if g['slot']==f['slot'] and normal(g['value'])==normal(f['value']) and overlap(g['value_spans'],f['value_spans'])]
        owners={g['entity_id'] for g in compatible};mapped=owner.get(f['entity_id'])
        status='unjudged' if mapped is None or len(owners)!=1 else 'correct' if mapped in owners else 'wrong'
        decisions.append({'fact_id':f['id'],'owner_status':status,'reference_owner_candidates':sorted(owners),'mapped_owner':mapped,'referent_partition_requires_review':f['entity_id'] in partition_ambiguous})
    correct=sum(r['owner_status']=='correct' for r in decisions);wrong=sum(r['owner_status']=='wrong' for r in decisions)
    base=scorer.score(pred,ref)
    return {'score':base,'ownership_correct':correct,'ownership_wrong':wrong,'ownership_unjudged':len(attrs)-correct-wrong,
            'ownership_decisions':decisions,'faithfulness_candidate_agreement':base['joint']['precision'],
            'textual_entailment_accuracy':None,'atomicity_semantic_accuracy':None,
            'reference_missing_facts':base['joint']['reference']-base['joint']['tp']}
