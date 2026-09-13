import unittest,copy
from analysis_skeleton.common import read_jsonl
from .refine import guarded,alternatives
from .run import SOURCE


class GuardTests(unittest.TestCase):
    def test_real_disjunction_is_not_two_objects(self):
        r=next(r for r in read_jsonl(SOURCE) if r['pair_id']=='18291');b=r['bundle']
        self.assertEqual(alternatives(b['steer']),[('e3','e4','table or shelf')])
        raw={'entities':[{'original':['e3'],'steer':['e4'],'status':'matched','description_change':'equivalent','reason':'same shelf'},
                         {'original':[],'steer':['e3'],'status':'steer_only','description_change':'absent','reason':'new table'}],
             'attributes':[{'original':['a3'],'steer':[],'status':'removed','reason':'wood missing'}]}
        result,audit=guarded(raw,b['original'],b['steer'])
        edge=next(e for e in result['alignments'] if 'entity_e3' in e['original'])
        self.assertEqual(edge['status'],'unresolved');self.assertEqual(set(edge['steer']),{'entity_e3','entity_e4'})
        attr=next(e for e in result['alignments'] if 'a3' in e['original'])
        self.assertEqual(attr['reason'],'subject_identity_unresolved')
        self.assertEqual(raw['attributes'][0]['status'],'removed')

    def test_and_does_not_quarantine(self):
        d={'text':'a table and shelf','entities':[{'id':'e1','mentions':[{'quote':'table','start':2,'end':7}]},
            {'id':'e2','mentions':[{'quote':'shelf','start':12,'end':17}]}]}
        self.assertEqual(alternatives(d),[])

    def test_bad_offsets_cannot_trigger_guard(self):
        d={'text':'a table or shelf','entities':[{'id':'e1','mentions':[{'quote':'table','start':1,'end':7}]},
            {'id':'e2','mentions':[{'quote':'shelf','start':11,'end':16}]}]}
        self.assertEqual(alternatives(d),[])

if __name__=='__main__':unittest.main()
