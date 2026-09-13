"""Replay new M3 responses locally and split unsafe old shared visual claims."""
import copy,json
from pathlib import Path
from analysis_skeleton.common import read_jsonl,write_jsonl,write_json,digest
from analysis_skeleton.final_v1.pipeline import enrich_queue
from analysis_skeleton.m4_queue import statement
from analysis_skeleton.framework_v2.ledger import production
from .local_alignment import validate_local
from .observation import analyze_pair
from . import run

ROOT=Path('outputs/coco400_revision_v2_guard')


def main():
    run.ROOT=ROOT;aligned={r['id']:r['result'] for r in read_jsonl(ROOT/'align_calls/results.jsonl')}
    result=[];tasks=[];quarantines=0;newbindings=0
    for item in read_jsonl(ROOT/'A_scope_only/pairs.jsonl'):
        r=copy.deepcopy(item);b=r['bundle'];pid=r['pair_id'];saved=aligned[pid]
        raw=saved.get('audit',{}).get('raw_content')
        b['alignment']=validate_local(json.loads(raw) if raw else {'entities':[],'alignments':[]},b['original'],b['steer'])
        quarantines+=len(b['alignment']['local_quarantine']);vmap={v['claim_id']:v for v in r['verification']}
        queue=[];values=[]
        for q in r['queue']:
            refs={(x['side'],x['fact_id']) for x in q['refs']}
            safe=len(refs)==1 or any(e['status']=='retained' and refs=={(s,f) for s in ('original','steer') for f in e[s]} for e in b['alignment']['alignments'])
            if safe:queue.append(q);values.append(vmap[q['claim_id']]);continue
            for index,ref in enumerate(q['refs']):
                nq=copy.deepcopy(q);nq['refs']=[ref];nq['claim_id']=digest({'pair':pid,'refs':[ref]})[:24]
                d=b[ref['side']];f=next(f for f in d['facts'] if f['id']==ref['fact_id']);e=next(e for e in d['entities'] if e['id']==f['entity_id'])
                nq['statement']=statement(f,e);nq['token_links']=[t for t in nq['token_links'] if t['side']==ref['side'] and t['fact_id']==ref['fact_id']]
                nq=enrich_queue([nq],{s:b[s] for s in ('original','steer')})[0]
                v=copy.deepcopy(vmap[q['claim_id']]);v['claim_id']=nq['claim_id'];v['source_old_claim_id']=q['claim_id']
                if index:
                    v.update(label='uncertain',reason='independent_visual_rebinding_required',needs_rebinding=True);newbindings+=1
                queue.append(nq);values.append(v)
        r['queue']=queue;r['verification']=values
        ledger,_,_,_=production(b,queue,values);r['ledger']=ledger;r['observation'],r['events']=analyze_pair(b,ledger);result.append(r)
        qmap={q['claim_id']:q for q in queue};vmap={v['claim_id']:v for v in values}
        byref={(ref['side'],ref['fact_id']):q['claim_id'] for q in queue for ref in q['refs']}
        target={k for k,v in vmap.items() if v['label']=='uncertain'}
        for row in ledger:
            if row['type']=='attribute' and (row['claim_id'] in target or (row['visual_label']=='supported' and row['parent_visual_label']!='supported')):
                target.add(row['claim_id']);parent=byref.get((row['side'],'entity_'+row['entity_id']))
                if parent:target.add(parent)
        for cid in sorted(target):
            q=qmap[cid];v=vmap[cid]
            payload={k:copy.deepcopy(q[k]) for k in ('image_path','image_sha256','statement','entity_context','claim_type')}
            payload.update(review_bbox=None if v.get('needs_rebinding') else v.get('evidence',{}).get('bbox'),
                review_focus='locate the intended referent in full image' if q['claim_type']=='entity' else 'resolve the owner, then inspect '+q['slot'])
            tasks.append({'id':pid+':'+cid,'pair_id':pid,'claim_id':cid,'input':payload,'purpose':'new_binding' if v.get('needs_rebinding') else 'second_review'})
    run.emit('B2_local_and_rebinding',result)
    write_jsonl(ROOT/'review_rebound_tasks.jsonl',tasks)
    write_json(ROOT/'rebinding_plan.json',{'local_quarantined_rows':quarantines,'new_independent_bindings':newbindings,
        'review_calls':len(tasks),'additional_llm_calls_for_local_replay':0,'first_query_fact_keeps_its_own_visual_label':True})
    print({'quarantine_rows':quarantines,'bindings':newbindings,'visual_tasks':len(tasks)},flush=True)


if __name__=='__main__':main()
