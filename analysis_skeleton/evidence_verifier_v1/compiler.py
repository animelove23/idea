"""Versioned correction: a property can be N/A when its referent is unconfirmed."""
import copy
from .stage import validate_evidence

def compile_evidence(raw,claim_type):
    # Never bypass unrelated schema errors. No labels or reference answers are consulted.
    nonmatching=isinstance(raw,dict) and raw.get('candidate_status') in ('alternative','not_found','unresolved')
    if claim_type=='attribute' and nonmatching and raw.get('attribute_status')=='not_applicable':
        normalized=copy.deepcopy(raw);normalized['attribute_status']='unresolved'
        result=validate_evidence(normalized,claim_type)
        result['evidence']=copy.deepcopy(raw)
        result['compiler_note']='property_not_applicable_because_referent_not_established'
        return result
    return validate_evidence(raw,claim_type)
