"""M2 repair: quarantine invalid mentions, not an otherwise valid entity."""
import copy
from analysis_skeleton.contracts import normalize_document as baseline_normalize,quote_span


def normalize_document(raw,text,caption_id='caption'):
    if not isinstance(raw,dict) or not isinstance(raw.get('entities'),list):
        return baseline_normalize(raw,text,caption_id)
    cleaned=copy.deepcopy(raw);audit=[]
    for entity in cleaned['entities']:
        if not isinstance(entity,dict) or not isinstance(entity.get('mentions'),list):continue
        valid=[];invalid=[]
        for mention in entity['mentions']:
            try:quote_span(text,mention);valid.append(mention)
            except (ValueError,KeyError,TypeError) as exc:
                invalid.append({'mention':mention,'reason':str(exc)})
        # No guesses and no search for a substitute quote. All-invalid still fails baseline validation.
        if valid and invalid:
            audit.append({'entity_id':entity.get('id'),'kind':'invalid_mentions_quarantined',
                          'valid_mentions_kept':len(valid),'quarantined':invalid})
            entity['mentions']=valid
    doc=baseline_normalize(cleaned,text,caption_id)
    doc['source_audit']=audit
    return doc
