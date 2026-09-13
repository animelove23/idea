import unittest
from .observe import candidates,analyze_pair


def fixture(status='retained',a='supported',b='supported'):
    facts={s:[{'id':'entity_e1','entity_id':'e1','type':'entity'}] for s in ('original','steer')}
    edge={'original':['entity_e1'],'steer':['entity_e1'],'status':status}
    if status=='removed':facts['steer']=[];edge['steer']=[]
    if status=='added':facts['original']=[];edge['original']=[]
    bundle={'pair_id':'1','alignment':{'alignments':[edge]},'lexical':{s:{'caption':{'word_len':n,'pos_counts':{'NOUN':1,'DET':n-1}}} for s,n in [('original',4),('steer',2)]}}
    ledger=[]
    for s,label in [('original',a),('steer',b)]:
        bundle[s]={'facts':facts[s],'entities':[{'id':'e1','mentions':[]}],'issues':[]}
        for f in facts[s]:ledger.append({'side':s,'fact_id':f['id'],'entity_id':'e1','type':'entity','slot':'existence','visual_label':label,'status':status})
    return bundle,ledger


class ObservationTests(unittest.TestCase):
    def test_four_set_changes(self):
        self.assertEqual(candidates(0,0),['unchanged']);self.assertEqual(candidates(1,0),['gained'])
        self.assertEqual(candidates(0,1),['lost']);self.assertEqual(candidates(1,1),['mixed'])
    def test_uncertainty_not_zero_and_mixed_remains_mixed(self):
        self.assertEqual(candidates(0,1,True),['lost','mixed'])
        self.assertEqual(candidates(1,1,True,True),['mixed'])
    def test_equal_count_replacement_is_mixed(self):
        r,e=analyze_pair(*fixture('modified'));self.assertEqual(r['supported_change'],'mixed')
        self.assertEqual(r['components'][0]['modified_out'],1)
    def test_hallucination_correction(self):
        r,e=analyze_pair(*fixture('modified','hallucinated','supported'))
        self.assertEqual((r['hallucination_change'],r['supported_change']),('lost','gained'))
    def test_unknown_removed_not_unchanged(self):
        r,e=analyze_pair(*fixture('removed','uncertain'))
        self.assertFalse(r['matrix_classifiable'])
    def test_retained_unknown_is_no_semantic_change_but_not_zero_hallucination(self):
        r,e=analyze_pair(*fixture('retained','uncertain','uncertain'))
        self.assertTrue(r['matrix_classifiable']);self.assertEqual(r['hallucination_unchanged_subtype'],'zero_known_but_visual_membership_unknown')
    def test_retained_label_conflict_not_fake_transition(self):
        r,e=analyze_pair(*fixture('retained','supported','hallucinated'))
        self.assertFalse(r['matrix_classifiable']);self.assertEqual(r['components'][0]['loss'],0)
    def test_pos_decomposition_identity(self):
        r,e=analyze_pair(*fixture());self.assertEqual(sum(r['pos_reduction_contribution'].values()),r['word_reduction'])
    def test_extraction_issue_blocks_confident_matrix(self):
        b,l=fixture();b['original']['issues']=[{'kind':'bad_quote'}]
        r,e=analyze_pair(b,l);self.assertFalse(r['matrix_classifiable'])
    def test_false_parent_attribute_not_double_counted_as_hallucination(self):
        b,l=fixture('removed','hallucinated');f={'id':'a1','entity_id':'e1','type':'attribute'}
        b['original']['facts'].append(f);b['alignment']['alignments'].append({'original':['a1'],'steer':[],'status':'removed'})
        l.append({'side':'original','fact_id':'a1','entity_id':'e1','type':'attribute','slot':'color','visual_label':'hallucinated','parent_visual_label':'hallucinated','status':'removed'})
        r,e=analyze_pair(b,l);self.assertEqual(r['components'][1]['loss'],1);self.assertEqual(r['components'][3]['loss'],0)
    def test_attribute_removed_with_retained_parent(self):
        self.check_attribute_removal('retained','parent_retained_attribute_removed')
    def test_attribute_removed_with_removed_parent(self):
        self.check_attribute_removal('removed','parent_removed')
    def check_attribute_removal(self,parent_status,expected):
        b,l=fixture(parent_status)
        b['original']['facts'].append({'id':'a1','entity_id':'e1','type':'attribute'})
        b['alignment']['alignments'].append({'original':['a1'],'steer':[],'status':'removed'})
        l.append({'side':'original','fact_id':'a1','entity_id':'e1','type':'attribute','slot':'color',
                  'visual_label':'supported','parent_visual_label':'supported','strict_parent_supported_eligible':True,'status':'removed'})
        r,e=analyze_pair(b,l);self.assertEqual(r['attribute_removal_components'],{expected:1})


if __name__=='__main__':unittest.main()
