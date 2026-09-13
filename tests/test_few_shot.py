import json
import unittest
import tempfile
import contextlib
import io
from unittest.mock import patch
from pathlib import Path
from decomposition.config import load_prompt, SHOT_PATH, APIConfig
from decomposition.schemas import validate_document
from decomposition.semantic_decomposer import build_messages

class FewShotTests(unittest.TestCase):
    def examples(self): return [json.loads(x) for x in SHOT_PATH.read_text(encoding='utf-8').splitlines() if x.strip()]
    def test_exact_eight_and_neutral_ids(self):
        ds=self.examples(); self.assertEqual(len(ds),8)
        for d in ds: validate_document(d,expected_id='caption')
        self.assertEqual(load_prompt().count('\nINPUT JSON:\n'),8)
    def test_control_is_same_rules_without_any_example(self):
        zero=load_prompt(shots=0); few=load_prompt(shots=8)
        self.assertTrue(few.startswith(zero)); self.assertNotIn('INPUT JSON:',zero)
    def test_user_supervision_preserved(self):
        ds=self.examples()
        self.assertTrue(any(e['canonical']=='hand' for e in ds[0]['entities']))
        self.assertEqual(ds[1]['entities'][0]['canonical'],'man')
        self.assertTrue(any(f.get('subject')=='e4' and f['type']=='object' for f in ds[3]['facts']))
        for d in ds:
            self.assertFalse(any(f['type']=='attribute' and f.get('value') in {'busy','comfortable','delicious','refreshing'} for f in d['facts']))
        self.assertTrue(any(f['predicate']=='have_found_place_to_sit' for f in ds[3]['facts']))
    def test_no_metadata_or_truth_in_demonstrations(self):
        messages=build_messages('A hand holds a phone.',load_prompt())
        self.assertEqual(json.loads(messages[-1]['content']),{'id':'caption','text':'A hand holds a phone.'})
        for d in self.examples():
            self.assertEqual(set(d),{'id','text','entities','facts'})
            self.assertTrue(all(f['verification']=='pending' for f in d['facts']))
    def test_unsupported_shot_count_rejected(self):
        with self.assertRaises(ValueError): load_prompt(shots=4)
    def test_pilot_split_and_offline_runner(self):
        from tests import run_fewshot_pilot as pilot
        class FakeClient:
            def __init__(self, *args, **kwargs): pass
            def decompose(self, caption):
                return {'id':'caption','text':caption,'entities':[],'facts':[]}, {'attempts':[{'usage':{'prompt_tokens':1,'completion_tokens':1}}]}
        c=APIConfig(model='test',api_key='placeholder',timeout=120,retries=1)
        with tempfile.TemporaryDirectory() as tmp, patch.object(pilot,'load_api_config',return_value=c), patch.object(pilot,'DeepSeekDecomposer',FakeClient), contextlib.redirect_stdout(io.StringIO()):
            path=Path(tmp)/'pilot'; pilot.prepare(path); pilot.execute(path)
            summary=json.loads((path/'summary.json').read_text(encoding='utf-8'))
            self.assertEqual(summary['completed_jobs'],32)
            self.assertEqual(summary['primary']['0']['success'],14)
            self.assertEqual(summary['primary']['8']['success'],14)
            self.assertEqual(len(summary['repeats']),4)
            self.assertTrue(summary['all_success'])

if __name__=='__main__': unittest.main()
