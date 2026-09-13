"""Continue the authorized local-guard/visual branch without sending internal drafts."""
import argparse
from . import refine,run
from analysis_skeleton.common import read_jsonl,write_jsonl,write_json


def build():
    root=refine.ROOT;local=read_jsonl(root/'local_results.jsonl')
    (root/'align_calls').mkdir(exist_ok=False)
    write_jsonl(root/'align_calls/results.jsonl',[{'id':r['id'],'result':{'status':'complete','value':r['value']}} for r in local])
    write_json(root/'align_calls/README.json',{'not_model_calls':True,'source':'400 original v4 model responses plus local guards',
        'remote_repair_executed':False,'remote_repair_tasks':42,'reason':'automatic approval rejected transmitting previous model responses and validation issues'})
    write_json(root/'repair_status.json',{'status':'not_executed_approval_rejected','requests':0,'planned':42,
        'reason':'previous model responses and validation issues lack explicit outbound authorization; use local guards and retain residual uncertainty'})
    run.ROOT=root;run.align_result()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['B','visual','C']);p.add_argument('--resume',action='store_true');a=p.parse_args()
    if a.action=='B':build()
    else:
        run.ROOT=refine.ROOT
        if a.action=='visual':run.calls('visual',a.resume)
        else:run.visual_result()
