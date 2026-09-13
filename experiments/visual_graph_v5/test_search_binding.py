import unittest
from .stage import shots
from .search_binding import validate

class SearchTests(unittest.TestCase):
    def test_search_area_does_not_imply_target_exists(self):
        s=shots()[0];ev=s['output']['claims'][0]['evidence'];ev.update(candidate_status='not_found',bbox=None)
        out=validate(s['output'],s['input'])
        self.assertEqual(out['claims']['q1']['value']['label'],'hallucinated')
        self.assertIsNone(out['claims']['q1']['value']['region_id'])
        self.assertEqual(len(out['search_binding_audit']),1)
    def test_limit_still_blocks_negative(self):
        s=shots()[0];ev=s['output']['claims'][0]['evidence'];ev.update(candidate_status='not_found',bbox=None,limitation='blur',region_status='limited')
        self.assertEqual(validate(s['output'],s['input'])['claims']['q1']['value']['label'],'uncertain')
    def test_unknown_search_region_not_recovered(self):
        s=shots()[0];s['output']['claims'][0].update(region_id='nonexistent');s['output']['claims'][0]['evidence'].update(candidate_status='not_found',bbox=None)
        self.assertEqual(validate(s['output'],s['input'])['claims']['q1']['status'],'technical_failure')

if __name__=='__main__':unittest.main()
