import copy
import unittest
from analysis_skeleton.build_fixtures import D,E,A,q
from analysis_skeleton.contracts import normalize_document as original_normalize
from analysis_skeleton.repair_v1.contracts import normalize_document
from analysis_skeleton.repair_v1.alignment import canonicalize,validate_alignment
from analysis_skeleton.repair_v1.context import SourceLocator
from analysis_skeleton.common import read_jsonl


class MentionRepairTests(unittest.TestCase):
    def test_one_bad_mention_keeps_entity_and_bound_attribute(self):
        raw=D([E('e1','car','car',q('car',9))],[A('a1','e1','color','red','red car','red')])
        d=normalize_document(raw,'A red car.')
        self.assertEqual(len(d['facts']),2);self.assertFalse(d['issues'])
        self.assertEqual(len(d['source_audit']),1)
        self.assertEqual(len(raw['entities'][0]['mentions']),2)
    def test_all_invalid_not_invented(self):
        d=normalize_document(D([E('e1','car','missing')]),'A car.')
        self.assertFalse(d['facts']);self.assertTrue(d['issues'])
    def test_duplicate_entity_ids_still_quarantined(self):
        d=normalize_document(D([E('e1','car','car'),E('e1','dog','dog')]),'A car and a dog.')
        self.assertFalse(d['facts'])
    def test_valid_document_unchanged(self):
        raw=D([E('e1','car','car')]);new=normalize_document(raw,'A car.')
        self.assertEqual(new.pop('source_audit'),[])
        self.assertEqual(new,original_normalize(raw,'A car.'))


class AlignmentRepairTests(unittest.TestCase):
    def setUp(self):
        self.o=original_normalize(D([E('a','car','car'),E('b','dog','dog')]),'A car and a dog.')
        self.s=original_normalize(D([]),'')
    def test_batch_removed_split_without_new_decision(self):
        raw={'entities':[{'original':['a','b'],'steer':[],'status':'original_only'}],
             'alignments':[{'original':['entity_a','entity_b'],'steer':[],'status':'removed'}]}
        result=validate_alignment(raw,self.o,self.s)
        self.assertFalse(result['issues']);self.assertEqual(len(result['alignments']),2)
        self.assertEqual({r['status'] for r in result['alignments']},{'removed'})
    def test_only_unresolved_overlap_can_merge(self):
        raw={'entities':[{'original':['a'],'steer':['c'],'status':'unresolved','reason':'identity_unclear'},
                         {'original':['b'],'steer':['c'],'status':'unresolved','reason':'identity_unclear'}],
             'alignments':[]}
        result,audit=canonicalize(raw)
        self.assertEqual(len(result['entities']),1)
        self.assertEqual(result['entities'][0]['original'],['a','b'])
        self.assertEqual(result['entities'][0]['status'],'unresolved')
    def test_conflicting_determinate_link_not_merged(self):
        raw={'entities':[{'original':['a'],'steer':['c'],'status':'unresolved'},
                         {'original':['b'],'steer':['c'],'status':'matched'}],'alignments':[]}
        result,audit=canonicalize(raw)
        self.assertEqual(result,raw);self.assertFalse(audit)
    def test_invalid_id_not_guessed(self):
        raw={'entities':[{'original':['a','unknown'],'steer':[],'status':'original_only'}],
             'alignments':[{'original':['entity_a','bad'],'steer':[],'status':'removed'}]}
        result=validate_alignment(raw,self.o,self.s)
        self.assertTrue(result['issues'])
        self.assertEqual({i for r in result['alignments'] for i in r['original']},{'entity_a','entity_b'})
    def test_original_fewshot_still_valid(self):
        for ex in read_jsonl('analysis_skeleton/shots/align.jsonl'):
            self.assertFalse(validate_alignment(ex['output'],ex['input']['original'],ex['input']['steer'])['issues'])


class ContextRepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.locator=SourceLocator()
    def test_owner_context_and_exact_span_without_labels(self):
        text='Several people wait. A girl wears a pink shirt.'
        d=original_normalize(D([E('e1','shirt','shirt')]),text)
        result=self.locator.context(d,d['entities'][0],{'name':'shirt','source_mentions':['shirt']})
        self.assertIn('A girl wears',result['source_window'])
        span=result['target_mention']
        self.assertEqual(result['source_window'][span['start']:span['end']],'shirt')
        self.assertNotIn('label',result);self.assertNotIn('status',result)
    def test_window_limited_to_current_and_previous_sentence(self):
        text='A dog runs. A cat sits. A man holds a cup. The sky is clear.'
        d=original_normalize(D([E('e1','cup','cup')]),text)
        result=self.locator.context(d,d['entities'][0],{})
        self.assertNotIn('dog',result['source_window']);self.assertNotIn('sky',result['source_window'])
