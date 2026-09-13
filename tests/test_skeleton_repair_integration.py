import copy
import json
import unittest
from analysis_skeleton.common import read_jsonl,digest
from analysis_skeleton.m5_verify import VisualStage
from analysis_skeleton.repair_v1.pipeline import ExactCache
from analysis_skeleton.expansion20.run_end_to_end import visual_key


class CacheTests(unittest.TestCase):
    def test_exact_replay_uses_prediction_not_reference(self):
        class Stage:
            identity={'model':'test'}
            def run(self,payload):return {'label':'fresh'},{'api_calls':1}
        stage=Stage();payload={'statement':'a','image_sha256':'img','entity_context':{'name':'shirt'}}
        record={'reference_label':'wrong','audit':{'identity':stage.identity,'input':payload,
                'raw_content':json.dumps({'label':'supported'}),'api_calls':1,'usage':{'total_tokens':20}}}
        cache=ExactCache(stage,[(record,'source.jsonl')],visual_key)
        raw,audit=cache.run(payload)
        self.assertEqual(raw,{'label':'supported'});self.assertEqual(audit['api_calls'],0)
        self.assertNotIn('usage',audit);self.assertEqual(audit['reused_usage']['total_tokens'],20)
        for field,value in [('statement','b'),('image_sha256','other'),('entity_context',{'name':'girl shirt'})]:
            changed=copy.deepcopy(payload);changed[field]=value
            self.assertEqual(cache.run(changed)[1]['api_calls'],1)
        stage.identity={'model':'other'}
        self.assertEqual(ExactCache(stage,[(record,'source')],visual_key).run(payload)[1]['api_calls'],1)

    def test_alignment_payload_change_prevents_reuse(self):
        class Stage:
            identity={'model':'test'}
            def run(self,payload):return {},{'api_calls':1}
        payload={'original':{'entities':['e1']},'steer':{}}
        record={'audit':{'identity':Stage.identity,'input':payload,'raw_content':'{}'}}
        cache=ExactCache(Stage(),[(record,'source')],digest)
        self.assertEqual(cache.run(payload)[1]['api_calls'],0)
        self.assertEqual(cache.run({'original':{'entities':['e1','e2']},'steer':{}})[1]['api_calls'],1)


class FrozenABTests(unittest.TestCase):
    def test_only_context_changes_and_reference_is_not_sent(self):
        cases=read_jsonl('analysis_skeleton/fixtures/repair_v1/visual_ab.jsonl')
        self.assertEqual(len(cases),60)
        self.assertEqual(sum(c['order'][0]=='control' for c in cases),30)
        # No network; inspect the actual final user message including image serialization.
        stage=VisualStage(transport=lambda body:None)
        for c in cases:
            left=c['control_input'];right=c['context_input']
            self.assertEqual({k:v for k,v in left.items() if k!='entity_context'},
                             {k:v for k,v in right.items() if k!='entity_context'})
            ctx=right['entity_context'];m=ctx['target_mention']
            self.assertEqual(ctx['source_window'][m['start']:m['end']],m['quote'])
            user=stage.user(right);text=json.loads(user['content'][0]['text'])
            self.assertEqual(set(text),{'statement','entity_context'})
            self.assertNotIn('reference_label',json.dumps(text))


if __name__=='__main__':unittest.main()
