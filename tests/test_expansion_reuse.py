import json
import tempfile
import unittest
from pathlib import Path
from analysis_skeleton.common import write_jsonl
from analysis_skeleton.expansion20.run_end_to_end import visual_key,FrozenDecompose,replay


class ReuseTests(unittest.TestCase):
    def test_visual_reuse_requires_same_image_and_subject(self):
        base={'image_sha256':'abc','statement':'A car.','entity_context':{'name':'car'}}
        self.assertEqual(visual_key(base),visual_key({**base,'upstream_status':'removed','claim_id':'another'}))
        self.assertNotEqual(visual_key(base),visual_key({**base,'image_sha256':'def'}))
        self.assertNotEqual(visual_key(base),visual_key({**base,'entity_context':{'name':'other car'}}))
    def test_replay_uses_prediction_not_reference_and_counts_no_new_call(self):
        record={'reference_label':'supported','audit':{'input':{'text':'text'},'raw_content':'{"label":"uncertain"}',
                'usage':{'total_tokens':99},'elapsed_seconds':3,'api_calls':1}}
        result,audit=replay(record,'file')
        self.assertEqual(result['label'],'uncertain');self.assertEqual(audit['api_calls'],0)
        self.assertNotIn('usage',audit);self.assertEqual(record['audit']['api_calls'],1)
    def test_missing_text_or_changed_identity_does_not_call_api(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'r.jsonl'
            write_jsonl(path,[{'audit':{'input':{'text':'x'},'identity':{'model':'a'},'raw_content':'{}'}}])
            cache=FrozenDecompose(path,{'model':'a'})
            with self.assertRaises(ValueError):cache.run({'text':'y'})
            with self.assertRaises(ValueError):FrozenDecompose(path,{'model':'b'})
