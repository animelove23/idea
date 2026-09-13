import unittest
from analysis_skeleton.common import read_jsonl
from .json_entry import AlignStage


class FormatTests(unittest.TestCase):
    def test_json_mode_prompt_and_blind_query(self):
        stage=AlignStage(transport=lambda _: self.fail('offline test cannot call network'))
        ex=read_jsonl('experiments/entity_attribute_v3/m3_probes.jsonl')[0]
        messages=stage.messages(ex['input'])
        self.assertEqual(len(messages),18)
        self.assertIn('json',messages[0]['content'].lower())
        self.assertIn('required_ids',messages[-1]['content'])
        self.assertNotIn('reference',messages[-1]['content'])
        self.assertEqual(len(stage.shots),8)

if __name__=='__main__':unittest.main()
