"""Unresolved-only subgraph patching; locked decisions are immutable.

Reuse the pre-existing, validated v4 repair predictions. No new model call and
no selection based on matrix membership, visual labels or reference answers.
"""
import copy
from collections import Counter
from experiments.coco400_revision_v2.alignment import validate

SIDES=('original','steer')

def refs(e):return {(s,x) for s in SIDES for x in e[s]}
def signature(e):return (tuple(e['original']),tuple(e['steer']),e['status'],e.get('description_change'))

def fill(old,proposed):
    locked=[copy.deepcopy(e) for e in old if e['status']!='unresolved']
    unresolved=[e for e in old if e['status']=='unresolved'];pool=set().union(*(refs(e) for e in unresolved)) if unresolved else set()
    accepted=[];used=set()
    for e in proposed:
        rr=refs(e)
        if rr and rr<=pool and not rr&used and e['status']!='unresolved':accepted.append(copy.deepcopy(e));used|=rr
    leftovers=[]
    for e in unresolved:
        left=refs(e)-used
        if left:leftovers.append({**copy.deepcopy(e),**{s:[x for x in e[s] if (s,x) in left] for s in SIDES}})
    return locked+accepted+leftovers,len(accepted)


def patch(old,candidate,original,steer):
    entities,ne=fill(old['entities'],candidate['entities'])
    facts,nf=fill(old['alignments'],candidate['alignments'])
    if not ne and not nf:return copy.deepcopy(old),{'status':'no_closed_proposal','proposed_entity_rows':0,'proposed_fact_rows':0}
    raw={'entities':entities,'alignments':copy.deepcopy(facts)}
    for e in raw['alignments']:
        if e.get('description_change') in ('generalized','specialized') and e['status']=='modified':e['status']='description_changed'
    try:
        checked=validate(raw,original,steer)
        for table in ('entities','alignments'):
            known={signature(e) for e in checked[table]}
            if any(signature(e) not in known for e in old[table] if e['status']!='unresolved'):raise ValueError('locked_decision_would_change')
        for side,d in [('original',original),('steer',steer)]:
            ids=[fid for e in checked['alignments'] for fid in e[side]]
            if Counter(ids)!=Counter(f['id'] for f in d['facts']):raise ValueError('fact_coverage_changed')
    except (ValueError,KeyError,IndexError) as e:
        return copy.deepcopy(old),{'status':'patch_rejected','reason':str(e),'proposed_entity_rows':ne,'proposed_fact_rows':nf}
    # Restore locked rows byte-for-byte; keep their original evidence and reasons.
    for table in ('entities','alignments'):
        locked={signature(e):e for e in old[table] if e['status']!='unresolved'}
        checked[table]=[copy.deepcopy(locked.get(signature(e),e)) for e in checked[table]]
    checked['v5_patch_audit']={'policy':'only_old_unresolved_refs_can_change','source':'frozen_v4_approved_predictions',
        'proposed_entity_rows':ne,'proposed_fact_rows':nf}
    return checked,{'status':'validated_patch','proposed_entity_rows':ne,'proposed_fact_rows':nf}
