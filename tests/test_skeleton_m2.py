import copy
import json
import unittest
from analysis_skeleton.build_fixtures import E,A,D
from analysis_skeleton.common import read_jsonl
from analysis_skeleton.contracts import normalize_document,quote_span
from analysis_skeleton.metrics import score_documents
from analysis_skeleton.llm import FewShotStage,CallFailure


class DecompositionTests(unittest.TestCase):
    def test_frozen_shots_all_valid(self):
        shots=read_jsonl('analysis_skeleton/shots/decompose.jsonl')
        self.assertEqual(len(shots),8)
        for s in shots:
            self.assertFalse(normalize_document(s['output'],s['input']['text'])['issues'])

    def test_invalid_attribute_does_not_destroy_entity(self):
        raw=D([E('e1','car','car')],[A('a1','e1','state','parked','car','car')])
        doc=normalize_document(raw,'A car.')
        self.assertEqual(len(doc['facts']),1)
        self.assertEqual(doc['status'],'needs_review')

    def test_repeated_quote_requires_correct_occurrence(self):
        self.assertEqual(quote_span('red car and red bus',{'quote':'red','occurrence':1})['start'],12)
        with self.assertRaises(ValueError):
            quote_span('carpet',{'quote':'car','occurrence':0})

    def test_subject_binding_not_just_color(self):
        text='A red car and a blue bus.'
        ref=D([E('e1','car','car'),E('e2','bus','bus')],[A('a1','e1','color','red','red car','red')])
        pred=copy.deepcopy(ref);pred['attributes'][0]['entity_id']='e2'
        scores=score_documents(normalize_document(pred,text),normalize_document(ref,text))
        self.assertEqual(scores['by_type']['attribute']['tp'],0)

    def test_one_request_and_eight_shots(self):
        calls=[]
        def transport(body):
            calls.append(body)
            return {'model':'test','choices':[{'finish_reason':'stop','message':{'content':json.dumps(D([]))}}]}
        stage=FewShotStage('decompose',transport=transport)
        stage.run({'text':'No relevant description.'})
        self.assertEqual(len(calls),1)
        self.assertEqual(len(calls[0]['messages']),18)
        self.assertEqual(calls[0]['thinking'],{'type':'disabled'})
        self.assertNotIn('image',calls[0]['messages'][-1]['content'])

    def test_truncated_response_not_repaired(self):
        calls=[]
        def transport(body):
            calls.append(1);return {'choices':[{'finish_reason':'length','message':{'content':'{}'}}]}
        with self.assertRaises(CallFailure):
            FewShotStage('decompose',transport=transport).run({'text':'A car.'})
        self.assertEqual(len(calls),1)
