"""Record both locator contexts without altering the actual repair_v1 visual query."""
from analysis_skeleton.repair_v1.context import build_queue as baseline_queue,SourceLocator
from analysis_skeleton.common import digest


def build_queue(pair_id,original,steer,alignment,image_path,image_sha256=None,lexical=None,locator=None):
    locator=locator or SourceLocator()
    queue=baseline_queue(pair_id,original,steer,alignment,image_path,image_sha256,lexical,locator)
    docs={'original':original,'steer':steer}
    for q in queue:
        contexts=[]
        for ref in q['refs']:
            d=docs[ref['side']];f=next(f for f in d['facts'] if f['id']==ref['fact_id'])
            e=next(e for e in d['entities'] if e['id']==f['entity_id'])
            context=locator.context(d,e,{'name':e['name'],'source_mentions':[m['quote'] for m in e['mentions']]})
            contexts.append({**ref,'context':context,'locator_status':'source_window_available' if 'source_window' in context else 'missing'})
        q['locator_audit']={'by_ref':contexts,'query_source_side':q['refs'][0]['side'],
                            'shared':len(contexts)>1,'shared_reason':'retained_under_frozen_contract' if len(contexts)>1 else None,
                            'contexts_exactly_equal':len({digest(c['context']) for c in contexts})==1,
                            'visual_same_referent_verified':False}
    return queue
