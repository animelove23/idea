import copy,unittest
from analysis_skeleton.common import read_jsonl
from analysis_skeleton.evidence_verifier_v1.stage import make_evidence_shots
from analysis_skeleton.evidence_verifier_v1.compiler import compile_evidence

class CompilerTests(unittest.TestCase):
    def setUp(self):self.raw=make_evidence_shots(read_jsonl('analysis_skeleton/shots/verify.jsonl'))[3]['output']
    def test_absent_property_not_applicable_is_hallucinated(self):
        raw={**self.raw,'candidate_status':'not_found','bbox':None,'attribute_status':'not_applicable'}
        result=compile_evidence(raw,'attribute');self.assertEqual(result['label'],'hallucinated');self.assertEqual(result['evidence'],raw)
    def test_alternative_property_not_applicable_is_hallucinated(self):
        result=compile_evidence({**self.raw,'candidate_status':'alternative','attribute_status':'not_applicable'},'attribute')
        self.assertEqual(result['label'],'hallucinated')
    def test_ambiguous_referent_property_not_applicable_is_uncertain(self):
        result=compile_evidence({**self.raw,'candidate_status':'unresolved','limitation':'ambiguous_identity','attribute_status':'not_applicable'},'attribute')
        self.assertEqual(result['label'],'uncertain')
    def test_matching_referent_cannot_omit_property_and_other_errors_still_fail(self):
        with self.assertRaises(ValueError):compile_evidence({**self.raw,'attribute_status':'not_applicable'},'attribute')
        with self.assertRaises(ValueError):compile_evidence({**self.raw,'candidate_status':'alternative','bbox':None,'attribute_status':'not_applicable'},'attribute')

if __name__=='__main__':unittest.main()
