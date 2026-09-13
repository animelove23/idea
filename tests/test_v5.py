import copy
import unittest
from annotation.v5.build_reference import shots,probes
from decomposition.v5.schema import validate_entities,model_entities,validate_facts,model_facts,ProtocolError
from decomposition.v5.pipeline import apply_patches,normalize,DecomposerV5,warnings
from decomposition.v5.metrics import compare,change_score,assignment
from decomposition.config import APIConfig

class V5Tests(unittest.TestCase):
    def test_unique_case_repair_preserves_text_and_offsets(self):
        text='Her hand is visible.'
        a,r=validate_entities({'entities':[{'id':'e1','canonical':'hand','kind':'part','mentions':[{'sentence_id':'s1','quote':'her hand'}]}],'unresolved':[],'excluded':[]},text)
        self.assertEqual(len(r),1);span=a['entities'][0]['mentions'][0]
        self.assertEqual(text[span['start']:span['end']],'Her hand')
    def test_ambiguous_quote_not_first_match(self):
        with self.assertRaises(ProtocolError):
            validate_entities({'entities':[{'id':'e1','canonical':'man','kind':'single','mentions':[{'sentence_id':'s1','quote':'man'}]}],'unresolved':[],'excluded':[]},'A man sees a man.')
    def test_pronoun_is_not_matched_inside_suitcase(self):
        text='The suitcase is blue and it is open.'
        a,r=validate_entities({'entities':[{'id':'e1','canonical':'suitcase','kind':'single','mentions':[{'sentence_id':'s1','quote':'it'}]}],'unresolved':[],'excluded':[]},text)
        self.assertEqual(a['entities'][0]['mentions'][0]['start'],text.index(' it ')+1)
        self.assertFalse(r)
    def test_parent_error_contains_repairable_field_path(self):
        payload={'entities':[{'id':'e1','canonical':'man','kind':'group','mentions':[{'sentence_id':'s1','quote':'men'}],'group_parent':None,'group_link':'subset_of'}],'unresolved':[],'excluded':[]}
        with self.assertRaises(ProtocolError) as caught:validate_entities(payload,'Three men stand.')
        self.assertIn('entities[0].group_parent',str(caught.exception))
        fixed=apply_patches(payload,{'patches':[{'op':'replace','path':'/entities/0/group_link','value':None}]},str(caught.exception))
        validate_entities(fixed,'Three men stand.')
    def test_group_cycle_rejected(self):
        es=[{'id':f'e{i}','canonical':'man','kind':'group','mentions':[{'sentence_id':'s1','quote':'men'}],'group_parent':f'e{3-i}','group_link':'subset_of'} for i in [1,2]]
        with self.assertRaises(ProtocolError):validate_entities({'entities':es,'unresolved':[],'excluded':[]},'Three men stand.')
    def test_local_patch_cannot_change_another_record(self):
        with self.assertRaises(ProtocolError):apply_patches({'facts':[{'predicate':'x'},{'predicate':'y'}]},{'patches':[{'op':'replace','path':'/facts/1/predicate','value':'z'}]},'facts[0].predicate: bad')
    def test_unknown_predicate_preserved_and_queued(self):
        d=shots()[0];fs=model_facts(d['facts']);fs[-1]['predicate']='previously_unknown_relation'
        b,_=validate_facts({'facts':fs,'unresolved':[],'excluded':[]},d['entities'],d['text'])
        self.assertEqual(b['registry_queue'][0]['predicate'],'previously_unknown_relation');self.assertEqual(len(b['facts']),len(fs))
    def test_filled_with_alias_does_not_create_false_loss(self):
        d=shots()[5];p=copy.deepcopy(d)
        next(f for f in p['facts'] if f['predicate']=='contains')['predicate']='filled_with'
        self.assertEqual(compare(p,d)['overall']['f1'],1)
    def test_warning_does_not_complete_missing_quantity(self):
        d=shots()[5];facts=[f for f in d['facts'] if f['type']!='count'];before=copy.deepcopy(facts)
        ws=warnings(d['text'],d['entities'],facts)
        self.assertTrue(any(w['rule']=='quantity_coverage' for w in ws));self.assertEqual(facts,before)
    def test_warning_flags_combined_body_postures(self):
        d=shots()[6];facts=copy.deepcopy(d['facts']);feet=next(e['id'] for e in d['entities'] if e['canonical']=='foot');facts=[f for f in facts if not (f['type']=='attribute' and f['subject']==feet)]
        self.assertTrue(any(w['rule']=='independent_body_postures' for w in warnings(d['text'],d['entities'],facts)))
    def test_counts_require_unit_and_comparator(self):
        d=shots()[2];fs=model_facts(d['facts']);f=next(x for x in fs if x['type']=='count');f['value']='several'
        with self.assertRaises(ProtocolError):validate_facts({'facts':fs,'unresolved':[],'excluded':[]},d['entities'],d['text'])
    def test_id_permutation_and_order_do_not_change_f1(self):
        d=shots()[6];p=copy.deepcopy(d);mapping={e['id']:f'e{i+20}' for i,e in enumerate(p['entities']) if e['id']!='ctx_image'}
        for e in p['entities']:e['id']=mapping.get(e['id'],e['id'])
        for f in p['facts']:
            for k in ['subject','object']:
                if k in f:f[k]=mapping.get(f[k],f[k])
            f['id']='renamed_'+f['id']
        p['facts'].reverse();p['entities'].reverse()
        self.assertEqual(compare(p,d)['overall']['f1'],1)
    def test_role_polarity_and_count_scope_are_scored(self):
        d=shots()[6];p=copy.deepcopy(d);next(f for f in p['facts'] if f['predicate']=='smile')['object_role']='patient'
        self.assertLess(compare(p,d)['action_roles']['f1'],1)
        d=shots()[2];p=copy.deepcopy(d);next(f for f in p['facts'] if f['type']=='count')['unit']='pair'
        self.assertEqual(compare(p,d)['by_type']['count']['f1'],0)
        d=shots()[7];p=copy.deepcopy(d);next(f for f in p['facts'] if f['predicate']=='holds')['polarity']='positive'
        self.assertLess(compare(p,d)['by_type']['relation']['f1'],1)
    def test_scope_is_not_deduplicated(self):
        d=shots()[0];fs=copy.deepcopy(d['facts']);f=copy.deepcopy(fs[-1]);f['id']='f99';f['event_scope']='later';fs.append(f)
        kept,_=normalize(fs);self.assertEqual(len(kept),len(fs))
    def test_known_change_gold_is_recovered(self):
        ps=probes();base=ps[0]['document']
        for p in ps[1:]:self.assertEqual(change_score(base,p['document'],base,p['document'])['f1'],1)
    def test_assignment_global_not_greedy(self):self.assertEqual(set(assignment([[.9,.8],[.85,0]])),{(0,1),(1,0)})
    def test_two_stage_frozen_anchors_and_pending(self):
        import json
        d=shots()[0];calls=[]
        a={'entities':model_entities([e for e in d['entities'] if e['id']!='ctx_image']),'excluded':[],'unresolved':[]}
        b={'facts':model_facts(d['facts']),'excluded':[],'unresolved':[]}
        def transport(body):
            calls.append(body);data=a if len(calls)==1 else b
            return {'model':'test','choices':[{'finish_reason':'stop','message':{'content':json.dumps(data)}}]}
        client=DecomposerV5(APIConfig('test','placeholder'),transport=transport,frozen_prompts={'entities':'stage_a','facts':'stage_b'})
        result,audit=client.decompose(d['text']);self.assertEqual(len(calls),2)
        self.assertEqual(json.loads(calls[1]['messages'][1]['content'])['entities'],result['entities'])
        self.assertTrue(all(f['verification']=='pending' for f in result['facts']))
        self.assertTrue(all(c['thinking']=={'type':'disabled'} for c in calls));self.assertTrue(audit['raw_valid'])

if __name__=='__main__':unittest.main()
