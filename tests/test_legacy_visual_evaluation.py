import copy,tempfile,unittest
from pathlib import Path
from contextlib import redirect_stdout
import io
from analysis_skeleton.common import read_jsonl,read_json
from analysis_skeleton.decompose_iteration_v1.legacy_visual import scope_slot,prepare

class LegacyEvaluationTests(unittest.TestCase):
    def test_scope_does_not_depend_on_label(self):
        rows=read_jsonl('outputs/legacy_object_attribute_reuse/all_object_attribute_labels.jsonl')
        for r in rows:
            a=scope_slot(r);s=copy.deepcopy(r);s['reference_label']='different';self.assertEqual(a,scope_slot(s))
        self.assertIsNone(scope_slot(next(r for r in rows if r['case_id']=='35966:original:f15')))
    def test_all_retained_rows_have_unchanged_claims_and_no_gold_in_query(self):
        with tempfile.TemporaryDirectory() as d,redirect_stdout(io.StringIO()):
            prepare(d);refs=read_jsonl(Path(d)/'references.jsonl');tasks=read_jsonl(Path(d)/'tasks.jsonl');excluded=read_jsonl(Path(d)/'excluded.jsonl')
            self.assertEqual(len(refs)+len(excluded),635);self.assertEqual(len(refs),len(tasks))
            mapping={r['case_id']:r for r in read_jsonl('outputs/legacy_object_attribute_reuse/all_object_attribute_labels.jsonl')}
            for r in refs:
                self.assertEqual(r['reference_label'],mapping[r['case_id']]['reference_label']);self.assertEqual(r['input'],mapping[r['case_id']]['input'])
            for t in tasks:self.assertNotIn('reference_label',t['input']);self.assertNotIn('reference',t['input']);self.assertNotEqual(t['image_id'],'275717')

if __name__=='__main__':unittest.main()
