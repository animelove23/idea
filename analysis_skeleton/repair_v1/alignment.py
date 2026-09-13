"""M3 format-only canonicalization; never choose an identity or invent a relation."""
import copy
from analysis_skeleton.m3_align import validate_alignment as baseline_validate


def refs(row):
    if not isinstance(row,dict) or any(not isinstance(row.get(s),list) for s in ('original','steer')):return None
    if any(not isinstance(i,str) for s in ('original','steer') for i in row[s]):return None
    return {(s,i) for s in ('original','steer') for i in row[s]}


def canonical_rows(rows,kind):
    audit=[];split=[]
    one_sided={'original_only':'original','steer_only':'steer'} if kind=='entities' else {'removed':'original','added':'steer'}
    for row in rows:
        rr=refs(row)
        side=one_sided.get(row.get('status')) if isinstance(row,dict) else None
        other='steer' if side=='original' else 'original'
        if rr is not None and side and not row[other] and len(row[side])>1:
            split.extend({**row,side:[fid]} for fid in row[side])
            audit.append({'kind':'split_one_sided_batch','table':kind,'raw':row})
        else:split.append(row)
    # Connected overlapping unresolved sets express ambiguity, not multiple independent matchings.
    eligible={i for i,r in enumerate(split) if refs(r) and r.get('status')=='unresolved'
              and r.get('reason')!='extraction_gap' and not r.get('reason','').startswith('technical')}
    consumed=set();output=[]
    for i,row in enumerate(split):
        if i in consumed:continue
        if i not in eligible:output.append(row);continue
        members={i};component=refs(row)
        while True:
            more={j for j in eligible-members if refs(split[j])&component}
            if not more:break
            members|=more;component|=set().union(*(refs(split[j]) for j in more))
        # An overlap with a determined link or extraction-gap row is a conflict: leave it quarantined.
        conflict=any(j not in members and (refs(r) or set())&component for j,r in enumerate(split))
        if len(members)==1 or conflict:
            output.append(row);continue
        consumed|=members
        reasons=sorted({split[j].get('reason','') for j in members})
        merged={s:sorted(i for side,i in component if side==s) for s in ('original','steer')}
        merged.update(status='unresolved',reason=reasons[0] if len(reasons)==1 else 'combined_semantic_unresolved')
        output.append(merged)
        audit.append({'kind':'merge_overlapping_unresolved','table':kind,
                      'raw_rows':[split[j] for j in sorted(members)],'canonical':merged})
    return output,audit


def canonicalize(raw):
    if not isinstance(raw,dict) or any(not isinstance(raw.get(k),list) for k in ('entities','alignments')):return raw,[]
    result=copy.deepcopy(raw);audit=[]
    for key in ('entities','alignments'):
        result[key],events=canonical_rows(result[key],key);audit+=events
    return result,audit


def validate_alignment(raw,original,steer):
    canonical,audit=canonicalize(raw)
    result=baseline_validate(canonical,original,steer)
    result['format_audit']=audit
    return result
