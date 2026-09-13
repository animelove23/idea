"""Separate a searched region from the absent object's target region."""
import copy
from .stage import compiled

def validate(raw,payload):
    value=copy.deepcopy(raw);audit=[]
    if not isinstance(value,dict) or not isinstance(value.get('regions'),list) or not isinstance(value.get('claims'),list):return compiled(value,payload)
    known={r.get('id') for r in value['regions'] if isinstance(r,dict) and isinstance(r.get('id'),str)}
    for row in value['claims']:
        if not isinstance(row,dict):continue
        ev=row.get('evidence',{});rid=row.get('region_id')
        if isinstance(ev,dict) and ev.get('candidate_status')=='not_found' and ev.get('bbox') is None and isinstance(rid,str) and rid in known:
            audit.append({'claim_id':row.get('claim_id'),'searched_region_id':rid,'target_region_id':None,
                'policy':'explicit_not_found_has_no_target; referenced_region_is_search_context'})
            row['region_id']=None
    result=compiled(value,payload);result['search_binding_audit']=audit
    return result
