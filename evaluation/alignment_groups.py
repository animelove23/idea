"""Separate primary accounting from repeated references to shared semantic support."""
import copy
from collections import Counter


def members(row):
    return {(side, fid) for side in ('original', 'steer') for fid in row[side+'_fact_ids']}


def components(rows):
    remaining=list(rows)
    while remaining:
        group=[remaining.pop(0)]
        occupied=members(group[0])
        changed=True
        while changed:
            changed=False
            for row in remaining[:]:
                if occupied & members(row):
                    group.append(row); occupied.update(members(row)); remaining.remove(row); changed=True
        yield group


def resolve(rows, equivalence_keys=None):
    """No arbitrary winner between conflicting confident matches.

    Exact repeated output rows are redundant records, not two claims. A valid primary
    match is not invalidated by a contextual ambiguous reference to it. Remaining
    overlapping uncertain rows are represented as one uncertain group, not losses.
    """
    unique=[]; notes=[]; seen={}
    for row in rows:
        key=(tuple(sorted(row['original_fact_ids'])),tuple(sorted(row['steer_fact_ids'])),row['status'],row['reason'])
        if key in seen:
            target=seen[key]
            for e in row['evidence']:
                if e not in target['evidence']:target['evidence'].append(e)
            notes.append({'rule':'duplicate_output_record','fact_ids':list(key[:2])})
        else:
            saved=copy.deepcopy(row);unique.append(saved);seen[key]=saved
    confident=[r for r in unique if r['status']!='ambiguous']
    collapsed=[]
    for group in components(confident):
        equivalent=len(group)>1 and all(r['status']=='retained' for r in group) and equivalence_keys is not None
        if equivalent:
            for side in ('original','steer'):
                keys={equivalence_keys[(side,fid)] for r in group for fid in r[side+'_fact_ids']}
                equivalent=equivalent and len(keys)==1
        if equivalent:
            merged=copy.deepcopy(group[0])
            for side in ('original','steer'):
                merged[side+'_fact_ids']=list(dict.fromkeys(fid for r in group for fid in r[side+'_fact_ids']))
            merged['evidence']=[]
            for r in group:
                for e in r['evidence']:
                    if e not in merged['evidence']:merged['evidence'].append(e)
            collapsed.append(merged)
            notes.append({'rule':'group_exact_equivalent_facts','original_fact_ids':merged['original_fact_ids'],'steer_fact_ids':merged['steer_fact_ids']})
        else:collapsed.extend(group)
    confident=collapsed
    ownership=Counter(m for r in confident for m in members(r))
    selected=[]; unresolved=[]; rejected=[]
    for row in confident:
        if all(ownership[m]==1 for m in members(row)):
            selected.append(row)
        else:
            rejected.append({'raw':copy.deepcopy(row),'error':'conflicting confident correspondences require review'})
    occupied=set().union(*(members(r) for r in selected)) if selected else set()
    related=[]
    for row in (r for r in unique if r['status']=='ambiguous'):
        overlap=members(row)&occupied
        rest=members(row)-occupied
        if overlap:
            # This remains an uncertain association, never a second retained claim.
            related.append({**copy.deepcopy(row),'role':'contextual_reference','counted_as_primary_alignment':False,
                            'shared_fact_ids':[{ 'side':s,'fact_id':fid} for s,fid in sorted(overlap)]})
            notes.append({'rule':'preserve_primary_and_contextual_reference','shared_fact_ids':sorted(overlap)})
        if rest:
            residual=copy.deepcopy(row)
            for side in ('original','steer'):
                residual[side+'_fact_ids']=[fid for fid in row[side+'_fact_ids'] if (side,fid) in rest]
            unresolved.append(residual)
    for group in components(unresolved):
        row=copy.deepcopy(group[0])
        for side in ('original','steer'):
            row[side+'_fact_ids']=list(dict.fromkeys(fid for r in group for fid in r[side+'_fact_ids']))
        row['evidence']=[]
        for r in group:
            for e in r['evidence']:
                if e not in row['evidence']:row['evidence'].append(e)
        reasons=sorted({r['reason'] for r in group})
        if len(group)>1:
            row['reason']=reasons[0] if len(reasons)==1 and reasons[0]!='extraction_gap' else 'granularity'
            row['component_reasons']=reasons
            notes.append({'rule':'group_overlapping_uncertain_correspondences','original_fact_ids':row['original_fact_ids'],'steer_fact_ids':row['steer_fact_ids']})
        selected.append(row)
    return selected,related,notes,rejected
