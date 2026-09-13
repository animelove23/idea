"""Fixed entity/attribute routing; reproduce the conservative 400-pair candidate."""
import copy,json,csv
from analysis_skeleton.common import read_jsonl,write_json,write_jsonl,digest
from experiments.coco400_revision_v2.visual import merge
from experiments.matrix_recovery_v4 import run as base
from experiments.matrix_recovery_v4.bounds import tighten
from experiments.matrix_recovery_v4.report import compare
from .run import SOURCE,ROOT
from .search_binding import validate
from .local_alignment import patch,signature

def main():
    old=read_jsonl(SOURCE);oldmap={r['pair_id']:r for r in old};tasks={t['id']:t['input'] for t in read_jsonl(ROOT/'tasks.jsonl')};results={}
    for r in read_jsonl(ROOT/'calls/results.jsonl'):
        if r['result']['status']=='complete':results[r['id']]=(validate(json.loads(r['result']['audit']['raw_content']),tasks[r['id']]),r['result']['audit'])
    candidate={r['pair_id']:r for r in read_jsonl('outputs/matrix_recovery_v4_approved_repair/D_bounds/pairs.jsonl')};rows=copy.deepcopy(old)
    for r in rows:
        kinds={q['claim_id']:q['claim_type'] for q in r['queue']}
        if r['pair_id'] in results:
            out,audit=results[r['pair_id']]
            for v in r['verification']:
                if kinds[v['claim_id']]=='entity' and v['claim_id'] in out['claims']:
                    v.update(merge(v,{**out['claims'][v['claim_id']],'audit':audit}));v['v5_joint_response_id']=audit.get('response_id')
        b=r['bundle'];b['alignment'],_=patch(b['alignment'],candidate[r['pair_id']]['bundle']['alignment'],b['original'],b['steer'])
        base.recompute(r);r['observation']=tighten(r['observation'],r['ledger'],r['bundle'])
        prior=oldmap[r['pair_id']];pv={v['claim_id']:v for v in prior['verification']}
        for v in r['verification']:
            if kinds[v['claim_id']]=='attribute':assert v==pv[v['claim_id']]
        for side in ('original','steer'):assert digest(b[side])==digest(prior['bundle'][side])
        for table in ('entities','alignments'):
            present={signature(e):e for e in b['alignment'][table]}
            assert all(present.get(signature(e))==e for e in prior['bundle']['alignment'][table] if e['status']!='unresolved')
    name='entity_graph_attribute_frozen';base.ROOT=ROOT;base.emit(name,rows)
    summary,trans=compare(oldmap,rows);summary.update(route='fixed input type: entity=joint_graph; attribute=prior_verification',post_evaluation_selection=True,independent_accuracy_measured=False)
    assert len(rows)==400 and sum(len(r['ledger']) for r in rows)==5959
    with (ROOT/name/'matrix.csv').open(encoding='utf-8-sig',newline='') as f:assert sum(int(x['count']) for x in csv.DictReader(f))==summary['after']
    write_json(ROOT/name/'comparison.json',summary);write_jsonl(ROOT/name/'transitions.jsonl',trans)
    write_jsonl(ROOT/name/'remaining_cases.jsonl',[{'pair_id':r['pair_id'],'original':r['bundle']['original']['text'],'steer':r['bundle']['steer']['text'],'observation':r['observation'],
        'unresolved_alignment':[e for e in r['bundle']['alignment']['alignments'] if e['status']=='unresolved']} for r in rows if not r['observation']['matrix_classifiable']])
    print(summary,flush=True)

if __name__=='__main__':main()
