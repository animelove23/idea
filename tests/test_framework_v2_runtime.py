import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from analysis_skeleton.common import read_json,write_json
from analysis_skeleton.framework_v2.runtime import SafeStage,ResponseCache,CacheConflict,Checkpoints,CheckpointIntegrityError
from analysis_skeleton.llm import CallFailure


class FakeStage:
    stage='decompose';identity={'model':'fake'}
    def __init__(self):self.calls=0
    def run(self,payload):
        self.calls+=1
        return {'ok':True},{'api_calls':1,'identity':self.identity,'input':payload,'raw_content':'{"ok":true}',
                            'response_id':f'id{self.calls}','response_model':'fake'}


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.stage=FakeStage();self.payload={'text':'A car.'}
        self.cp=Checkpoints(self.tmp.name,{'replicate_id':'r1'})
    def test_completed_resume_never_reissues_call(self):
        a=self.cp.call('a',self.stage,self.payload,lambda r:r)
        b=self.cp.call('a',self.stage,self.payload,lambda r:r)
        self.assertEqual(a,b);self.assertEqual(self.stage.calls,1)
    def test_response_saved_before_validation_interruption_is_recovered(self):
        def interrupt(raw):raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):self.cp.call('a',self.stage,self.payload,interrupt)
        r=self.cp.call('a',self.stage,self.payload,lambda raw:raw)
        self.assertEqual(r['status'],'complete');self.assertEqual(self.stage.calls,1)
    def test_started_without_response_is_unknown_and_never_retried(self):
        class Interrupt(FakeStage):
            def run(self,payload):raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):self.cp.call('a',Interrupt(),self.payload,lambda x:x)
        r=self.cp.call('a',self.stage,self.payload,lambda x:x)
        self.assertEqual(r['status'],'outcome_unknown');self.assertEqual(self.stage.calls,0)
    def test_identity_change_and_corruption_rejected(self):
        self.cp.call('a',self.stage,self.payload,lambda x:x)
        with self.assertRaises(CheckpointIntegrityError):self.cp.call('a',self.stage,{'text':'Different'},lambda x:x)
        r=read_json(self.cp.file('a'));r['value']['value']={'forged':True};write_json(self.cp.file('a'),r)
        with self.assertRaises(CheckpointIntegrityError):self.cp.call('a',self.stage,self.payload,lambda x:x)
    def test_duplicate_cache_selection_rejected(self):
        _,a=self.stage.run(self.payload);r={'task_key':'a','audit':a}
        with self.assertRaises(CacheConflict):ResponseCache([r,r])
    def test_replay_uses_raw_prediction_not_reference_and_fresh_bypasses(self):
        _,audit=self.stage.run(self.payload)
        cache=ResponseCache([{'task_key':'a','audit':audit,'reference_label':'wrong'}])
        replay=Checkpoints(Path(self.tmp.name)/'replay',{},cache,'replay')
        r=replay.call('a',self.stage,self.payload,lambda x:x)
        self.assertEqual(r['value'],{'ok':True});self.assertEqual(r['audit']['api_calls'],0)
        fresh=Checkpoints(Path(self.tmp.name)/'fresh',{},cache,'fresh')
        fresh.call('a',self.stage,self.payload,lambda x:x)
        self.assertEqual(self.stage.calls,2)
    def test_changed_payload_cache_miss_does_not_call_transport(self):
        _,audit=self.stage.run(self.payload)
        cp=Checkpoints(Path(self.tmp.name)/'replay',{},ResponseCache([{'task_key':'a','audit':audit}]),'replay')
        r=cp.call('a',self.stage,{'text':'Changed'},lambda x:x)
        self.assertEqual(r['status'],'technical_failure');self.assertEqual(self.stage.calls,1)
    def test_returned_model_mismatch_cannot_reuse_response(self):
        _,audit=self.stage.run(self.payload);audit['response_model']='different_model'
        cache=ResponseCache([{'task_key':'a','audit':audit}])
        self.assertIsNone(cache.get('a',self.stage,self.payload))
    def test_unexpected_validator_bug_is_diagnostic_failure(self):
        def fail(raw):raise RuntimeError('secret text must not be logged')
        r=self.cp.call('a',self.stage,self.payload,fail)
        self.assertEqual(r['status'],'unexpected_failure')
        self.assertTrue(r['diagnostic']['frames']);self.assertNotIn('secret',json.dumps(r))
        self.assertEqual(self.cp.call('b',self.stage,self.payload,lambda x:x)['status'],'complete')


class TransportTests(unittest.TestCase):
    def source(self,transport,messages=lambda payload:[]):
        return SimpleNamespace(stage='verify',identity={'model':'fake'},
                               config=SimpleNamespace(model='fake',max_tokens=10),messages=messages,transport=transport)
    def test_missing_or_corrupt_image_is_input_failure_before_transport(self):
        for exc in (FileNotFoundError(),OSError('bad image')):
            called=[]
            def messages(p):raise exc
            stage=SafeStage(self.source(lambda body:called.append(body),messages))
            with self.assertRaises(CallFailure) as c:stage.run({})
            self.assertEqual(c.exception.audit['api_calls'],0);self.assertFalse(called)
    def test_timeout_invalid_json_truncation_are_failures(self):
        def timeout(body):raise TimeoutError('credential must not be serialized')
        transports=[timeout,lambda b:{'choices':[{'finish_reason':'stop','message':{'content':'{bad'}}]},
                    lambda b:{'choices':[{'finish_reason':'length','message':{'content':'{}'}}]}]
        for transport in transports:
            with self.assertRaises(CallFailure) as c:SafeStage(self.source(transport)).run({})
            self.assertEqual(c.exception.audit['api_calls'],1)
            self.assertNotIn('credential',json.dumps(c.exception.audit))
    def test_frozen_request_parameters_and_raw_response_retained(self):
        seen=[]
        def request(body):
            seen.append(body)
            return {'model':'returned-version','id':'response1','usage':{'total_tokens':12},
                    'choices':[{'finish_reason':'stop','message':{'content':'{"label":"supported","reason":"visible"}'}}]}
        raw,a=SafeStage(self.source(request)).run({'statement':'x'})
        self.assertEqual(seen[0]['temperature'],0);self.assertEqual(seen[0]['thinking'],{'type':'disabled'})
        self.assertEqual(a['response_model'],'returned-version');self.assertEqual(raw['label'],'supported')


if __name__=='__main__':unittest.main()
