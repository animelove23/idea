import unittest
from analysis_skeleton.common import read_jsonl
from analysis_skeleton.decompose_iteration_v1.experiment import new_shots,SplitStage
from analysis_skeleton.framework_v2.contracts import normalize_document

class SplitShotTests(unittest.TestCase):
    def test_exactly_one_example_changes(self):
        old=read_jsonl('analysis_skeleton/shots/decompose.jsonl');new=new_shots(old)
        self.assertEqual(len(new),8);self.assertEqual([i for i,(a,b) in enumerate(zip(old,new)) if a!=b],[6])
        self.assertEqual(old[6]['input']['text'],'Two dogs stand beside a beautiful car.')
        for shot in new:self.assertFalse(normalize_document(shot['output'],shot['input']['text'])['issues'])
    def test_partition_has_distinct_ids_and_color_owners(self):
        s=new_shots(read_jsonl('analysis_skeleton/shots/decompose.jsonl'))[6];d=normalize_document(s['output'],s['input']['text'])
        self.assertEqual(len(d['entities']),3)
        attrs=[f for f in d['facts'] if f['type']=='attribute'];self.assertEqual(len({f['entity_id'] for f in attrs}),2)
    def test_prompt_query_model_and_other_messages_unchanged(self):
        a,b=SplitStage('control'),SplitStage('split_shot');x,y=a.messages({'text':'A cup.'}),b.messages({'text':'A cup.'})
        self.assertEqual([i for i,(u,v) in enumerate(zip(x,y)) if u!=v],[13,14])
        self.assertEqual(a.config.model,'deepseek-flash');self.assertEqual(b.config.model,'deepseek-flash')

if __name__=='__main__':unittest.main()
