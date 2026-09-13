import unittest
from evaluation.reference_metrics import compute


def row(o,s,status='retained',reason='same_fact',survival='present'):
    return dict(original_fact_ids=o,steer_fact_ids=s,status=status,reason=reason,survival_in_opposite_caption=survival)


def score(g,p):return compute([dict(pair_id='x',fact_alignment=g)],[dict(pair_id='x',fact_alignment=p)])[0]


class ReferenceMetricsTests(unittest.TestCase):
    def test_perfect(self):
        r=[row(['f1'],['f2'])];m=score(r,r)
        self.assertEqual(m['alignment_edge']['f1'],1);self.assertEqual(m['status_macro_f1'],1)
    def test_wrong_pair_same_status(self):
        g=[row(['a'],['x']),row(['b'],['y'])];p=[row(['a'],['y']),row(['b'],['x'])];m=score(g,p)
        self.assertEqual(m['alignment_edge']['f1'],0);self.assertEqual(m['status_macro_f1'],1)
    def test_technical_ambiguous_no_credit(self):
        g=[row(['a'],[],'ambiguous','extraction_gap')];p=[row(['a'],[],'ambiguous','stage_failed')];m=score(g,p)
        self.assertEqual(m['joint_edge_status']['tp'],0);self.assertEqual(m['status_per_class']['ambiguous']['f1'],0)
    def test_group_not_cartesian_product(self):
        r=[row(['a','b'],['x','y'])];m=score(r,r)
        self.assertEqual(m['alignment_edge']['tp'],1);self.assertEqual(m['facts'],4)
    def test_false_removal_and_uncertainty(self):
        g=[row(['a'],[],'ambiguous','extraction_gap'),row(['b'],[],'ambiguous','entity_uncertain','uncertain')]
        p=[row(['a'],[],'removed','not_expressed'),row(['b'],[],'removed','not_expressed')];m=score(g,p)
        self.assertEqual(m['false_removal']['rate'],.5);self.assertEqual(m['false_removal']['upper_bound'],1)
    def test_no_predicted_removed(self):
        r=[row(['a'],['b'])];self.assertIsNone(score(r,r)['false_removal']['rate'])


if __name__=='__main__':unittest.main()
