"""Verify three completed run snapshots replay without network or changed outputs."""
import shutil
import socket
from pathlib import Path
from unittest.mock import patch
from analysis_skeleton.common import read_json,read_jsonl,write_json,sha
from analysis_skeleton.final_v1.pipeline import execute

ROOT=Path('outputs/coco400_final_v1')


def main():
    ids=[e['pair_id'] for e in read_jsonl(ROOT/'run_events.jsonl') if e['status']=='exported'][:3]
    assert len(ids)==3
    target=ROOT/'resume_probe';target.mkdir(exist_ok=False)
    names=['bundles.jsonl','verification_queue.jsonl','verification.jsonl','denominator_ledger.jsonl','lexical_slices.jsonl','strict_analysis.json']
    results=[]
    for pid in ids:
        original=ROOT/'runs'/pid;snapshot=target/pid
        shutil.copytree(original,snapshot)
        before={name:sha(snapshot/name) for name in names}
        with patch.object(socket.socket,'connect',side_effect=AssertionError('offline_probe_network_forbidden')):
            m=execute(ROOT/'pairs.jsonl',snapshot,[pid],resume=True,profile=ROOT/'profile.json',
                condition_id='coco400_greedy_baseline_vs_vista',replicate_id='r1')
        assert m['new_api_calls_this_invocation']==0
        assert before=={name:sha(snapshot/name) for name in names}
        assert before=={name:sha(original/name) for name in names}
        results.append({'pair_id':pid,'new_api_calls':0,'reused_checkpoints':m['resumed_checkpoints'],
            'exports_byte_identical':True,'original_artifacts_unchanged':True})
    write_json(target/'result.json',{'passed':True,'network_blocked':True,'results':results})
    print(results)


if __name__=='__main__':main()
