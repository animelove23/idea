"""Repair integration on the authorized 20-image roster with exact-input response reuse."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from analysis_skeleton.common import read_json,read_jsonl,write_json,write_jsonl,new_run,check_frozen,report,sha,digest
from analysis_skeleton.contracts import model_document
from analysis_skeleton.llm import FewShotStage
from analysis_skeleton.m5_verify import VisualStage,validate_label
from analysis_skeleton.m6_analysis import execute as export_analysis
from analysis_skeleton.pipeline import call
from analysis_skeleton.expansion20.run_end_to_end import visual_key,replay
from .alignment import validate_alignment
from .context import SourceLocator,build_queue

BASE=Path('outputs/skeleton_expansion20')
ROOT=Path('outputs/skeleton_repair_v1')


class ExactCache:
    def __init__(self,stage,records,key):
        self.stage=stage;self.identity=stage.identity;self.key=key;self.records={}
        for record,source in records:
            audit=record.get('audit',{})
            if audit.get('identity')==stage.identity and audit.get('raw_content') and 'error' not in audit:
                self.records[key(audit['input'])]=(record,source)
    def run(self,payload):
        hit=self.records.get(self.key(payload))
        return replay(*hit) if hit else self.stage.run(payload)


def main():
    for p in (BASE/'end_to_end',ROOT/'m2_replay',ROOT/'visual_ab'):check_frozen(p)
    source=Path('analysis_skeleton/fixtures/expansion20/pairs.jsonl');pairs=read_jsonl(source)
    docs={r['case_id']:r['document'] for r in read_jsonl(ROOT/'m2_replay/results.jsonl')}
    old_bundles={b['pair_id']:b for b in read_jsonl(BASE/'end_to_end/bundles.jsonl')}
    old_align=[(read_json(p),str(p)) for p in sorted((BASE/'end_to_end').glob('pair_*/m3.json'))]
    visual_records=[(r,str(ROOT/'visual_ab/results.jsonl')) for r in read_jsonl(ROOT/'visual_ab/results.jsonl') if r['condition']=='context' and 'prediction' in r]
    align=ExactCache(FewShotStage('align'),old_align,digest)
    vision=ExactCache(VisualStage(),visual_records,visual_key)
    locator=SourceLocator();package=Path('analysis_skeleton')
    inputs=[source,ROOT/'m2_replay/results.jsonl',ROOT/'visual_ab/results.jsonl',BASE/'end_to_end/bundles.jsonl',
            *[p for _,p in old_align],*[p['image_path'] for p in pairs],
            *[package/'prompts'/f'{s}.txt' for s in ('align','verify')],
            *[package/'shots'/f'{s}.jsonl' for s in ('align','verify')],
            *[e['input']['image_path'] for e in vision.stage.shots]]
    code=[__file__,Path(__file__).with_name('alignment.py'),Path(__file__).with_name('context.py'),
          *[package/n for n in ('pipeline.py','contracts.py','m3_align.py','m4_queue.py','m5_verify.py','m6_analysis.py','llm.py')],
          package/'expansion20/run_end_to_end.py']
    out=new_run(ROOT/'end_to_end','repair_integration',inputs,
        {'align':align.identity,'verify':vision.identity,'locator':locator.identity,
         'm2_source':'same saved response + local mention repair','m1_source':'unchanged caption cached lexical output',
         'cache_policy':'exact model identity and complete model payload only','references_sent':False,
         'vision_workers':4},code)
    bundles=[];queue=[];verifications=[];audits=[];statuses=[]
    for i,p in enumerate(pairs):
        check_frozen(out);pairdir=out/f'pair_{i:04d}';pairdir.mkdir()
        d={s:docs[p[s]['caption_id']] for s in ('original','steer')}
        for s in d:assert d[s]['text']==p[s]['text']
        lexical=old_bundles[p['pair_id']]['lexical']
        response=call(align,{s:model_document(d[s]) for s in d},pairdir/'m3.json',
                      lambda raw:validate_alignment(raw,d['original'],d['steer']))
        audits.append(response['audit'])
        aligned=response.get('value') or validate_alignment({'entities':[],'alignments':[]},d['original'],d['steer'])
        bundle={'pair_id':p['pair_id'],**d,'alignment':aligned,'lexical':lexical,
                'image_path':p['image_path'],'image_sha256':p['image_sha256']}
        bundles.append(bundle);write_json(pairdir/'bundle.json',bundle)
        items=build_queue(p['pair_id'],d['original'],d['steer'],aligned,p['image_path'],p['image_sha256'],lexical,locator)
        queue+=items;write_jsonl(pairdir/'verification_queue.jsonl',items)
        assert sha(p['image_path'])==p['image_sha256']
        def verify_item(item):
            check_frozen(out)
            result=call(vision,item,pairdir/f'm5_{item["claim_id"]}.json',validate_label)
            return result['audit'],{'claim_id':item['claim_id'],'label':None,'status':result['status'],**result.get('value',{})}
        with ThreadPoolExecutor(max_workers=4) as pool:
            for audit,value in pool.map(verify_item,items):
                audits.append(audit);verifications.append(value)
        statuses.append({'pair_id':p['pair_id'],'alignment_status':aligned['status'],
                         'alignment_call_status':response['status'],'claims':len(items)})
        write_jsonl(out/'bundles.jsonl',bundles);write_jsonl(out/'verification_queue.jsonl',queue)
        write_jsonl(out/'verification.jsonl',verifications);write_jsonl(out/'pair_status.jsonl',statuses)
        print(f'Repair E2E {i+1}/{len(pairs)} pair={p["pair_id"]} claims={len(items)} align={aligned["status"]}',flush=True)
    export_analysis(out/'bundles.jsonl',out/'verification_queue.jsonl',out/'verification.jsonl',out/'m6')
    report(out,'修复版本端到端集成复测',{'pairs':len(pairs),'facts':sum(len(d[s]['facts']) for d in bundles for s in ('original','steer')),
        'claims':len(queue),'pending_claims':sum(v['label'] is None for v in verifications),
        'new_api_calls':sum(a.get('api_calls',0) for a in audits),'cached_calls':sum(bool(a.get('cache_hit')) for a in audits),
        'new_tokens':sum((a.get('usage') or {}).get('total_tokens',0) for a in audits),
        'm3_new_calls':sum(a.get('api_calls',0) for a in audits if a.get('stage')=='align'),
        'm5_new_calls':sum(a.get('api_calls',0) for a in audits if a.get('stage')=='verify')},
        ['M2使用已修复的同批输出；M3输入完全相同时重放原响应，否则重新请求；M5只复用完全相同图像/命题/语境/模型的预测。',
         '集成同时包含三项修复，仅验证连接和统计可用；不得将集成差异归因于单个变量。',
         '没有扩大图像或caption范围，没有用参考标签回填预测。'])


if __name__=='__main__':main()
