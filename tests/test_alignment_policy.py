import copy
import unittest
from evaluation.alignment import align_entities,align_facts
from evaluation.alignment_policy import semantic_review
from evaluation.common import ContractError
from tests.test_evaluation import doc,entity_response,fact_response


def f(category='spatial',kind='relation',assertion='asserted'):
    return dict(type=kind,category=category,assertion=assertion,polarity='positive')


class PolicyTests(unittest.TestCase):
    def test_ambiguous_entity_candidates_union_without_losing_certain_matches(self):
        p=entity_response();p['original_entities'].append(dict(id='o3',mention='cup',fact_ids=['f1'],description='candidate'))
        p['entity_alignment'][0]['status']='ambiguous'
        p['entity_alignment'].append(dict(original_entity_ids=['o3'],steer_entity_ids=['s1'],status='ambiguous',reason='second candidate'))
        e=align_entities(p,doc(),doc())
        self.assertIsNone(e['global_mapping']['original']['o1'])
        self.assertIsNone(e['global_mapping']['original']['o3'])
        self.assertEqual(e['global_mapping']['original']['o2'],e['global_mapping']['steer']['s2'])
        self.assertEqual(len(e['entity_alignment']),2)
    def test_conflicting_confident_entity_edges_are_localized_not_chosen(self):
        p=entity_response();p['entity_alignment'].append(dict(original_entity_ids=['o1'],steer_entity_ids=['s2'],status='matched',reason='conflicting proposal'))
        e=align_entities(p,doc(),doc())
        self.assertTrue(all(v is None for side in e['global_mapping'].values() for v in side.values()))
        self.assertEqual(e['resolution_notes'][0]['rule'],'localize_entity_conflict')
    def test_unknown_entity_id_still_fails(self):
        p=entity_response();p['entity_alignment'][0]['original_entity_ids']=['fake']
        with self.assertRaises(ContractError):align_entities(p,doc(),doc())
    def test_reverse_direction_requires_inverse_relation(self):
        r,_=semantic_review('retained',[f(),f()],[['a','b'],['b','a']],['above','above'])
        self.assertEqual(r[0],'partial_overlap')
        r,w=semantic_review('retained',[f(),f()],[['a','b'],['b','a']],['above','below'])
        self.assertIsNone(r);self.assertTrue(w)
    def test_collection_permutation_preserves_reference_role(self):
        r,w=semantic_review('retained',[f(),f()],[['a','b','c','room'],['c','a','b','room']],['scattered_in']*2)
        self.assertIsNone(r);self.assertTrue(w)
        r,_=semantic_review('retained',[f(),f()],[['a','b','c','room'],['room','a','b','c']],['scattered_in']*2)
        self.assertIsNotNone(r)
    def test_material_to_color_is_semantic_review_not_technical_rejection(self):
        r,_=semantic_review('modified',[f('material','attribute'),f('color','attribute')],[['a'],['a']],['material','color'])
        self.assertEqual(r,('granularity','different_attribute_dimensions'))
    def test_count_scope_not_erased(self):
        r,_=semantic_review('modified',[f('counting','attribute')]*2,[['a'],['a']],['count_people','count_people_skiing'])
        self.assertEqual(r[0],'partial_overlap')
    def test_alias_slot_can_keep_modified(self):
        r,w=semantic_review('modified',[f('counting','attribute')]*2,[['a'],['a']],['quantity','count'])
        self.assertIsNone(r);self.assertTrue(w)
    def test_unmapped_scene_property_can_be_added(self):
        r,w=semantic_review('added',[f('attribute','attribute')],[[]],['weather'])
        self.assertIsNone(r);self.assertEqual(w[0]['rule'],'one_sided_caption_judgment')
    def test_uncertain_instance_color_loss_can_be_caption_judgment(self):
        r,w=semantic_review('removed',[f('color','attribute')],[[None]],['color'])
        self.assertIsNone(r);self.assertTrue(w)
    def test_uncertain_existence_loss_needs_review(self):
        r,_=semantic_review('removed',[f('object','entity')],[[None]],['existence'])
        self.assertEqual(r[0],'entity_uncertain')
    def test_uncertain_cross_caption_identity_preserves_proposed_pair(self):
        e=entity_response();e['entity_alignment'][0]['status']='ambiguous';d=doc()
        result=align_facts(fact_response(),d,d,align_entities(e,d,d))
        row=next(x for x in result['fact_alignment'] if 'f3' in x['original_fact_ids'])
        self.assertEqual(row['steer_fact_ids'],['f3']);self.assertEqual(row['reason'],'entity_uncertain')
        self.assertFalse(result['rejected_alignments']);self.assertTrue(result['semantic_reviews'])
    def test_retained_modality_change_is_not_silently_accepted(self):
        r,_=semantic_review('retained',[f(),f(assertion='speculative')],[['a'],['a']],['sit','sit'])
        self.assertEqual(r[0],'qualifier_difference')


if __name__=='__main__':unittest.main()
