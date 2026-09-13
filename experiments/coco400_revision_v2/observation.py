"""Scoped uncertainty, preserving all original data and explicit component states."""
import copy
from experiments.coco400_v1.observe import analyze_pair as baseline, candidates, KINDS, LABELS


def analyze_pair(bundle,ledger):
    b=copy.deepcopy(bundle);rows=copy.deepcopy(ledger);audits=[];missing=set();affected=set()
    for side in ('original','steer'):
        for issue in b[side].get('issues',[]):
            kind=issue.get('kind','');raw=issue.get('raw',{});reason=issue.get('reason','')
            if kind=='excluded_invalid':policy='diagnostic_only_excluded_record'
            elif kind=='attribute_state_unsupported':policy='rejected_nonliteral_state_not_a_text_fact'
            elif kind=='attribute_invalid' and reason=='state outside frozen six-value vocabulary':policy='outside_frozen_semantic_scope'
            else:
                policy='scoped_missing_information'
                if kind.startswith('attribute'):
                    missing.add('attribute');owner=raw.get('entity_id');slot=raw.get('slot')
                    owners={(side,owner)}
                    for e in b['alignment']['entities']:
                        if owner in e[side]:owners.update((s,x) for s in ('original','steer') for x in e[s])
                    affected.update((r['side'],r['fact_id']) for r in rows if r['type']=='attribute'
                        and ((r['side'],r['entity_id']) in owners or not owner) and (not slot or r['slot']==slot))
                else:
                    # Missing entities can affect unidentified opposite referents and their attributes.
                    missing.update(KINDS);affected.update((r['side'],r['fact_id']) for r in rows)
            audits.append({'side':side,'issue':issue,'policy':policy})
        b[side]['issues']=[]
    for e in b['alignment']['alignments']:
        refs={(s,x) for s in ('original','steer') for x in e[s]}
        if refs&affected:
            e.update(status='unresolved',reason='technical_scoped_extraction_dependency')
            for r in rows:
                if (r['side'],r['fact_id']) in refs:r.update(status='unresolved',reason=e['reason'],alignment_axis='technical_unresolved')
    result,events=baseline(b,rows)
    result['quality']['extraction_issues']=len(audits)
    result['issue_impact_audit']=audits;result['missing_component_types']=sorted(missing)
    result['component_states']={}
    for c in result['components']:
        key=c['type']+'_'+c['role']
        result['component_states'][key]=candidates(c['gain'],c['loss'],bool(c['possible_gain']) or c['type'] in missing,
                                                 bool(c['possible_loss']) or c['type'] in missing)
    for label,name in [('S','supported_change'),('H','hallucination_change')]:
        cc=[c for c in result['components'] if c['role']==label]
        cs=candidates(sum(c['gain'] for c in cc),sum(c['loss'] for c in cc),
            bool(missing) or any(c['possible_gain'] for c in cc),bool(missing) or any(c['possible_loss'] for c in cc))
        result['candidate_states'][label]=cs;result[name]=cs[0] if len(cs)==1 else 'unresolved'
    result['matrix_classifiable']=all(result[n]!='unresolved' for n in ('supported_change','hallucination_change'))
    if result['hallucination_change']!='unchanged':result['hallucination_unchanged_subtype']=None
    return result,events
