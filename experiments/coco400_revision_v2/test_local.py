import copy,unittest
from .fixtures import cases
from .local_alignment import validate_local


class LocalTests(unittest.TestCase):
    def test_conflicting_entity_description_only_isolates_its_fact(self):
        c=copy.deepcopy(cases()[4]);e=c['output']['entities'][0];e['description_change']='generalized'
        r=validate_local(c['output'],**c['input'])
        self.assertEqual(r['alignments'][0]['status'],'unresolved')
        self.assertEqual(r['alignments'][1]['status'],'removed')
        self.assertEqual(len(r['local_quarantine']),1)
    def test_part_whole_bad_match_stays_unresolved(self):
        c=copy.deepcopy(cases()[3]);c['output']['entities'][0]['status']='matched'
        r=validate_local(c['output'],**c['input']);self.assertEqual(r['entities'][0]['status'],'unresolved')
    def test_valid_examples_unchanged(self):
        for c in cases():self.assertFalse(validate_local(c['output'],**c['input'])['local_quarantine'])


if __name__=='__main__':unittest.main()
