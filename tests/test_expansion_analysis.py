import unittest
from analysis_skeleton.expansion20.analyze import bootstrap,fact_mapping
from analysis_skeleton.build_fixtures import D,E,A
from analysis_skeleton.contracts import normalize_document


class ExpandedAnalysisTests(unittest.TestCase):
    def test_clustered_bootstrap_constant_rates_and_empty_class(self):
        pairs=[];selection=[]
        for i in range(20):
            p={'pair_id':str(i)}
            for kind in ('entity','attribute'):
                p[kind]={'true':{'denominator':2,'removed':1,'retained':1},
                         'hallucinated':{'denominator':0,'removed':0,'retained':0}}
            pairs.append(p);selection.append({'pair_id':str(i),'length_stratum':i//5+1})
        a=bootstrap(pairs,selection,repetitions=50)
        self.assertEqual(a,bootstrap(pairs,selection,repetitions=50))
        self.assertEqual(a['rates']['entity_true_removed']['ci95'],[.5,.5])
        self.assertIsNone(a['rates']['entity_hallucinated_removed']['rate'])
    def test_fact_mapping_does_not_credit_changed_value(self):
        text='A red car.'
        reference=normalize_document(D([E('e1','car','car')],[A('a1','e1','color','red','red car','red')]),text)
        prediction=normalize_document(D([E('x','car','car')],[A('y','x','color','blue','red car','red')]),text)
        mapped=fact_mapping(prediction,reference)
        self.assertEqual(mapped,{'entity_e1':'entity_x'})
