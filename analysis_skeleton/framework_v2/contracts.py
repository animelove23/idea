"""Quarantine malformed JSON rows before applying the unchanged semantic contract."""
import copy
from analysis_skeleton.repair_v1.contracts import normalize_document as baseline_document
from analysis_skeleton.repair_v1.alignment import validate_alignment as baseline_alignment


def normalize_document(raw,text,caption_id='caption'):
    if not isinstance(raw,dict) or any(not isinstance(raw.get(k),list) for k in ('entities','attributes','excluded')):
        raise ValueError('document_arrays_required')
    clean=copy.deepcopy(raw);issues=[];blocked_ids=set()
    for group in ('entities','attributes','excluded'):
        accepted=[]
        for row in clean[group]:
            valid=isinstance(row,dict)
            if group!='excluded':valid=valid and isinstance(row.get('id'),str)
            if group=='attributes':
                valid=valid and isinstance(row.get('entity_id'),str) and isinstance(row.get('slot'),str)
            if group=='excluded':valid=valid and isinstance(row.get('reason'),str)
            if valid:accepted.append(row)
            else:
                issues.append({'kind':group+'_schema_invalid','raw':row,'reason':'invalid_field_type'})
                if group!='excluded' and isinstance(row,dict) and isinstance(row.get('id'),str):blocked_ids.add(row['id'])
        clean[group]=accepted
    for group in ('entities','attributes'):
        conflicting=[r for r in clean[group] if r['id'] in blocked_ids]
        clean[group]=[r for r in clean[group] if r['id'] not in blocked_ids]
        issues += [{'kind':group+'_schema_invalid','raw':r,'reason':'ID_conflicts_with_invalid_row'} for r in conflicting]
    doc=baseline_document(clean,text,caption_id)
    if issues:
        doc['issues']+=issues;doc['status']='needs_review'
    return doc


def validate_alignment(raw,original,steer):
    if not isinstance(raw,dict) or any(not isinstance(raw.get(k),list) for k in ('entities','alignments')):
        raise ValueError('alignment_arrays_required')
    clean=copy.deepcopy(raw);issues=[]
    for group in ('entities','alignments'):
        rows=clean[group];bad=[];blocked=set()
        def ids(row):
            return {(side,i) for side in ('original','steer')
                    for i in (row.get(side,[]) if isinstance(row,dict) and isinstance(row.get(side),list) else []) if isinstance(i,str)}
        for i,row in enumerate(rows):
            valid=isinstance(row,dict) and isinstance(row.get('status'),str)
            valid=valid and ('reason' not in row or isinstance(row['reason'],str))
            valid=valid and all(isinstance(row.get(s),list) and all(isinstance(v,str) for v in row[s]) for s in ('original','steer'))
            if not valid:bad.append(i);blocked|=ids(row)
        # A rejected row must not free its IDs and turn a conflicting link into a valid match.
        while True:
            more=[i for i,r in enumerate(rows) if i not in bad and ids(r)&blocked]
            if not more:break
            bad+=more
            for i in more:blocked|=ids(rows[i])
        clean[group]=[r for i,r in enumerate(rows) if i not in bad]
        issues += [{'stage':'entity' if group=='entities' else 'fact','raw':rows[i],
                    'reason':'invalid_field_type_or_connected_conflict'} for i in sorted(bad)]
    result=baseline_alignment(clean,original,steer)
    if issues:
        result['issues']+=issues;result['status']='needs_review'
    return result
