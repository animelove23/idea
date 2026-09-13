import copy
import unittest
from analysis_skeleton.build_fixtures import D,E,A
from analysis_skeleton.framework_v2.contracts import normalize_document
from analysis_skeleton.framework_v2.scoring import LemmaScorer,correspondences
from analysis_skeleton.framework_v2.ledger import reference_ledger


class LedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.scorer=LemmaScorer()
    def test_missing_reference_fact_stays_in_denominator(self):
        ref=normalize_document(D([E('e1','car','car')],[A('a1','e1','color','red','red car','red')]),'A red car.','p_original')
        pred=normalize_document(D([E('x','car','car')]),'A red car.','p_original')
        empty=normalize_document(D([]),'','p_steer')
        rows,extra,scores=reference_ledger([ref],[{'pair_id':'p','original':pred,'steer':empty}],[],self.scorer)
        self.assertEqual(len(rows),2);self.assertFalse(extra)
        missing=next(r for r in rows if r['reference_fact_id']=='a1')
        self.assertEqual(missing['extraction_axis'],'extraction_missing')
        self.assertIsNone(missing['predicted_transition'])
        self.assertEqual(scores[0]['score']['joint']['reference'],2)
    def test_all_reference_facts_retained_if_entire_document_failed(self):
        ref=normalize_document(D([E('e','car','car')]),'A car.','missing')
        rows,_,_=reference_ledger([ref],[],[],self.scorer)
        self.assertEqual(len(rows),1);self.assertEqual(rows[0]['extraction_axis'],'extraction_missing')
    def test_duplicate_reference_cannot_silently_double_denominator(self):
        ref=normalize_document(D([E('e','car','car')]),'A car.','p')
        with self.assertRaises(ValueError):reference_ledger([ref,ref],[],[],self.scorer)
    def test_lemma_equivalence_does_not_credit_hypernym(self):
        a=normalize_document(D([E('a','dogs','dogs')]),'Two dogs.','p')
        b=normalize_document(D([E('b','dog','dogs')]),'Two dogs.','p')
        self.assertEqual(len(correspondences(a,b,self.scorer)),1)
        b['entities'][0]['name']='animal';b['facts'][0]['value']='animal'
        self.assertEqual(len(correspondences(a,b,self.scorer)),0)
    def test_attribute_binding_swap_cannot_earn_credit(self):
        raw=D([E('a','car','car'),E('b','bench','bench')],[A('x','a','color','red','red car','red')])
        ref=normalize_document(raw,'A red car by a bench.','p');pred=copy.deepcopy(ref)
        pred['facts'][-1]['entity_id']='b'
        self.assertEqual(len(correspondences(pred,ref,self.scorer)),2)
        self.assertEqual(self.scorer.score(pred,ref)['by_type']['attribute']['tp'],0)


if __name__=='__main__':unittest.main()
