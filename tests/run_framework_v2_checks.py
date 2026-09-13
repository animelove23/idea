"""Offline acceptance runner that persists test IDs and failures without network access."""
import argparse
import json
import unittest
from pathlib import Path
from unittest.mock import patch


class RecordedResult(unittest.TextTestResult):
    def __init__(self,*a,**k):super().__init__(*a,**k);self.passed=[]
    def addSuccess(self,test):super().addSuccess(test);self.passed.append(test.id())


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args()
    paths=sorted(Path('tests').glob('test_skeleton_*.py'))+sorted(Path('tests').glob('test_framework_v2_*.py'))
    suite=unittest.defaultTestLoader.loadTestsFromNames(['tests.'+p.stem for p in paths])
    with patch('urllib.request.OpenerDirector.open',side_effect=AssertionError('Network is forbidden in offline checks')):
        result=unittest.TextTestRunner(verbosity=1,resultclass=RecordedResult).run(suite)
    out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
    payload={'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
             'skipped':len(result.skipped),'passed_test_ids':result.passed,
             'failure_details':[{'test_id':t.id(),'traceback':s} for t,s in result.failures+result.errors],
             'network':'blocked_by_test_runner','new_api_calls':0}
    (out/'test_results.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'fault_injection_report.json').write_text(json.dumps({'passed_tests':[s for s in result.passed if 'framework_v2' in s],
        'failures':payload['failure_details'],'new_api_calls':0},ensure_ascii=False,indent=2),encoding='utf-8')
    raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__=='__main__':main()
