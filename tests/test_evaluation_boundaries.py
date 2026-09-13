import copy
import unittest
from collections import Counter
from tests.test_evaluation import doc,entity_response,fact_response
from evaluation.alignment import align_entities,align_facts


def duplicate_case(speculative=False):
    a,b=doc(),doc()
    f=copy.deepcopy(a['facts'][2]);f['id']='f5'
    if speculative:
        a['text']+=' The cup appears white.'
        f.update(fact='The cup appears white.',source='The cup appears white',assertion='speculative')
    a['facts'].append(f)
    e=entity_response();e['original_entities'][0]['fact_ids'].append('f5')
    p=fact_response();p['original_bindings'].append({'fact_id':'f5','entity_ids':['o1'],'slot':'color'})
    return a,b,align_entities(e,a,b),p


class BoundaryTests(unittest.TestCase):
    def test_relation_labels_do_not_veto_model_semantic_match(self):
        p=fact_response();p['original_bindings'][3]['slot']='rests_on';p['steer_bindings'][3]['slot']='is_on'
        r=align_facts(p,doc(),doc(),align_entities(entity_response(),doc(),doc()))
        self.assertEqual(r['status'],'ready')
        self.assertEqual(r['fact_alignment'][3]['status'],'retained')
        self.assertTrue(any(w['rule']=='different_slot_labels' for w in r['warnings']))

    def test_explicit_category_not_arbitrary_slot_determines_color_dimension(self):
        p=fact_response();p['steer_bindings'][2]['slot']='age'
        r=align_facts(p,doc(),doc(),align_entities(entity_response(),doc(),doc()))
        self.assertEqual(r['status'],'ready')
        self.assertTrue(any(w['rule']=='different_slot_labels' for w in r['warnings']))

    def test_repeated_valid_source_is_not_unknown_referent(self):
        a,b=doc(),doc();a['text']+=' The cup is here.';a['facts'][0]['source_status']='ambiguous'
        r=align_facts(fact_response(),a,b,align_entities(entity_response(),a,b))
        self.assertEqual(r['status'],'ready')
        self.assertTrue(any(w['rule']=='repeated_source_occurrence' for w in r['warnings']))

    def test_absent_source_still_rejected(self):
        a,b=doc(),doc();a['facts'][0]['source']='nonexistent elephant'
        r=align_facts(fact_response(),a,b,align_entities(entity_response(),a,b))
        self.assertTrue(any('source must occur' in x['error'] for x in r['rejected_alignments']))

    def test_correct_primary_survives_qualified_contextual_reference(self):
        a,b,sidecar,p=duplicate_case(True)
        p['fact_alignment'].append({'original_fact_ids':['f5'],'steer_fact_ids':['f3'],'status':'ambiguous','reason':'qualifier_difference','evidence':[]})
        r=align_facts(p,a,b,sidecar)
        primary=next(x for x in r['fact_alignment'] if 'f3' in x['original_fact_ids'])
        self.assertEqual(primary['status'],'retained')
        self.assertEqual(primary['steer_fact_ids'],['f3'])
        extra=next(x for x in r['fact_alignment'] if 'f5' in x['original_fact_ids'])
        self.assertEqual(extra['status'],'ambiguous')
        ref=r['related_correspondences'][0]
        self.assertFalse(ref['counted_as_primary_alignment'])
        self.assertEqual(ref['qualifiers']['original'][0]['assertion'],'speculative')
        self.assertEqual(ref['qualifiers']['steer'][0]['assertion'],'asserted')
        for side,d in [('original',a),('steer',b)]:
            self.assertEqual(Counter(fid for x in r['fact_alignment'] for fid in x[side+'_fact_ids']),Counter(f['id'] for f in d['facts']))

    def test_exact_duplicate_facts_share_one_retained_group(self):
        a,b,sidecar,p=duplicate_case()
        p['fact_alignment'].append({'original_fact_ids':['f5'],'steer_fact_ids':['f3'],'status':'retained','reason':'same_fact','evidence':[]})
        r=align_facts(p,a,b,sidecar)
        group=next(x for x in r['fact_alignment'] if 'f5' in x['original_fact_ids'])
        self.assertEqual(set(group['original_fact_ids']),{'f3','f5'})
        self.assertEqual(group['steer_fact_ids'],['f3'])
        self.assertTrue(group['equivalent_fact_group'])
        self.assertEqual(group['semantic_unit_count'],1)

    def test_explicit_equivalent_group_allows_multiple_references(self):
        a,b,sidecar,p=duplicate_case()
        p['fact_alignment'][2]['original_fact_ids'].append('f5')
        r=align_facts(p,a,b,sidecar)
        self.assertEqual(r['status'],'ready')
        self.assertTrue(r['fact_alignment'][2]['equivalent_fact_group'])

    def test_qualified_statements_cannot_be_silently_collapsed_as_retained(self):
        a,b,sidecar,p=duplicate_case(True)
        p['fact_alignment'][2]['original_fact_ids'].append('f5')
        r=align_facts(p,a,b,sidecar)
        self.assertTrue(any(x['rule']=='modality_or_polarity_changed' for x in r['semantic_reviews']))
        self.assertFalse(r['rejected_alignments'])

    def test_two_distinct_values_do_not_auto_merge(self):
        a,b,sidecar,p=duplicate_case();a['facts'][-1]['fact']='The cup is blue.'
        p['fact_alignment'].append({'original_fact_ids':['f5'],'steer_fact_ids':['f3'],'status':'retained','reason':'same_fact','evidence':[]})
        r=align_facts(p,a,b,sidecar)
        self.assertTrue(any('conflicting confident' in x['error'] for x in r['rejected_alignments']))

    def test_overlapping_uncertain_claims_group_without_forced_equivalence(self):
        a,b,sidecar,p=duplicate_case()
        p['fact_alignment'][2].update(status='ambiguous',reason='partial_overlap')
        p['fact_alignment'].append({'original_fact_ids':['f5'],'steer_fact_ids':['f3'],'status':'ambiguous','reason':'granularity','evidence':[]})
        r=align_facts(p,a,b,sidecar)
        group=next(x for x in r['fact_alignment'] if 'f5' in x['original_fact_ids'])
        self.assertEqual(group['status'],'ambiguous')
        self.assertEqual(set(group['original_fact_ids']),{'f3','f5'})
        self.assertFalse(r['rejected_alignments'])


if __name__=='__main__':unittest.main()
