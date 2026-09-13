import copy
import json
import tempfile
import unittest
from pathlib import Path
from analysis_skeleton.common import read_json,read_jsonl,write_jsonl,sha
from analysis_skeleton.llm import CallFailure
from analysis_skeleton.m1_lexical import LexicalRecorder
from analysis_skeleton.framework_v2.pipeline import execute
from analysis_skeleton.framework_v2.runtime import CheckpointIntegrityError
import tests.test_skeleton_pipeline as baseline_fixtures


class Stub:
    identity={'model':'offline_fault_fixture'}
    def __init__(self,stage,responses):self.stage=stage;self.responses=iter(responses);self.inputs=[]
    def run(self,payload):
        self.inputs.append(copy.deepcopy(payload));r=next(self.responses)
        if isinstance(r,BaseException):raise r
        return copy.deepcopy(r),{'api_calls':0,'stage':self.stage,'identity':self.identity,'input':payload,'raw_content':json.dumps(r)}


class GenericPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.parser=LexicalRecorder()
    def setUp(self):
        f=baseline_fixtures.PipelineTests();f.setUp();self.f=f
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.source=self.root/'pairs.jsonl';self.out=self.root/'run'
    def stages(self,n=1,verify=None,decompose=None):
        return {'decompose':Stub('decompose',decompose if decompose is not None else [self.f.original,self.f.steer]*n),
                'align':Stub('align',[self.f.aligned]*n),
                'verify':Stub('verify',verify if verify is not None else [{'label':'supported','reason':'fixture'}]*(2*n))}
    def roster(self,n=1,image=True):
        pairs=[]
        for i in range(n):
            p=copy.deepcopy(self.f.pair);p['pair_id']=f'p{i}'
            for s in ('original','steer'):p[s]['caption_id']=f'p{i}_{s}'
            if image:
                inp=read_jsonl('analysis_skeleton/fixtures/verify_cases.jsonl')[0]['input']
                p.update(image_path=inp['image_path'],image_sha256=inp['image_sha256'])
            pairs.append(p)
        write_jsonl(self.source,pairs);return pairs
    def run_pipeline(self,stages,**kw):return execute(self.source,self.out,stages=stages,parser=self.parser,**kw)
    def test_new_captions_full_path_resume_and_both_locator_contexts(self):
        self.roster();stages=self.stages();m=self.run_pipeline(stages)
        self.assertEqual((m['analyzed_pairs'],m['facts'],m['claims']),(1,3,2))
        q=read_jsonl(self.out/'verification_queue.jsonl')
        self.assertEqual(len(q[0]['locator_audit']['by_ref']),2)
        before={s:len(v.inputs) for s,v in stages.items()}
        resumed=self.run_pipeline(stages,resume=True)
        self.assertEqual(before,{s:len(v.inputs) for s,v in stages.items()})
        self.assertEqual(resumed['resumed_checkpoints'],5)
    def test_one_invalid_visual_label_preserves_other_claims_and_pair(self):
        self.roster(2);stages=self.stages(2,verify=[{'label':'nonsense','reason':'x'}]+[{'label':'supported','reason':'visible'}]*3)
        m=self.run_pipeline(stages)
        self.assertEqual(m['analyzed_pairs'],2);self.assertEqual(m['pending_claims'],1)
        self.assertEqual(m['call_status_counts']['technical_failure'],1)
    def test_failed_decomposition_blocks_alignment_without_false_removals(self):
        self.roster();stages=self.stages(decompose=[CallFailure({'error':'timeout','api_calls':0}),self.f.steer])
        m=self.run_pipeline(stages)
        self.assertEqual(len(stages['align'].inputs),0);self.assertEqual(m['facts'],1)
        rows=read_jsonl(self.out/'denominator_ledger.jsonl')
        self.assertEqual(rows[0]['alignment_axis'],'technical_unresolved')
        self.assertEqual(rows[0]['status'],'unresolved')
    def test_missing_and_corrupt_image_leave_facts_pending(self):
        pairs=self.roster(2,image=False)
        corrupt=self.root/'bad.jpg';corrupt.write_bytes(b'not an image')
        pairs[1].update(image_path=str(corrupt),image_sha256=sha(corrupt));write_jsonl(self.source,pairs)
        stages=self.stages(2);m=self.run_pipeline(stages)
        self.assertEqual(m['facts'],6);self.assertEqual(m['pending_claims'],4)
        self.assertEqual(len(stages['verify'].inputs),0)
        self.assertTrue(all(r['visual_axis']=='pending' for r in read_jsonl(self.out/'denominator_ledger.jsonl')))
    def test_missing_caption_visible_in_roster(self):
        p=self.roster();p[0]['steer']=None;write_jsonl(self.source,p)
        stages=self.stages();m=self.run_pipeline(stages)
        self.assertEqual(m['analyzed_pairs'],0)
        self.assertEqual(read_jsonl(self.out/'pair_status.jsonl')[0]['status'],'missing_caption')
    def test_resume_rejects_changed_replicate(self):
        self.roster();stages=self.stages();self.run_pipeline(stages)
        with self.assertRaises(CheckpointIntegrityError):self.run_pipeline(stages,resume=True,replicate_id='r2')
    def test_duplicate_caption_id_rejected_before_requests(self):
        pairs=self.roster(2);pairs[1]['original']['caption_id']=pairs[0]['original']['caption_id'];write_jsonl(self.source,pairs)
        stages=self.stages(2)
        with self.assertRaises(ValueError):self.run_pipeline(stages)
        self.assertFalse(stages['decompose'].inputs)
    def test_interrupted_pair_restores_without_redoing_successful_m2(self):
        self.roster();stages=self.stages();stages['align']=Stub('align',[KeyboardInterrupt()])
        with self.assertRaises(KeyboardInterrupt):self.run_pipeline(stages)
        before=len(stages['decompose'].inputs)
        m=self.run_pipeline(stages,resume=True)
        self.assertEqual(len(stages['decompose'].inputs),before)
        self.assertEqual(m['call_status_counts']['outcome_unknown'],1)
        self.assertEqual(len(stages['align'].inputs),1)
        self.assertTrue(all(r['status']=='unresolved' for r in read_jsonl(self.out/'denominator_ledger.jsonl')))


if __name__=='__main__':unittest.main()
