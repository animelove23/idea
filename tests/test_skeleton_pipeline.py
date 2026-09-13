import copy
import tempfile
import unittest
from pathlib import Path
from analysis_skeleton.common import read_json,read_jsonl,write_jsonl
from analysis_skeleton.llm import CallFailure
from analysis_skeleton.pipeline import execute


class Stub:
    identity={'model':'offline_stub_not_model_evaluation'}
    def __init__(self,responses):self.responses=iter(responses);self.inputs=[]
    def run(self,payload):
        self.inputs.append(copy.deepcopy(payload));result=next(self.responses)
        if isinstance(result,Exception):raise result
        return copy.deepcopy(result),{'transport':'offline_stub'}


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.entity={'id':'e1','name':'car','mentions':[{'quote':'car','occurrence':0}]}
        self.original={'entities':[self.entity],'attributes':[{'id':'a1','entity_id':'e1','slot':'color','value':'red',
            'evidence':[{'quote':'red car','occurrence':0}],'value_quotes':[{'quote':'red','occurrence':0}]}],'excluded':[]}
        self.steer={'entities':[self.entity],'attributes':[],'excluded':[]}
        self.aligned={'entities':[{'original':['e1'],'steer':['e1'],'status':'matched'}],
                      'alignments':[{'original':['entity_e1'],'steer':['entity_e1'],'status':'retained'},
                                    {'original':['a1'],'steer':[],'status':'removed'}]}
        self.pair={'pair_id':'p','image_path':'','image_sha256':None,'image_status':'missing',
                   'original':{'caption_id':'p_original','text':'A red car.'},
                   'steer':{'caption_id':'p_steer','text':'A car.'}}
    def run_case(self,folder,visual=False,failure=False):
        if visual:
            inp=read_jsonl('analysis_skeleton/fixtures/verify_cases.jsonl')[0]['input']
            self.pair.update(image_path=inp['image_path'],image_sha256=inp['image_sha256'],image_status='ready')
        stages={'decompose':Stub([CallFailure({'error':'offline_simulated_failure'}) if failure else self.original,self.steer]),
                'align':Stub([self.aligned]),'verify':Stub([{'label':'supported','reason':'offline fixture'},
                                                         {'label':'hallucinated','reason':'offline fixture'}])}
        source=Path(folder)/'pairs.jsonl';write_jsonl(source,[self.pair]);out=Path(folder)/'result'
        execute(source,['p'],out,stages=stages)
        return stages,out
    def test_real_m0_schema_and_shared_visual_backfill(self):
        with tempfile.TemporaryDirectory() as td:
            stages,out=self.run_case(td,visual=True)
            self.assertEqual(len(stages['decompose'].inputs),2)
            self.assertEqual(len(stages['align'].inputs),1)
            self.assertEqual(len(stages['verify'].inputs),2)
            m=read_json(out/'m6/metrics.json')
            self.assertEqual(m['fact_rows'],3)
            self.assertEqual(m['truth_counts'],{'supported':2,'hallucinated':1})
    def test_missing_image_keeps_facts_and_makes_no_visual_calls(self):
        with tempfile.TemporaryDirectory() as td:
            stages,out=self.run_case(td)
            self.assertEqual(len(stages['verify'].inputs),0)
            self.assertEqual(read_json(out/'m6/metrics.json')['truth_counts'],{'pending':3})
    def test_failed_decompose_blocks_normal_alignment(self):
        with tempfile.TemporaryDirectory() as td:
            stages,out=self.run_case(td,failure=True)
            self.assertEqual(len(stages['align'].inputs),0)
            self.assertEqual(read_jsonl(out/'pair_status.jsonl')[0]['status'],'decomposition_failure')
            self.assertEqual(read_jsonl(out/'bundles.jsonl')[0]['alignment']['alignments'][0]['status'],'unresolved')
    def test_missing_caption_preserved_in_roster_without_calls(self):
        self.pair['steer']=None
        with tempfile.TemporaryDirectory() as td:
            stages,out=self.run_case(td)
            self.assertEqual(sum(len(s.inputs) for s in stages.values()),0)
            self.assertEqual(read_jsonl(out/'pair_status.jsonl')[0]['status'],'missing_caption')
