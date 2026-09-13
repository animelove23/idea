import copy,socket,unittest
from unittest.mock import patch
from pathlib import Path
from analysis_skeleton.common import read_jsonl,sha
from tests.test_final_pipeline import FinalPipelineTests,Stub
from .end_to_end import run_full


class NewEntryTests(unittest.TestCase):
    def test_fresh_pipeline_and_offline_resume(self):
        FinalPipelineTests.setUpClass();f=FinalPipelineTests();f.setUp();self.addCleanup(f.doCleanups)
        aligned=copy.deepcopy(f.f.aligned)
        for e in aligned['entities']:e['description_change']='equivalent' if e['status']=='matched' else 'absent' if e['status'] in ('original_only','steer_only') else 'unresolved'
        stages={'decompose':Stub('decompose',[f.f.original,f.f.steer]),'align':Stub('align',[aligned]),
            'verify':Stub('verify',unresolved=True,proposition=True)}
        # Review schema is fixed by type: entity=context, attribute=whole proposition.
        class TypedStub(Stub):
            def run(self,payload):
                self.proposition=payload['claim_type']=='attribute'
                return super().run(payload)
        review=TypedStub('verify')
        out=f.root/'revision'
        with patch.object(socket.socket,'connect',side_effect=AssertionError('network_forbidden')):
            first=run_full(f.source,out,profile=f.profile,stages=stages,review_stage=review,parser=f.parser,workers=1)
            self.assertEqual(first['analyzed_pairs'],1);self.assertGreater(first['review_tasks'],0)
            files=['pairs.jsonl','denominator_ledger.jsonl','observation_pairs.jsonl'];before={p:sha(out/p) for p in files}
            count=len(review.inputs)
            again=run_full(f.source,out,profile=f.profile,stages=stages,review_stage=review,parser=f.parser,workers=1,resume=True)
            self.assertEqual(len(review.inputs),count);self.assertEqual(again['review_new_calls'],0)
            self.assertEqual(before,{p:sha(out/p) for p in files})
            self.assertEqual(first['facts'],3)


if __name__=='__main__':unittest.main()
