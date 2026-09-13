import copy
import json
import unittest
from analysis_skeleton.build_fixtures import D,E
from analysis_skeleton.common import read_jsonl
from analysis_skeleton.framework_v2.contracts import normalize_document,validate_alignment
from analysis_skeleton.repair_v1.contracts import normalize_document as old_document
from analysis_skeleton.repair_v1.alignment import validate_alignment as old_alignment


class ContractsTests(unittest.TestCase):
    def test_null_reason_is_local_and_cannot_free_conflicting_id(self):
        o=normalize_document(D([E('a','car','car'),E('b','dog','dog')]),'A car and a dog.')
        s=normalize_document(D([E('c','car','car')]),'A car.')
        raw={'entities':[{'original':['a'],'steer':['c'],'status':'unresolved','reason':None},
                         {'original':['a'],'steer':['c'],'status':'matched'},
                         {'original':['b'],'steer':[],'status':'original_only'}],
             'alignments':[{'original':['entity_a'],'steer':['entity_c'],'status':'retained'},
                           {'original':['entity_b'],'steer':[],'status':'removed'}]}
        r=validate_alignment(raw,o,s)
        self.assertTrue(r['issues'])
        self.assertFalse(any(e['status']=='matched' for e in r['entities']))
        self.assertTrue(any(e['original']==['entity_b'] and e['status']=='removed' for e in r['alignments']))
        self.assertIsNone(raw['entities'][0]['reason'])

    def test_non_string_values_do_not_crash_batch(self):
        raw=D([E('a','car','car'),{'id':['bad'],'name':'car','mentions':[]}])
        raw['attributes']=[{'id':'x','entity_id':{},'slot':[]}]
        raw['excluded']=[None,{'reason':[],'source':{}}]
        d=normalize_document(raw,'A car.')
        self.assertEqual(len(d['facts']),1);self.assertEqual(len(d['issues']),4)

    def test_malformed_outer_schema_is_failure_not_empty_document(self):
        for raw in (None,[],{}, {'entities':[],'attributes':None,'excluded':[]}):
            with self.assertRaises(ValueError):normalize_document(raw,'A car.')
    def test_rejected_attribute_row_does_not_free_duplicate_entity_id(self):
        raw=D([E('e1','car','car')]);raw['attributes']=[{'id':'e1','entity_id':[],'slot':'color'}]
        doc=normalize_document(raw,'A car.')
        self.assertFalse(doc['facts']);self.assertTrue(doc['issues'])

    def test_same_saved_m2_responses_exactly_preserved(self):
        records=read_jsonl('outputs/skeleton_expansion20/m2/results.jsonl')
        for r in records:
            d=r['document'];raw=json.loads(r['audit']['raw_content'])
            self.assertEqual(normalize_document(raw,d['text'],d['caption_id']),old_document(raw,d['text'],d['caption_id']))

    def test_same_saved_m3_responses_exactly_preserved(self):
        cases={r['case_id']:r for r in read_jsonl('analysis_skeleton/fixtures/expansion20/align_cases.jsonl')}
        for r in read_jsonl('outputs/skeleton_expansion20/m3_independent/results.jsonl'):
            c=cases[r['case_id']];raw=json.loads(r['audit']['raw_content'])
            self.assertEqual(validate_alignment(raw,c['original'],c['steer']),old_alignment(raw,c['original'],c['steer']))


if __name__=='__main__':unittest.main()
