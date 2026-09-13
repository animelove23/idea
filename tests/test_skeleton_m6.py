import copy
import unittest
from analysis_skeleton.common import read_jsonl
from analysis_skeleton.m3_align import validate_alignment
from analysis_skeleton.m4_queue import build_queue
from analysis_skeleton.m6_analysis import analyze


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.c=read_jsonl('analysis_skeleton/fixtures/align_cases.jsonl')[1]
        self.al=validate_alignment(self.c['reference'],self.c['original'],self.c['steer'])
        self.q=build_queue('x',self.c['original'],self.c['steer'],self.al,'image.jpg')
    def calc(self,labels):return analyze(self.c['original'],self.c['steer'],self.al,self.q,labels)
    def test_hand_calculated_true_removal_and_new_hallucination(self):
        v=[{'claim_id':q['claim_id'],'label':'hallucinated' if q['upstream_status']=='added' else 'supported'} for q in self.q]
        r=self.calc(v)['metrics']
        self.assertEqual(r['entity']['true']['retained'],1)
        self.assertEqual(r['attribute']['true']['denominator'],1)
        self.assertEqual(r['attribute']['true']['removal_lower'],1)
        self.assertEqual(r['attribute']['added_by_truth'],{'hallucinated':1})
        self.assertEqual(r['conditional_true_attribute_retention']['lower'],0)
    def test_pending_not_false_and_zero_denominator_na(self):
        r=self.calc([])['metrics']
        self.assertEqual(r['attribute']['original_visual_pending'],1)
        self.assertIsNone(r['attribute']['true']['removal_lower'])
    def test_duplicate_verifier_output_rejected(self):
        v={'claim_id':self.q[0]['claim_id'],'label':'supported'}
        with self.assertRaises(ValueError):self.calc([v,v])
    def test_parent_attribute_truth_conflict_visible(self):
        v=[{'claim_id':q['claim_id'],'label':'hallucinated' if q['semantic_type']=='entity' else 'supported'} for q in self.q]
        r=self.calc(v)['metrics']
        self.assertEqual(r['attribute']['original_truth_conflict'],1)
        self.assertEqual(r['attribute']['true']['denominator'],0)
    def test_explicit_null_visual_result_stays_pending(self):
        r=self.calc([{'claim_id':q['claim_id'],'label':None} for q in self.q])['metrics']
        self.assertEqual(r['attribute']['original_visual_pending'],1)
    def test_duplicate_queue_claim_id_rejected(self):
        self.q[1]['claim_id']=self.q[0]['claim_id']
        with self.assertRaises(ValueError):self.calc([])
