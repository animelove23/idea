"""Tighten matrix states using necessary cardinality constraints, never guess labels."""
import copy,re
from collections import Counter
from experiments.coco400_v1.observe import role


FLAGS={'unchanged':(False,False),'gained':(True,False),'lost':(False,True),'mixed':(True,True)}


def constrain(states,gain_required,loss_required):
    return [s for s in states if (not gain_required or FLAGS[s][0]) and (not loss_required or FLAGS[s][1])]


def tighten(observation,ledger,bundle=None):
    """Fixed unique fact units / one-to-one retention, not counts of physical instances.

    If original supported facts exceed even the maximum possible supported facts
    on the other side, at least one original fact cannot be retained. The symmetric
    inequality proves a gain. This identifies a direction, not which fact changed.
    """
    out=copy.deepcopy(observation);counts=Counter();audit=[];requirements={r:[False,False] for r in ('S','H')}
    missing=set(out.get('missing_component_types',[]));disabled=[]
    # Opposite-side extraction gaps invalidate a complete-set count proof even
    # when the original M2 validator did not detect the missing fact.
    for row in ledger:
        reason=row.get('reason','')
        if 'extraction_gap' in reason:
            missing.update(('entity','attribute') if row['type']=='entity' else ('attribute',))
            disabled.append('alignment_detected_extraction_gap')
        if re.search(r'collection|part.whole|many.to.one|one.to.many|disjunction|group',reason,re.I):
            missing.update(('entity','attribute'));disabled.append('unstable_referent_granularity')
    if bundle:
        for e in bundle['alignment']['entities']:
            if e.get('description_change') in ('collection_change','part_whole') or re.search(r'collection|part.whole|many.to.one|one.to.many|disjunction|group',e.get('reason',''),re.I) and e['status']=='unresolved':
                missing.update(('entity','attribute'));disabled.append('unstable_referent_granularity')
    for row in ledger:counts[(row['side'],row['type'],role(row))]+=1
    for kind in ('entity','attribute'):
        for label in ('S','H'):
            lo={s:counts[(s,kind,label)] for s in ('original','steer')}
            hi={s:lo[s]+counts[(s,kind,'?')] for s in ('original','steer')}
            eligible=kind not in missing
            min_gain=max(0,lo['steer']-hi['original']) if eligible else 0
            min_loss=max(0,lo['original']-hi['steer']) if eligible else 0
            key=kind+'_'+label;prior=out['component_states'][key]
            post=constrain(prior,min_gain>0,min_loss>0)
            if not post:raise ValueError('cardinality_constraint_inconsistent_with_event_states:'+key)
            out['component_states'][key]=post
            requirements[label][0]|=min_gain>0;requirements[label][1]|=min_loss>0
            audit.append({'component':key,'original_count_lower':lo['original'],'original_count_upper':hi['original'],
                'steer_count_lower':lo['steer'],'steer_count_upper':hi['steer'],'minimum_gain_from_counts':min_gain,
                'minimum_loss_from_counts':min_loss,'eligible':eligible,'disabled_reason':sorted(set(disabled)) or ['M2_missing_information'] if not eligible else None,
                'before':prior,'after':post})
    for label,name in [('S','supported_change'),('H','hallucination_change')]:
        post=constrain(out['candidate_states'][label],*requirements[label])
        if not post:raise ValueError('cardinality_constraint_inconsistent_with_total_states:'+label)
        out['candidate_states'][label]=post;out[name]=post[0] if len(post)==1 else 'unresolved'
    out['matrix_classifiable']=all(out[k]!='unresolved' for k in ('supported_change','hallucination_change'))
    out['cardinality_bounds_audit']=audit
    out['matrix_method']='v2_events_intersect_necessary_cardinality_bounds_v4'
    return out
