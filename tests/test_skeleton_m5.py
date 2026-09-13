import unittest
from analysis_skeleton.common import read_jsonl
from analysis_skeleton.m5_verify import VisualStage,validate_label,score_labels


class VisualTests(unittest.TestCase):
    def test_images_in_fewshot_and_query_no_reference_leak(self):
        stage=VisualStage(transport=lambda body:None)
        c=read_jsonl('analysis_skeleton/fixtures/verify_cases.jsonl')[0]
        payload={**c['input'],'reference_label':'DO_NOT_SEND','method':'DO_NOT_SEND'}
        messages=stage.messages(payload)
        self.assertEqual(sum(m['role']=='user' for m in messages),7)
        self.assertEqual(sum(m['role']=='assistant' for m in messages),6)
        for m in messages:
            if m['role']=='user':self.assertEqual(m['content'][1]['type'],'image_url')
        self.assertNotIn('DO_NOT_SEND',messages[-1]['content'][0]['text'])
        self.assertEqual(stage.config.model,'deepseek-flash')
    def test_unknown_not_silently_false(self):
        with self.assertRaises(ValueError):validate_label({'label':'unknown','reason':'not sure'})
        self.assertEqual(validate_label({'label':'uncertain','reason':'occluded'})['label'],'uncertain')
    def test_failure_not_uncertain_credit(self):
        s=score_labels([{'reference_label':'uncertain','audit':{'error':'network'}}])
        self.assertEqual(s['technical_failures'],1)
        self.assertEqual(s['by_label']['uncertain']['tp'],0)
        self.assertEqual(s['by_label']['uncertain']['reference'],1)
