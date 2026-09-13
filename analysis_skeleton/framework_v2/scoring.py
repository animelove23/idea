"""Expose exact correspondences from the frozen repair_v1 scorer, without new aliases."""
from analysis_skeleton.metrics import matching,overlap,normal
from analysis_skeleton.repair_v1.scoring import LemmaScorer


def correspondences(pred,ref,scorer):
    em=matching(pred['entities'],ref['entities'],
                lambda a,b:scorer.name(a['name'])==scorer.name(b['name']) and overlap(a['mentions'],b['mentions']))
    entity_map={pred['entities'][i]['id']:ref['entities'][j]['id'] for i,j in em}
    def same(a,b):
        values=scorer.name(a['value'])==scorer.name(b['value']) if a['type']==b['type']=='entity' else normal(a['value'])==normal(b['value'])
        return a['type']==b['type'] and a['slot']==b['slot'] and values and entity_map.get(a['entity_id'])==b['entity_id']
    pairs=matching(pred['facts'],ref['facts'],same)
    return {ref['facts'][j]['id']:pred['facts'][i]['id'] for i,j in pairs}
