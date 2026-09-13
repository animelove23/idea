import unittest,copy
from .stage import shots
from .bounded_stage import compile_bounded,BoundedStage

class BudgetTests(unittest.TestCase):
    def test_excess_inventory_rejected(self):
        s=shots()[0];s['output']['regions'].append(copy.deepcopy(s['output']['regions'][0]))
        with self.assertRaises(ValueError):compile_bounded(s['output'],s['input'])
    def test_budget_does_not_change_evidence_label(self):
        s=shots()[0];self.assertEqual(compile_bounded(s['output'],s['input'])['claims']['q1']['value']['label'],'supported')
    def test_query_includes_finite_budget(self):
        stage=BoundedStage(transport=lambda _:None);s=shots()[0]
        self.assertIn('"region_budget": 1',stage.user(s['input'])['content'][0]['text'])

if __name__=='__main__':unittest.main()
