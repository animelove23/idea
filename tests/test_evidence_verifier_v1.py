import copy,tempfile,unittest
from pathlib import Path
from analysis_skeleton.common import read_jsonl,write_jsonl
from analysis_skeleton.evidence_verifier_v1.stage import validate_evidence,make_evidence_shots,EvidenceStage

class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.shots=make_evidence_shots(read_jsonl('analysis_skeleton/shots/verify.jsonl'))
        self.entity=copy.deepcopy(self.shots[0]['output']);self.attribute=copy.deepcopy(self.shots[3]['output'])
    def test_six_examples_keep_original_labels_and_inputs(self):
        original=read_jsonl('analysis_skeleton/shots/verify.jsonl')
        for old,new in zip(original,self.shots):
            self.assertEqual(old['input'],new['input']);self.assertEqual(old['image_id'],new['image_id'])
            self.assertEqual(validate_evidence(new['output'],new['semantic_type'])['label'],old['output']['label'])
    def test_inspected_absence_is_hallucinated_but_limited_search_is_uncertain(self):
        r={**self.entity,'candidate_status':'not_found','bbox':None,'observed_category':'none'}
        self.assertEqual(validate_evidence(r,'entity')['label'],'hallucinated')
        r.update(region_status='limited',limitation='occlusion')
        self.assertEqual(validate_evidence(r,'entity')['label'],'uncertain')
    def test_identifiable_alternative_has_explicit_rule(self):
        r=validate_evidence(self.shots[1]['output'],'entity')
        self.assertEqual(r['label'],'hallucinated');self.assertEqual(r['decision_rule'],'visible_alternative_or_inspected_absence')
    def test_attribute_supported_cannot_override_ambiguous_referent(self):
        r={**self.attribute,'candidate_status':'unresolved','limitation':'ambiguous_identity'}
        v=validate_evidence(r,'attribute');self.assertEqual(v['label'],'uncertain');self.assertTrue(v['attribute_support_blocked_by_referent'])
    def test_attribute_of_absent_or_wrong_category_is_not_supported(self):
        for state,box in [('alternative',[1,1,99,99]),('not_found',None)]:
            v=validate_evidence({**self.attribute,'candidate_status':state,'bbox':box},'attribute')
            self.assertEqual(v['label'],'hallucinated');self.assertTrue(v['attribute_support_blocked_by_referent'])
    def test_grayscale_attribute_is_uncertain_and_bbox_is_not_verified(self):
        v=validate_evidence(self.shots[5]['output'],'attribute')
        self.assertEqual(v['label'],'uncertain');self.assertFalse(v['bbox_verified'])
    def test_invalid_boxes_and_claim_types_are_technical_not_uncertain(self):
        for box in ([True,0,10,10],[0,0,1001,1000],[20,20,10,10],None):
            with self.assertRaises(ValueError):validate_evidence({**self.entity,'bbox':box},'entity')
        with self.assertRaises(ValueError):validate_evidence(self.entity,'attribute')
    def test_model_label_or_missing_fields_are_rejected(self):
        with self.assertRaises(ValueError):validate_evidence({**self.entity,'label':'supported'},'entity')
        r=copy.deepcopy(self.entity);del r['visible_cues']
        with self.assertRaises(ValueError):validate_evidence(r,'entity')
    def test_bad_enum_types_and_unexplained_uncertainty_are_rejected(self):
        for k in ('candidate_status','region_status','limitation','attribute_status'):
            with self.assertRaises(ValueError):validate_evidence({**self.entity,k:[]},'entity')
        with self.assertRaises(ValueError):validate_evidence({**self.entity,'candidate_status':'unresolved'},'entity')
    def test_six_image_fewshot_messages_have_no_final_labels(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'shots.jsonl';write_jsonl(p,self.shots);stage=EvidenceStage(p)
            query={**self.shots[0]['input'],'claim_type':'entity'};messages=stage.messages(query)
            self.assertEqual(len(messages),14)
            self.assertEqual(sum(m['role']=='assistant' for m in messages),6)
            self.assertTrue(all('"label"' not in m['content'] for m in messages if m['role']=='assistant'))
            self.assertEqual(len([p for p in messages[-1]['content'] if p['type']=='image_url']),1)

if __name__=='__main__':unittest.main()
