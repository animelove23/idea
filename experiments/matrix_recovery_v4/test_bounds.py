import unittest,itertools
from .bounds import tighten,constrain


class BoundTests(unittest.TestCase):
    def test_pigeonhole_constraints_exhaustive_small_counts(self):
        # Every feasible assignment of unknown memberships and every retained
        # one-to-one subset must obey the guaranteed gain/loss directions.
        for a,b,u,v in itertools.product(range(5),repeat=4):
            required_gain=b>a+u;required_loss=a>b+v
            for left in range(a,a+u+1):
                for right in range(b,b+v+1):
                    for kept in range(min(left,right)+1):
                        state='mixed' if left>kept and right>kept else 'lost' if left>kept else 'gained' if right>kept else 'unchanged'
                        self.assertIn(state,constrain(['unchanged','gained','lost','mixed'],required_gain,required_loss))

    def example(self,missing=()):
        ob={'component_states':{k:['unchanged','gained','lost','mixed'] for k in ['entity_S','entity_H','attribute_S','attribute_H']},
            'candidate_states':{'S':['gained','mixed'],'H':['unchanged']},'missing_component_types':list(missing),
            'supported_change':'unresolved','hallucination_change':'unchanged','matrix_classifiable':False}
        rows=[{'side':s,'type':'entity','visual_label':'supported'} for s,n in [('original',5),('steer',3)] for _ in range(n)]
        return ob,rows

    def test_known_gain_and_necessary_loss_proves_mixed(self):
        ob,rows=self.example();out=tighten(ob,rows)
        self.assertEqual(out['supported_change'],'mixed');self.assertTrue(out['matrix_classifiable'])
        self.assertFalse(ob['matrix_classifiable'])

    def test_missing_extraction_disables_cardinality_proof(self):
        ob,rows=self.example(['entity']);self.assertFalse(tighten(ob,rows)['matrix_classifiable'])

    def test_unknown_visual_membership_expands_upper_bound(self):
        ob,rows=self.example();rows += [{'side':'steer','type':'entity','visual_label':'uncertain'}]*2
        self.assertFalse(tighten(ob,rows)['matrix_classifiable'])

    def test_alignment_extraction_gap_blocks_count_proof(self):
        ob,rows=self.example();rows[0]['reason']='extraction_gap'
        self.assertFalse(tighten(ob,rows)['matrix_classifiable'])

    def test_group_granularity_blocks_count_proof(self):
        ob,rows=self.example();rows[0]['reason']='many_to_one_collection'
        self.assertFalse(tighten(ob,rows)['matrix_classifiable'])

if __name__=='__main__':unittest.main()
