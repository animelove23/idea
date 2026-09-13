import copy,unittest
from analysis_skeleton.decompose_iteration_v1.value_anchor import normalize_with_value_anchors
from analysis_skeleton.framework_v2.contracts import normalize_document

class ValueAnchorTests(unittest.TestCase):
    def raw(self,evidence='The cup is red',value='red',occurrence=0):
        return {'entities':[{'id':'e1','name':'cup','mentions':[{'quote':'cup','occurrence':0}]}],
                'attributes':[{'id':'a1','entity_id':'e1','slot':'color','value':value,'evidence':[{'quote':evidence,'occurrence':0}],'value_quotes':[{'quote':value,'occurrence':occurrence}]}],'excluded':[]}
    def test_repeated_value_uniquely_bound_to_evidence(self):
        text='A red car. The cup is red.';raw=self.raw();before=copy.deepcopy(raw)
        self.assertTrue(normalize_document(raw,text)['issues'])
        result=normalize_with_value_anchors(raw,text)
        self.assertFalse(result['issues']);self.assertEqual(result['facts'][1]['value_spans'][0]['occurrence'],1);self.assertEqual(raw,before)
    def test_valid_occurrence_never_changes(self):
        r=normalize_with_value_anchors(self.raw(occurrence=1),'A red car. The cup is red.')
        self.assertFalse(r['value_anchor_audit']['repairs'])
    def test_two_candidates_in_evidence_stay_invalid(self):
        r=normalize_with_value_anchors(self.raw('The cup is red with red dots'),'A red car. The cup is red with red dots.')
        self.assertTrue(r['issues']);self.assertFalse(r['value_anchor_audit']['repairs']);self.assertEqual(r['value_anchor_audit']['ambiguous_not_repaired'][0]['candidate_count'],2)
    def test_no_substitution_no_invalid_evidence_repair(self):
        for raw in [self.raw(value='blue'),self.raw('invented evidence')]:
            r=normalize_with_value_anchors(raw,'A red car. The cup is red.');self.assertTrue(r['issues']);self.assertFalse(r['value_anchor_audit']['repairs'])
    def test_repair_does_not_bypass_invalid_owner_or_slot(self):
        raw=self.raw();raw['attributes'][0]['entity_id']='missing'
        r=normalize_with_value_anchors(raw,'A red car. The cup is red.');self.assertTrue(r['issues']);self.assertEqual(len(r['facts']),1)

if __name__=='__main__':unittest.main()
