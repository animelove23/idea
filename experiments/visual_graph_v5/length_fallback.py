"""One predeclared bounded re-run for completed responses truncated at token limit."""
from pathlib import Path
from analysis_skeleton.common import read_jsonl,read_json,write_jsonl,write_json,new_run,digest,check_frozen
from analysis_skeleton.framework_v2.runtime import SafeStage,Checkpoints
from analysis_skeleton.final_v1.routing import routing_inputs
from .bounded_stage import BoundedStage,compile_bounded
from .legacy_eval import ROOT as LEGACY

ROOT=LEGACY/'bounded_fallback'

def main():
    tasks={t['id']:t for t in read_jsonl(LEGACY/'tasks.jsonl')}
    failed=[r for r in read_jsonl(LEGACY/'run/results.jsonl') if r['result'].get('audit',{}).get('finish_reason')=='length']
    ROOT.mkdir(exist_ok=False);selected=[tasks[r['id']] for r in failed];write_jsonl(ROOT/'tasks.jsonl',selected)
    write_json(ROOT/'protocol.json',{'trigger':'recorded completed HTTP response finish_reason=length only','calls':len(selected),
        'fallback_passes':1,'region_budget':'at most number of query claims','reference_labels_sent':False})
    out=ROOT/'run';new_run(out,'bounded_truncation_fallback',[ROOT/'tasks.jsonl',ROOT/'protocol.json',*routing_inputs('outputs/final_v1_release/visual_routes.json')],
        {'model':'deepseek-flash'},list(Path(__file__).parent.glob('*.py')))
    manifest=read_json(out/'manifest.json');stage=SafeStage(BoundedStage());rows=[]
    for t in selected:
        cp=Checkpoints(out/'checkpoints',digest(manifest));result=cp.call(t['id'],stage,t['input'],lambda raw:compile_bounded(raw,t['input']))
        rows.append({'id':t['id'],'result':result,'new_calls':cp.new_api_calls})
    write_jsonl(out/'results.jsonl',rows);check_frozen(out)
    print([{'id':r['id'],'status':r['result']['status'],'finish':r['result'].get('audit',{}).get('finish_reason')} for r in rows],flush=True)

if __name__=='__main__':main()
