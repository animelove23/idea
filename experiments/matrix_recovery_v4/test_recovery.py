import copy,json,unittest
from analysis_skeleton.common import read_jsonl
from experiments.entity_attribute_v3.m3 import validate
from experiments.coco400_revision_v2.visual import merge
from experiments.coco400_revision_v2.fixtures import doc
from analysis_skeleton.final_v1.routing import validate_typed
from .run import SOURCE,split_queue,recompute
from .stages import AlignStage


class RecoveryTests(unittest.TestCase):
    def test_eight_existing_probes_and_fact_coverage(self):
        for ex in read_jsonl('experiments/entity_attribute_v3/m3_probes.jsonl'):
            v=validate(ex['output'],**ex['input'])
            for side in ('original','steer'):
                refs=[f for e in v['alignments'] for f in e[side]]
                self.assertCountEqual(refs,[f['id'] for f in ex['input'][side]['facts']])
                self.assertEqual(len(refs),len(set(refs)))

    def test_unresolved_owner_keeps_attribute_semantic(self):
        a=doc('A wooden shelf is visible.','shelf',('wooden','material'));b=doc('A table is visible.','table')
        raw={'entities':[{'original':['e1'],'steer':['e1'],'status':'unresolved','description_change':'unresolved','reason':'ambiguous_identity'}],
             'attributes':[{'original':['a1'],'steer':[],'status':'unresolved','reason':'subject_identity_unresolved'}]}
        out=validate(raw,a,b)
        row=next(e for e in out['alignments'] if e['original']==['a1'])
        self.assertEqual(row['status'],'unresolved');self.assertFalse(row['reason'].startswith('technical'))

    def test_missing_row_is_never_deletion(self):
        d=doc('A red chair.','chair',('red','color'))
        out=validate({'entities':[],'attributes':[]},d,d)
        self.assertTrue(all(e['status']=='unresolved' for e in out['alignments']))

    def test_distinct_entities_can_be_two_absences(self):
        a=doc('A house.','house');b=doc('A carriage.','carriage')
        raw={'entities':[{'original':['e1'],'steer':[],'status':'original_only','description_change':'absent','reason':'distinct concept'},
                         {'original':[],'steer':['e1'],'status':'steer_only','description_change':'absent','reason':'distinct concept'}],'attributes':[]}
        self.assertEqual({e['status'] for e in validate(raw,a,b)['alignments']},{'removed','added'})

    def test_rebinding_preserves_every_fact_without_cross_referent_truth(self):
        r=next(r for r in read_jsonl(SOURCE) if any(len(q['refs'])>1 for q in r['queue']))
        before={(s,f['id']) for s in ('original','steer') for f in r['bundle'][s]['facts']}
        r['bundle']['alignment']=validate({'entities':[],'attributes':[]},r['bundle']['original'],r['bundle']['steer'])
        split_queue(r);recompute(r)
        after=[(ref['side'],ref['fact_id']) for q in r['queue'] for ref in q['refs']]
        self.assertEqual(set(after),before);self.assertEqual(len(after),len(before))
        self.assertTrue(any(v.get('needs_rebinding') and v['label'] is None for v in r['verification']))

    def test_visual_boundaries_are_unchanged(self):
        raw={'claim_type':'entity','candidate_status':'unresolved','region_status':'limited','bbox':None,
             'observed_category':'liquid','scope':'cup','visible_cues':'Liquid species cannot be seen.',
             'limitation':'category_boundary','attribute_status':'not_applicable'}
        self.assertEqual(validate_typed(raw,'entity')['label'],'uncertain')
        raw.update(candidate_status='not_found',region_status='inspectable',limitation='none',visible_cues='Inspected clear frame contains no claimed object.')
        self.assertEqual(validate_typed(raw,'entity')['label'],'hallucinated')
        self.assertEqual(merge({'label':'supported'},{'status':'complete','value':{'label':'hallucinated'}})['label'],'uncertain')

    def test_fixed_source_denominator(self):
        rows=read_jsonl(SOURCE)
        self.assertEqual(len(rows),400);self.assertEqual(sum(r['observation']['matrix_classifiable'] for r in rows),269)
        self.assertEqual(sum(len(r['ledger']) for r in rows),5959)

if __name__=='__main__':unittest.main()
