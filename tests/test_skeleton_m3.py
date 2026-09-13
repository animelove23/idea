import copy
import unittest
from analysis_skeleton.common import read_jsonl
from analysis_skeleton.m3_align import validate_alignment,score_alignment


class AlignmentTests(unittest.TestCase):
    def setUp(self):
        self.case=read_jsonl('analysis_skeleton/fixtures/align_cases.jsonl')[0]
    def validate(self,raw):return validate_alignment(raw,self.case['original'],self.case['steer'])
    def test_bad_fact_id_does_not_erase_entity_link(self):
        raw=copy.deepcopy(self.case['reference']);raw['alignments'][1]['steer']=['missing']
        result=self.validate(raw)
        self.assertEqual(result['alignments'][0]['status'],'retained')
        self.assertEqual(sum(len(r['original'])+len(r['steer']) for r in result['alignments']),4)
        self.assertTrue(result['issues'])
    def test_duplicate_fact_not_double_counted(self):
        raw=copy.deepcopy(self.case['reference']);raw['alignments'].append(copy.deepcopy(raw['alignments'][1]))
        result=self.validate(raw)
        self.assertEqual(sum(len(r['original']) for r in result['alignments']),2)
        self.assertEqual(sum(len(r['steer']) for r in result['alignments']),2)
    def test_unknown_subject_prevents_false_modification(self):
        raw=copy.deepcopy(self.case['reference']);raw['entities'][0]['status']='unresolved'
        result=self.validate(raw)
        self.assertTrue(all(r['status']=='unresolved' for r in result['alignments']))
    def test_technical_unresolved_gets_no_free_credit(self):
        result=self.validate({'entities':[],'alignments':[]})
        score=score_alignment(result,self.case['reference'])
        self.assertEqual(score['joint']['tp'],0)
        self.assertEqual(score['joint']['reference'],2)
        self.assertEqual(score['technical_fact_count'],4)
    def test_all_frozen_examples_valid(self):
        for ex in read_jsonl('analysis_skeleton/shots/align.jsonl'):
            self.assertFalse(validate_alignment(ex['output'],ex['input']['original'],ex['input']['steer'])['issues'])
    def test_matched_entity_cannot_be_removed_and_added(self):
        raw=copy.deepcopy(self.case['reference']);e=raw['alignments'].pop(0)
        raw['alignments'] += [{'original':e['original'],'steer':[],'status':'removed'},
                              {'original':[],'steer':e['steer'],'status':'added'}]
        r=self.validate(raw)
        self.assertFalse(any(x['status'] in {'removed','added'} for x in r['alignments']))
        self.assertEqual(len(r['issues']),2)
