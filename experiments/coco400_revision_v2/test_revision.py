import copy,unittest,tempfile,json
from pathlib import Path
from .alignment import validate
from .fixtures import cases,doc
from .visual import merge,ReviewStage
from .observation import analyze_pair
from experiments.coco400_v1.test_observe import fixture,ObservationTests


class RevisionTests(unittest.TestCase):
    def test_excluded_issue_does_not_block_pair(self):
        b,l=fixture();b['original']['issues']=[{'kind':'excluded_invalid'}]
        r,_=analyze_pair(b,l);self.assertTrue(r['matrix_classifiable'])
    def test_out_of_scope_state_is_not_missing_in_scope_fact(self):
        b,l=fixture();b['original']['issues']=[{'kind':'attribute_invalid','reason':'state outside frozen six-value vocabulary'}]
        r,_=analyze_pair(b,l);self.assertTrue(r['matrix_classifiable'])
    def test_unknown_attribute_issue_keeps_entity_component(self):
        b,l=fixture();b['alignment']['entities']=[]
        b['original']['issues']=[{'kind':'attribute_invalid','raw':{'entity_id':'e1','slot':'color'}}]
        r,_=analyze_pair(b,l);self.assertEqual(r['component_states']['entity_S'],['unchanged'])
        self.assertFalse(r['matrix_classifiable'])
    def test_unknown_entity_issue_still_blocks(self):
        b,l=fixture();b['original']['issues']=[{'kind':'entity_invalid'}]
        r,_=analyze_pair(b,l);self.assertFalse(r['matrix_classifiable'])
    def test_all_demonstrations_and_probes_validate(self):
        for c in cases()+cases(True):
            r=validate(c['output'],**c['input']);self.assertFalse(r['issues'],c['example_id'])
    def test_generalization_not_equal(self):
        c=cases()[1];r=validate(c['output'],**c['input'])
        self.assertEqual(r['alignments'][0]['status'],'modified')
        self.assertEqual(r['description_transitions'][0]['change'],'generalized')
    def test_generalization_cannot_silently_retain(self):
        c=copy.deepcopy(cases()[1]);c['output']['alignments'][0]['status']='retained'
        with self.assertRaises(ValueError):validate(c['output'],**c['input'])
    def test_part_whole_cannot_match(self):
        c=copy.deepcopy(cases()[3]);c['output']['entities'][0]['status']='matched'
        with self.assertRaises(ValueError):validate(c['output'],**c['input'])
    def test_conflict_not_optimistic_selection(self):
        r=merge({'label':'supported'},{'status':'complete','value':{'label':'hallucinated'}})
        self.assertEqual(r['label'],'uncertain')
    def test_failed_review_keeps_original(self):
        self.assertEqual(merge({'label':'uncertain'},{'status':'technical_failure'}),{'label':'uncertain'})
    def test_unresolved_review_not_forced(self):
        self.assertEqual(merge({'label':'uncertain'},{'status':'complete','value':{'label':'uncertain'}})['label'],'uncertain')
    def test_review_query_does_not_leak_prior_verdict(self):
        with tempfile.TemporaryDirectory() as tmp:
            config=Path(tmp)/'offline.json'
            config.write_text(json.dumps({'api_key':'offline-test-placeholder','model':'deepseek-flash'}),encoding='utf-8')
            stage=ReviewStage('outputs/final_v1_release/visual_routes.json',config_path=config,transport=lambda body:None)
        source=stage.stages['entity'].source;p=copy.deepcopy(source.shots[0]['input'])
        p.update(claim_type='entity',first_label='hallucinated',first_reason='SECRET_PRIOR')
        messages=source.messages(p)
        self.assertNotIn('SECRET_PRIOR',str(messages));self.assertNotIn('first_label',str(messages))
        self.assertEqual(len(messages),14) # system + 6 user/assistant + query


if __name__=='__main__':unittest.main()
