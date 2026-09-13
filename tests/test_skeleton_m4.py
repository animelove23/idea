import copy
import unittest
from analysis_skeleton.common import read_jsonl
from analysis_skeleton.m4_queue import build_queue
from analysis_skeleton.m3_align import validate_alignment


class QueueTests(unittest.TestCase):
    def setUp(self):self.cases=read_jsonl('analysis_skeleton/fixtures/align_cases.jsonl')
    def queue(self,c):
        return build_queue(c['case_id'],c['original'],c['steer'],validate_alignment(c['reference'],c['original'],c['steer']),'missing.jpg')
    def test_retained_once_modified_twice(self):
        q=self.queue(self.cases[0])
        self.assertEqual(len(q),3)
        self.assertEqual(sorted(len(c['refs']) for c in q),[1,1,2])
        self.assertEqual(sum(len(c['refs']) for c in q),4)
    def test_no_lexical_record_does_not_erase_claim(self):
        q=self.queue(self.cases[3])
        self.assertEqual(len(q),2)
        self.assertTrue(all(link['status']=='unavailable' for c in q for link in c['token_links']))
    def test_different_images_not_shared(self):
        c=self.cases[0];a=self.queue(c)
        c=copy.deepcopy(c);c['case_id']='different_image';b=self.queue(c)
        self.assertFalse({r['claim_id'] for r in a}&{r['claim_id'] for r in b})
    def test_duplicate_alignment_rejected(self):
        c=copy.deepcopy(self.cases[0]);c['reference']['alignments'].append(c['reference']['alignments'][0])
        with self.assertRaises(ValueError):
            build_queue('x',c['original'],c['steer'],c['reference'],'x.jpg')
