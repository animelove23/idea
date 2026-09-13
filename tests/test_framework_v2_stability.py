import unittest
from analysis_skeleton.framework_v2.stability import repeat_metrics,visual_metrics


class StabilityTests(unittest.TestCase):
    def rows(self):
        return [{'case_id':'a','image_id':'img','replicate_id':str(i),'condition_id':'baseline','status':'complete',
                 'signature':label,'label':label,'query_hash':'same_query','audit':{'response_id':str(i),'identity':{'model':'test'}}}
                for i,label in enumerate(['supported','supported','uncertain'])]
    def test_pairwise_rate_not_any_change_rate(self):
        m=repeat_metrics(self.rows(),['a'],['0','1','2'])
        self.assertEqual(m['pairwise_disagreement'],2/3);self.assertEqual(m['any_change_case_rate'],1)
        self.assertEqual(m['independent_images'],1)
    def test_failure_does_not_become_a_semantic_label_or_disappear(self):
        rows=self.rows();rows[-1]['status']='technical_failure'
        m=repeat_metrics(rows,['a'],['0','1','2'])
        self.assertIsNone(m['pairwise_disagreement']);self.assertEqual(m['unsuccessful_or_missing_requests'],1)
        self.assertFalse(m['stability_gate_evaluable'])
    def test_cache_and_repeated_response_ids_rejected(self):
        for field in ('cache_hit','response_id'):
            rows=self.rows();rows[-1]['audit'][field]=True if field=='cache_hit' else '0'
            with self.assertRaises(ValueError):repeat_metrics(rows,['a'],['0','1','2'])
    def test_overconfident_uncertain_reference_included_in_risk(self):
        rows=[{'reference_label':'uncertain','prediction':{'label':'supported'}},
              {'reference_label':'supported','prediction':{'label':'supported'}}]
        m=visual_metrics(rows)
        self.assertEqual(m['decided_error_rate'],.5);self.assertEqual(m['gold_decidable_coverage'],1)
    def test_model_or_query_change_cannot_be_counted_as_repeat(self):
        rows=self.rows();rows[-1]['query_hash']='different'
        with self.assertRaises(ValueError):repeat_metrics(rows,['a'],['0','1','2'])


if __name__=='__main__':unittest.main()
