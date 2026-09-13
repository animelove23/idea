"""Resolve a misindexed verbatim value only when its supplied evidence is unique."""
import copy
from analysis_skeleton.contracts import quote_span
from analysis_skeleton.framework_v2.contracts import normalize_document

def normalize_with_value_anchors(raw,text,caption_id='caption'):
    clean=copy.deepcopy(raw);repairs=[];ambiguous=[]
    if isinstance(clean,dict) and isinstance(clean.get('attributes'),list):
        for row in clean['attributes']:
            if not isinstance(row,dict) or not isinstance(row.get('evidence'),list) or not isinstance(row.get('value_quotes'),list):continue
            try:evidence=[quote_span(text,q) for q in row['evidence']]
            except (ValueError,KeyError,TypeError):continue
            if not evidence:continue
            def inside(span):return any(e['start']<=span['start'] and span['end']<=e['end'] for e in evidence)
            for index,q in enumerate(row['value_quotes']):
                if not isinstance(q,dict) or not isinstance(q.get('quote'),str) or not q['quote'] or type(q.get('occurrence')) is not int or q['occurrence']<0:continue
                try:current=quote_span(text,q)
                except (ValueError,KeyError,TypeError):current=None
                if current is not None and inside(current):continue
                candidates=[];occ=0
                while True:
                    try:span=quote_span(text,{'quote':q['quote'],'occurrence':occ})
                    except ValueError:break
                    if inside(span):candidates.append(span)
                    occ+=1
                if len(candidates)==1:
                    candidate=candidates[0];replacement={**q,'occurrence':candidate['occurrence']}
                    repairs.append({'attribute_id':row.get('id'),'field_index':index,'before':copy.deepcopy(q),'after':replacement,'resolved_span':candidate,'rule':'same_verbatim_value_unique_within_supplied_evidence'})
                    row['value_quotes'][index]=replacement
                elif len(candidates)>1:ambiguous.append({'attribute_id':row.get('id'),'field_index':index,'candidate_count':len(candidates)})
    doc=normalize_document(clean,text,caption_id)
    doc['value_anchor_audit']={'repairs':repairs,'ambiguous_not_repaired':ambiguous,'new_model_calls':0}
    return doc
