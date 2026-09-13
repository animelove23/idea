import copy,tempfile,unittest
from pathlib import Path
from analysis_skeleton.common import read_jsonl,write_jsonl
from analysis_skeleton.m5_verify import VisualStage
from analysis_skeleton.visual_shot_context_v1.stage import with_context,ContextShotStage

class ContextTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'shots.jsonl';self.original=read_jsonl('analysis_skeleton/shots/verify.jsonl')
        self.updated=with_context(self.original);write_jsonl(self.path,self.updated)
    def test_only_input_context_changes_with_exact_offsets(self):
        for a,b in zip(self.original,self.updated):
            self.assertEqual(a['output'],b['output']);self.assertEqual(a['image_id'],b['image_id'])
            self.assertEqual({k:v for k,v in a['input'].items() if k!='entity_context'},{k:v for k,v in b['input'].items() if k!='entity_context'})
            ctx=b['input']['entity_context'];m=ctx['target_mention']
            self.assertEqual(ctx['source_window'][m['start']:m['end']],m['quote'])
    def test_query_and_labels_unchanged_in_actual_messages(self):
        baseline=VisualStage();candidate=ContextShotStage(self.path)
        q={'image_path':self.original[0]['input']['image_path'],'image_sha256':self.original[0]['input']['image_sha256'],'statement':'There is a horse.','entity_context':{}}
        a=baseline.messages(q);b=candidate.messages(q)
        self.assertEqual(a[0],b[0]);self.assertEqual(a[-1],b[-1])
        self.assertEqual([r for r in a if r['role']=='assistant'],[r for r in b if r['role']=='assistant'])
        self.assertEqual(baseline.identity['prompt_sha'],candidate.identity['prompt_sha'])
    def test_any_answer_or_image_change_is_rejected(self):
        altered=copy.deepcopy(self.updated);altered[0]['output']['label']='uncertain';write_jsonl(self.path,altered)
        with self.assertRaisesRegex(ValueError,'only_context'):ContextShotStage(self.path)

if __name__=='__main__':unittest.main()
