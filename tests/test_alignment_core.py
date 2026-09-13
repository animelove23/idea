import copy
import unittest

from test_evaluation import doc, entity_response, fact_response
from evaluation.alignment import align_entities
from evaluation.alignment_core import align_core, fallback_alignments, review_core
from evaluation.build_core_examples import build
from evaluation.common import ContractError
from evaluation.core_metrics import score


class CoreAlignmentTests(unittest.TestCase):
    def test_uncertain_identity_is_excluded_other_not_modified(self):
        a,b=doc(),doc('blue');ent=entity_response();ent['entity_alignment'][0]['status']='ambiguous'
        result=align_core(fact_response(True),a,b,align_entities(ent,a,b))
        color=next(r for r in result['fact_alignment'] if r['original_fact_ids']==['f3'])
        self.assertEqual(color['status'],'other');self.assertFalse(color['in_main'])
        self.assertEqual(color['exclusion_reason'],'entity_uncertain')

    def test_same_subject_relation_new_target_is_modified(self):
        facts=[{'type':'relation','category':'spatial','assertion':'asserted','polarity':'positive'}]*2
        self.assertIsNone(review_core('modified',facts,[['g1','g2'],['g1','g3']],['above','above'])[0])
        self.assertIsNotNone(review_core('retained',facts,[['g1','g2'],['g1','g3']],['above','above'])[0])
        self.assertIsNotNone(review_core('modified',facts,[['g1','g2'],['g4','g3']],['above','above'])[0])

    def test_action_and_location_are_not_same_change_dimension(self):
        facts=[{'type':'relation','category':c,'assertion':'asserted','polarity':'positive'} for c in ('action','location')]
        self.assertIsNotNone(review_core('modified',facts,[['g1'],['g1']],['state','state'])[0])

    def test_count_population_difference_still_requires_review(self):
        facts=[{'type':'attribute','category':'counting','assertion':'asserted','polarity':'positive'}]*2
        self.assertEqual(review_core('modified',facts,[['g1'],['g1']],['count_people','count_skiers'])[0][1],'count_scope_changed')

    def test_public_protocol_rejects_old_fact_label(self):
        payload=fact_response();payload['fact_alignment'][2].update(status='ambiguous',reason='partial_overlap')
        with self.assertRaises(ContractError):align_core(payload,doc(),doc(),align_entities(entity_response(),doc(),doc()))

    def test_other_fact_type_is_excluded_even_if_model_says_retained(self):
        a,b=doc(),doc()
        for d in (a,b):d['facts'][2]['type']='other'
        result=align_core(fact_response(),a,b,align_entities(entity_response(),a,b))
        r=next(r for r in result['fact_alignment'] if 'f3' in r['original_fact_ids'])
        self.assertEqual(r['status'],'other');self.assertEqual(r['reason'],'other_scope');self.assertFalse(r['in_main'])

    def test_failed_stages_do_not_enter_main_counts(self):
        rows=fallback_alignments(doc(),doc())
        self.assertTrue(all(r['status']=='other' and not r['in_main'] and r['reason']=='stage_failed' for r in rows))

    def test_core_demonstrations_preserve_inputs_and_phase_change(self):
        cases=build();self.assertEqual(len(cases),8)
        for c in cases:
            before=copy.deepcopy(c['input'])
            r=align_core(c['output'],c['input']['original'],c['input']['steer'],c['input']['entity_sidecar'])
            self.assertEqual(c['input'],before)
            self.assertNotIn('ambiguous',{row['status'] for row in r['fact_alignment']})
        c=next(c for c in cases if c['id']=='pianist_event_phase')
        self.assertEqual(c['output']['fact_alignment'][-1]['status'],'modified')

    def test_excluding_everything_cannot_improve_core_recall(self):
        def r(a,b,status):return dict(original_fact_ids=a,steer_fact_ids=b,status=status,reason='same_fact',survival_in_opposite_caption='present')
        gold=[{'pair_id':'x','fact_alignment':[r(['f1'],['f1'],'retained'),r(['f2'],['f2'],'modified'),r(['f3'],['f3'],'other')]}]
        pred=copy.deepcopy(gold)
        for row in pred[0]['fact_alignment']:row.update(status='other',reason='entity_uncertain')
        m,_,_=score(gold,pred)
        self.assertEqual(m['core_edge']['recall'],0)
        self.assertEqual(m['core_status_macro_f1'],0)
        self.assertEqual(m['exclusions']['false_exclusions'],4)
        self.assertEqual(m['exclusions']['predicted_other_rate'],1)

    def test_core_prediction_on_gold_other_is_false_positive(self):
        gold=[{'pair_id':'x','fact_alignment':[dict(original_fact_ids=['f1'],steer_fact_ids=['f1'],status='other',reason='entity_uncertain',survival_in_opposite_caption='uncertain')]}]
        pred=copy.deepcopy(gold);pred[0]['fact_alignment'][0].update(status='modified',reason='value_changed')
        m,_,_=score(gold,pred)
        self.assertEqual(m['core_edge']['predicted'],1);self.assertEqual(m['core_edge']['tp'],0)


if __name__=='__main__':unittest.main()
