import copy,unittest
from experiments.coco400_revision_v2.fixtures import doc
from experiments.entity_attribute_v3.m3 import validate
from .local_alignment import patch,signature

class PatchTests(unittest.TestCase):
    def docs(self):return doc('A red chair.','chair',('red','color')),doc('A red chair.','chair',('red','color'))
    def matching(self,a,b):
        return validate({'entities':[{'original':['e1'],'steer':['e1'],'status':'matched','description_change':'equivalent','reason':'same chair'}],
            'attributes':[{'original':['a1'],'steer':['a1'],'status':'retained','reason':'same color'}]},a,b)
    def test_unresolved_component_can_be_completed(self):
        a,b=self.docs();old=validate({'entities':[],'attributes':[]},a,b);new=self.matching(a,b)
        result,audit=patch(old,new,a,b)
        self.assertEqual(audit['status'],'validated_patch');self.assertTrue(all(e['status']=='retained' for e in result['alignments']))
    def test_locked_identity_and_facts_cannot_be_replaced(self):
        a,b=self.docs();old=self.matching(a,b);new=validate({'entities':[],'attributes':[]},a,b)
        result,audit=patch(old,new,a,b);self.assertEqual(result,old)
    def test_proposal_touching_locked_ref_is_not_inserted(self):
        a,b=self.docs();old=self.matching(a,b)
        old['alignments'][1].update(status='unresolved',reason='test')
        new=copy.deepcopy(old);new['alignments']=[{'original':['a1'],'steer':['entity_e1'],'status':'modified','reason':'wrong peer'}]
        result,audit=patch(old,new,a,b)
        self.assertEqual(result,old)

if __name__=='__main__':unittest.main()
