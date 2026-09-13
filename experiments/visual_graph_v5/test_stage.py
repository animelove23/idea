import copy,unittest
from .stage import shots,compiled,JointStage

class GraphTests(unittest.TestCase):
    def test_six_examples_include_joint_owner_attribute(self):
        ss=shots();self.assertEqual(len(ss),6);self.assertEqual(sum(len(s['input']['claims'])==2 for s in ss),3)
        for s in ss:
            out=compiled(s['output'],s['input'])
            self.assertTrue(all(v['status']=='complete' for v in out['claims'].values()))
        self.assertEqual(compiled(ss[-1]['output'],ss[-1]['input'])['claims']['p1']['value']['label'],'supported')
        self.assertEqual(compiled(ss[-1]['output'],ss[-1]['input'])['claims']['q1']['value']['label'],'uncertain')

    def test_duplicate_only_quarantines_affected_claim(self):
        s=shots()[3];s['output']['claims'].append(copy.deepcopy(s['output']['claims'][1]))
        out=compiled(s['output'],s['input'])['claims']
        self.assertEqual(out['p1']['status'],'complete');self.assertEqual(out['q1']['status'],'technical_failure')

    def test_region_box_mismatch_rejected(self):
        s=shots()[0];s['output']['claims'][0]['evidence']['bbox']=[1,2,3,4]
        self.assertEqual(compiled(s['output'],s['input'])['claims']['q1']['status'],'technical_failure')

    def test_uncertain_parent_blocks_supported_attribute(self):
        s=shots()[3];ev=s['output']['claims'][0]['evidence']
        ev.update(candidate_status='unresolved',limitation='ambiguous_identity')
        out=compiled(s['output'],s['input'])['claims']
        self.assertEqual(out['q1']['value']['label'],'uncertain')

    def test_missing_parent_row_cannot_support_property(self):
        s=shots()[3];s['output']['claims']=s['output']['claims'][1:]
        self.assertEqual(compiled(s['output'],s['input'])['claims']['q1']['value']['label'],'uncertain')

    def test_unrelated_region_cannot_support_property(self):
        s=shots()[3];s['output']['regions'].append({**s['output']['regions'][0],'id':'r2'})
        s['output']['claims'][1]['region_id']='r2'
        self.assertEqual(compiled(s['output'],s['input'])['claims']['q1']['value']['label'],'uncertain')

    def test_query_contains_no_previous_verdict(self):
        s=JointStage(transport=lambda _:self.fail('no network in local test'))
        ex=shots()[0];msg=s.messages(ex['input'])
        self.assertEqual(len(msg),14);self.assertIn('JSON',msg[0]['content'])
        self.assertNotIn('reference_label',msg[-1]['content'][0]['text'])

if __name__=='__main__':unittest.main()
