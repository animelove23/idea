"""Reuse frozen M2 outputs and exact M5 queries; no gold enters the production pipeline."""
import copy
import json
from pathlib import Path
from analysis_skeleton.common import read_jsonl,new_run,check_frozen,digest
from analysis_skeleton.llm import FewShotStage,CallFailure
from analysis_skeleton.m5_verify import VisualStage
from analysis_skeleton.pipeline import execute

ROOT=Path('outputs/skeleton_expansion20')


def visual_key(payload):
    return digest({k:payload.get(k) for k in ('image_sha256','statement','entity_context')})


def replay(record,source):
    audit=copy.deepcopy(record['audit'])
    audit['reused_usage']=audit.pop('usage',None)
    audit['reused_elapsed_seconds']=audit.pop('elapsed_seconds',None)
    audit.update(api_calls=0,elapsed_seconds=0,cache_hit=True,source_result=str(source))
    if 'error' in audit:raise CallFailure(audit)
    return json.loads(audit['raw_content']),audit


class FrozenDecompose:
    def __init__(self,path,identity):
        self.path=Path(path);self.identity=identity
        records=read_jsonl(path)
        self.records={r['audit']['input']['text']:r for r in records}
        if len(records)!=len(self.records):raise ValueError('Duplicate caption cache key')
        if any(r['audit']['identity']!=identity for r in records):raise ValueError('Decompose identity changed')
    def run(self,payload):
        if set(payload)!={'text'} or payload['text'] not in self.records:raise ValueError('Frozen decomposition missing')
        return replay(self.records[payload['text']],self.path)


class ExactVisualCache:
    def __init__(self,stage,path):
        self.stage=stage;self.path=Path(path);self.identity=stage.identity;self.count=0
        self.records={}
        for r in read_jsonl(path):
            if r['audit'].get('identity')!=self.identity:raise ValueError('Vision identity changed')
            if 'prediction' in r:self.records[visual_key(r['audit']['input'])]=r
    def run(self,payload):
        key=visual_key(payload);self.count+=1
        if key in self.records:
            result=replay(self.records[key],self.path);mode='reused'
        else:
            result=self.stage.run(payload);mode='api'
        print(f'M5 end-to-end {self.count} pair={payload["pair_id"]} {mode}',flush=True)
        return result


class Progress:
    def __init__(self,stage):self.stage=stage;self.identity=stage.identity;self.count=0
    def run(self,payload):
        self.count+=1
        result=self.stage.run(payload)
        print(f'M3 end-to-end pair {self.count}',flush=True)
        return result


def main():
    for name in ('m2','m5_independent'):check_frozen(ROOT/name)
    source=Path('analysis_skeleton/fixtures/expansion20/pairs.jsonl')
    pairs=read_jsonl(source)
    decompose=FewShotStage('decompose')
    stages={'decompose':FrozenDecompose(ROOT/'m2/results.jsonl',decompose.identity),
            'align':Progress(FewShotStage('align')),
            'verify':ExactVisualCache(VisualStage(),ROOT/'m5_independent/results.jsonl')}
    new_run(ROOT/'orchestration','expansion20_orchestration',
            [source,ROOT/'m2/results.jsonl',ROOT/'m5_independent/results.jsonl'],
            {'same_input_reuse_only':True,'query_references_sent':False},
            [__file__])
    execute(source,[p['pair_id'] for p in pairs],ROOT/'end_to_end',stages=stages)


if __name__=='__main__':main()
