"""Semantic review decisions are distinct from malformed-output failures."""
import copy
from collections import Counter


def entity_groups(rows):
    """Deduplicate records, union uncertain candidates, localize identity conflicts."""
    groups=[];notes=[]
    for raw in rows:
        row=copy.deepcopy(raw)
        exact=next((r for r in groups if all(set(r[k])==set(row[k]) for k in ('original_entity_ids','steer_entity_ids')) and r['status']==row['status']),None)
        if exact is not None:
            notes.append({'rule':'duplicate_entity_correspondence','raw':row});continue
        overlap=[];members=lambda r:{(s,i) for s in ('original','steer') for i in r[s+'_entity_ids']}
        seen=members(row)
        changed=True
        while changed:
            changed=False
            for r in groups:
                if r not in overlap and seen & members(r):
                    overlap.append(r);seen|=members(r);changed=True
        if overlap:
            involved=overlap+[row]
            uncertain=all(r['status']=='ambiguous' for r in involved)
            row={k:sorted({i for r in involved for i in r[k]}) for k in ('original_entity_ids','steer_entity_ids')}
            row.update(status='ambiguous',reason='; '.join(dict.fromkeys(r['reason'] for r in involved)))
            notes.append({'rule':'union_uncertain_entity_candidates' if uncertain else 'localize_entity_conflict','raw':involved})
            for r in overlap:groups.remove(r)
        groups.append(row)
    return groups,notes


def attribute_dimension(fact,slot):
    # Use the existing semantic category, not an unrestricted auxiliary slot name.
    category={'color':'color','material':'material','counting':'count','shape':'shape'}.get(fact.get('category'))
    if category:return category
    return slot if slot in {'age','condition','size','height','color','material','shape'} else None


INVERSES={('above','below'),('left_of','right_of'),('in_front_of','behind')}
INVERSES|={(b,a) for a,b in list(INVERSES)}
SYMMETRIC={'near','next_to','beside','close_to'}
COLLECTIONS={'scattered_in','scattered_around','spread_in','spread_across'}


def semantic_review(status,facts,participants,slots):
    """Return a review reason, or warnings. Never invent a confident semantic label."""
    warnings=[]
    if status=='ambiguous':return None,warnings
    types={f['type'] for f in facts}
    missing=any(not p for p in participants)
    uncertain=any(None in p for p in participants)
    if status in ('removed','added'):
        if uncertain and types=={'entity'}:
            return ('entity_uncertain','unresolved_existence_identity'),warnings
        if missing or uncertain:
            warnings.append({'rule':'one_sided_caption_judgment','note':'Accepted the model caption-level loss/addition claim despite incomplete referent bookkeeping; this is not independent semantic verification.'})
        return None,warnings
    if len(types)>1:return ('granularity','different_fact_types'),warnings
    if uncertain:return ('entity_uncertain','unresolved_correspondence_identity'),warnings
    if missing and types!={'other'}:return ('entity_uncertain','missing_correspondence_referent'),warnings
    if not all(p==participants[0] for p in participants):
        # Collection order is irrelevant, but subject/reference roles for directional relations are not.
        collection=(types=={'relation'} and len(set(slots))==1 and slots[0] in COLLECTIONS
            and all(len(p)>2 and p[-1]==participants[0][-1] and Counter(p[:-1])==Counter(participants[0][:-1]) for p in participants))
        reversed_pair=(len(participants)==2 and len(participants[0])==len(participants[1])==2
                       and participants[0]==participants[1][::-1])
        inverse=(types=={'relation'} and status=='retained' and reversed_pair and
                 ((slots[0],slots[1]) in INVERSES or (slots[0] in SYMMETRIC and slots[1] in SYMMETRIC and slots[0]==slots[1])))
        if collection or inverse:warnings.append({'rule':'participant_order_semantically_compatible','slots':slots})
        else:return ('partial_overlap','participant_roles_or_scope_changed'),warnings
    dimensions={d for f,s in zip(facts,slots) if (d:=attribute_dimension(f,s)) is not None}
    if types=={'attribute'} and len(dimensions)>1:
        return ('granularity','different_attribute_dimensions'),warnings
    if status=='modified' and dimensions=={'count'}:
        # Explicit count scopes differ; do not erase them merely because both are numeric attributes.
        scopes={s.removeprefix('count_') for s in slots if s.startswith('count_')}
        if len(scopes)>1:return ('partial_overlap','count_scope_changed'),warnings
    if status=='retained' and any((f['assertion'],f['polarity'])!=(facts[0]['assertion'],facts[0]['polarity']) for f in facts):
        return ('qualifier_difference','modality_or_polarity_changed'),warnings
    if len(set(slots))>1:warnings.append({'rule':'different_slot_labels','slots':slots,'note':'Labels alone do not prove different semantics; accepted model correspondence after explicit category/scope checks.'})
    return None,warnings
