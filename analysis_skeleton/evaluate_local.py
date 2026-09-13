"""Per-module offline regression reports plus explicitly synthetic downstream arithmetic."""
import argparse
import io
import unittest
from pathlib import Path
from .common import new_run,read_jsonl,write_jsonl,report
from .m1_lexical import LexicalRecorder
from .m3_align import validate_alignment
from .m4_queue import execute as queue_execute
from .m6_analysis import execute as analysis_execute


def execute(output):
    root=Path(output)
    out=new_run(root,'local_evaluation',[],{'external_calls':0},[__file__])
    results=[]
    code_root=Path(__file__).parent
    for i in range(7):
        testfile=Path(f'tests/test_skeleton_m{i}.py')
        files=list(code_root.glob('*.py'))
        module_out=new_run(out/f'm{i}',f'M{i}_regression',[testfile],{'llm_calls':0},files)
        stream=io.StringIO()
        suite=unittest.defaultTestLoader.loadTestsFromName(f'tests.test_skeleton_m{i}')
        result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
        (module_out/'tests.txt').write_text(stream.getvalue(),encoding='utf-8')
        metrics={'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
                 'passed':result.wasSuccessful(),'semantic_model_accuracy':None}
        report(module_out,f'M{i} 本地回归测评',metrics,['这里测工程约束、故障隔离和计数，不用mock正确率替代模型测评。'])
        results.append({'module':f'M{i}',**metrics})
        print(f'M{i}: {result.testsRun} tests; passed={result.wasSuccessful()}',flush=True)
    if not all(r['passed'] for r in results):raise AssertionError('Local module regression failed')
    cases_path=code_root/'fixtures/align_cases.jsonl'
    parser=LexicalRecorder();bundles=[]
    for c in read_jsonl(cases_path):
        # Hand-built upstream fixtures, never presented as real model outputs.
        bundles.append({'pair_id':c['case_id'],'fixture':True,'original':c['original'],'steer':c['steer'],
                        'alignment':validate_alignment(c['reference'],c['original'],c['steer']),
                        'image_path':'','image_sha256':None,
                        'lexical':{s:parser.record(c['case_id']+'_'+s,c[s]['text']) for s in ('original','steer')}})
    bundles_path=out/'controlled_bundles.jsonl';write_jsonl(bundles_path,bundles)
    queue_execute(bundles_path,out/'m4_controlled')
    qpath=out/'m4_controlled/verification_queue.jsonl';q=read_jsonl(qpath)
    vpath=out/'synthetic_verifications.jsonl'
    write_jsonl(vpath,[{'claim_id':c['claim_id'],
                       'label':'hallucinated' if c['upstream_status']=='added' else 'supported',
                       'provenance':'synthetic_arithmetic_fixture_not_visual_prediction'} for c in q])
    analysis_execute(bundles_path,qpath,vpath,out/'m6_controlled',synthetic=True)
    report(out,'逐模块本地测评总览',{'modules':results,'tests':sum(r['tests'] for r in results),'external_calls':0},
           ['M4/M6控制用例导出齐备；视觉标签是明示的合成输入，不是DeepSeek图像判定。',
            '真实在线模型结果分别见同级m2_online、m3_online、m5_online。'])


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();execute(a.output)
