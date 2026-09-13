"""M6: deterministic truth transitions; explicit missingness, fixed denominators and no LLM stats."""
from collections import Counter
from .common import ratio
from .contracts import LABELS


def analyze(original,steer,alignment,queue,verifications):
    docs={'original':original,'steer':steer}
    by_claim={}
    for v in verifications:
        if v['claim_id'] in by_claim:raise ValueError('Duplicate claim verification')
        label=v.get('label')
        if label is not None and label not in LABELS:raise ValueError('Invalid visual label')
        by_claim[v['claim_id']]=v
    valid_ids={c['claim_id'] for c in queue}
    if len(valid_ids)!=len(queue):raise ValueError('Duplicate queue claim ID')
    if set(by_claim)-valid_ids:raise ValueError('Unknown verification claim ID')
    truth={};links={}
    for c in queue:
        value=by_claim.get(c['claim_id'],{})
        for ref in c['refs']:
            k=(ref['side'],ref['fact_id'])
            if k in truth:raise ValueError('Duplicate fact backfill')
            truth[k]=value.get('label') or 'pending'
        for link in c['token_links']:links[(link['side'],link['fact_id'])]=link
    assigned={}
    for edge in alignment['alignments']:
        for side in docs:
            for fid in edge[side]:
                if (side,fid) in assigned:raise ValueError('Duplicate fact transition')
                assigned[(side,fid)]=edge
    expected={(side,f['id']) for side,d in docs.items() for f in d['facts']}
    if set(assigned)!=expected or set(truth)!=expected:raise ValueError('Incomplete fact assignment/backfill')
    matched={i for e in alignment['entities'] if e['status']=='matched' for i in e['original']}
    rows=[]
    for side,doc in docs.items():
        for f in doc['facts']:
            k=(side,f['id']);edge=assigned[k];other='steer' if side=='original' else 'original'
            peers=edge[other]
            parent_truth=truth.get((side,'entity_'+f['entity_id']))
            conflict=f['type']=='attribute' and truth[k]=='supported' and parent_truth=='hallucinated'
            rows.append({'side':side,'fact_id':f['id'],'type':f['type'],'slot':f['slot'],'entity_id':f['entity_id'],
                         'visual_label':truth[k],'truth_conflict':conflict,'status':edge['status'],
                         'reason':edge.get('reason',''),'removal_reason':edge.get('removal_reason'),
                         'peer_label':truth.get((other,peers[0])) if len(peers)==1 else None,
                         'entity_matched':f['entity_id'] in matched if side=='original' else None,
                         'pos':links.get(k,{}).get('pos',[]),'positions':links.get(k,{}).get('positions',[])})
    metric={}
    for kind in ('entity','attribute'):
        base=[r for r in rows if r['side']=='original' and r['type']==kind]
        stats={}
        for truth_label,name in [('supported','true'),('hallucinated','hallucinated')]:
            eligible=[r for r in base if r['visual_label']==truth_label and not r['truth_conflict']]
            c=Counter(r['status'] for r in eligible);n=len(eligible)
            stats[name]={'denominator':n,'retained':c['retained'],'removed':c['removed'],'modified':c['modified'],
                         'unresolved':c['unresolved'],'removal_lower':ratio(c['removed'],n),
                         'removal_upper':ratio(c['removed']+c['unresolved'],n)}
        stats['original_visual_uncertain']=sum(r['visual_label']=='uncertain' for r in base)
        stats['original_visual_pending']=sum(r['visual_label']=='pending' for r in base)
        stats['original_truth_conflict']=sum(r['truth_conflict'] for r in base)
        stats['added_by_truth']=dict(Counter(r['visual_label'] for r in rows if r['side']=='steer' and r['type']==kind and r['status']=='added'))
        metric[kind]=stats
    ca=[r for r in rows if r['side']=='original' and r['type']=='attribute' and r['entity_matched'] and r['visual_label']=='supported' and not r['truth_conflict']]
    metric['conditional_true_attribute_retention']={'denominator':len(ca),'retained':sum(r['status']=='retained' for r in ca),
                                                   'lower':ratio(sum(r['status']=='retained' for r in ca),len(ca)),
                                                   'upper':ratio(sum(r['status'] in {'retained','unresolved'} for r in ca),len(ca))}
    metric['fact_rows']=len(rows)
    metric['upstream_issue_count']=sum(len(d.get('issues',[])) for d in docs.values())
    metric['unique_claims']=len(queue)
    return {'facts':rows,'metrics':metric}


def execute(bundles_path,queue_path,verification_path,output,synthetic=False):
    """Consume explicit normalized bundles and flat claim_id/label records; no model calls."""
    from pathlib import Path
    from .common import read_jsonl,new_run,write_jsonl,write_csv,report
    bundles=read_jsonl(bundles_path);queue=read_jsonl(queue_path);vs=read_jsonl(verification_path)
    pair_ids=[b['pair_id'] for b in bundles]
    if len(pair_ids)!=len(set(pair_ids)):raise ValueError('Duplicate pair ID')
    if {q['pair_id'] for q in queue}-set(pair_ids):raise ValueError('Unknown queue pair')
    claim_ids=[q['claim_id'] for q in queue];v_ids=[v['claim_id'] for v in vs]
    if len(set(claim_ids))!=len(claim_ids) or len(set(v_ids))!=len(v_ids):raise ValueError('Duplicate claim ID')
    if set(v_ids)-set(claim_ids):raise ValueError('Unknown verification claim')
    out=new_run(output,'M6',[bundles_path,queue_path,verification_path],
                {'llm_calls':0,'synthetic_truth':synthetic},[__file__,Path(__file__).parent/'contracts.py'])
    rows=[];pair_rows=[];analyses=[]
    for b in bundles:
        q=[c for c in queue if c['pair_id']==b['pair_id']];ids={c['claim_id'] for c in q}
        result=analyze(b['original'],b['steer'],b['alignment'],q,[v for v in vs if v['claim_id'] in ids])
        rows.extend({'pair_id':b['pair_id'],**r} for r in result['facts'])
        analyses.append({'pair_id':b['pair_id'],**result['metrics']})
        cap={s:b.get('lexical',{}).get(s,{}).get('caption',{}) for s in ('original','steer')}
        wc={s:cap[s].get('word_len') for s in cap}
        row={'pair_id':b['pair_id'],'original_words':wc['original'],'steer_words':wc['steer'],
             'word_change':None if None in wc.values() else wc['steer']-wc['original'],
             'original_pos_counts':cap['original'].get('pos_counts',{}),
             'steer_pos_counts':cap['steer'].get('pos_counts',{}),
             'original_pos_per100':cap['original'].get('pos_per100',{}),
             'steer_pos_per100':cap['steer'].get('pos_per100',{})}
        for side in ('original','steer'):
            side_rows=[r for r in result['facts'] if r['side']==side]
            supported=sum(r['visual_label']=='supported' and not r['truth_conflict'] for r in side_rows)
            row[side+'_facts']=len(side_rows);row[side+'_supported_facts']=supported
            row[side+'_supported_per100_words']=ratio(100*supported,wc[side]) if wc[side] is not None else None
        for kind in ('entity','attribute'):
            for label in ('true','hallucinated'):
                for k,v in result['metrics'][kind][label].items():row[kind+'_'+label+'_'+k]=v
        row['conditional_true_attribute_retention']=result['metrics']['conditional_true_attribute_retention']
        pair_rows.append(row)
    write_jsonl(out/'pair_analysis.jsonl',analyses)
    write_csv(out/'transitions.csv',list(rows[0]) if rows else ['pair_id'],rows)
    write_csv(out/'pair_metrics.csv',list(pair_rows[0]) if pair_rows else ['pair_id'],pair_rows)
    slices=Counter((r['type'],r['slot'],r['status'],r['visual_label'],p) for r in rows for p in (r['pos'] or ['unlinked']))
    slice_rows=[dict(zip(['type','slot','status','visual_label','pos','fact_memberships'],[*k,n])) for k,n in sorted(slices.items())]
    write_csv(out/'pos_slices.csv',['type','slot','status','visual_label','pos','fact_memberships'],slice_rows)
    metrics={'pairs':len(bundles),'fact_rows':len(rows),'queue_claims':len(queue),'verification_records':len(vs),
             'truth_counts':dict(Counter(r['visual_label'] for r in rows)),
             'original_attribute_removal_reasons':dict(Counter(r['removal_reason'] for r in rows if r['side']=='original' and r['type']=='attribute' and r['status']=='removed')),
             'modified_truth_transitions':dict(Counter(str(r['visual_label'])+' -> '+str(r['peer_label']) for r in rows if r['side']=='original' and r['status']=='modified')),
             'truth_conflicts':sum(r['truth_conflict'] for r in rows),'llm_calls':0,
             'synthetic_truth':synthetic,'research_conclusion_validated':False}
    report(out,'M6 迁移统计与导出',metrics,
           ['synthetic_truth=true时，所有真假分布仅用于手算校验，不能作为模型现象。',
            'POS表为fact在不同词性中的成员数，一条fact可能跨多个POS，不能相加当总事实数。',
            'pending包含未执行或失败；uncertain为已执行的视觉证据不足。两者都不当幻觉。',
            '当前导出按pair统计；同图不同生成条件须分开实验，不能作为独立图像做推断。'])
    return metrics


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser()
    for name in ('bundles','queue','verifications','output'):p.add_argument('--'+name,required=True)
    p.add_argument('--synthetic',action='store_true');a=p.parse_args()
    execute(a.bundles,a.queue,a.verifications,a.output,a.synthetic)
