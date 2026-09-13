"""M4: deterministic shared verification queue and span/token linking."""
from collections import Counter
from .common import digest


def statement(fact, entity):
    if fact['type']=='entity':
        return f'An entity or group described as "{entity["name"]}" is present in the image.'
    if fact['slot']=='material':
        return f'The referenced {entity["name"]} is made of {fact["value"]}.'
    return f'The referenced {entity["name"]} is {fact["value"]}.'


def build_queue(pair_id,original,steer,alignment,image_path,image_sha256=None,lexical=None):
    docs={'original':original,'steer':steer}
    facts={s:{f['id']:f for f in d['facts']} for s,d in docs.items()}
    entities={s:{e['id']:e for e in d['entities']} for s,d in docs.items()}
    for side in docs:
        counts=Counter(i for r in alignment['alignments'] for i in r[side])
        if set(counts)!=set(facts[side]) or any(v!=1 for v in counts.values()):
            raise ValueError('Every input fact must have exactly one alignment assignment')
    queue=[]
    for edge in alignment['alignments']:
        refs=[{'side':s,'fact_id':i} for s in docs for i in edge[s]]
        groups=[refs] if edge['status']=='retained' else [[r] for r in refs]
        for group in groups:
            first=group[0];s=first['side'];f=facts[s][first['fact_id']];e=entities[s][f['entity_id']]
            claim={'claim_id':digest({'pair':pair_id,'refs':group})[:24],'pair_id':pair_id,
                   'image_path':str(image_path),'image_sha256':image_sha256,
                   'refs':group,'statement':statement(f,e),'semantic_type':f['type'],'slot':f['slot'],
                   'entity_context':{'name':e['name'],'source_mentions':[m['quote'] for m in e['mentions']]},
                   'token_links':[],'upstream_status':edge['status']}
            for ref in group:
                side=ref['side'];fact=facts[side][ref['fact_id']]
                record=(lexical or {}).get(side)
                selected=[] if record is None else [t for t in record['tokens'] if any(t['char_start']<v['end'] and v['start']<t['char_end'] for v in fact['value_spans'])]
                claim['token_links'].append({**ref,'status':'linked' if selected else 'unavailable',
                                             'token_ids':[t['token_id'] for t in selected],
                                             'pos':sorted({t['upos'] for t in selected}),
                                             'positions':[t['relative_position'] for t in selected if t['relative_position'] is not None]})
            queue.append(claim)
    all_refs=[(r['side'],r['fact_id']) for c in queue for r in c['refs']]
    if len(all_refs)!=len(set(all_refs)):
        raise ValueError('Duplicate verification backfill reference')
    return queue


def execute(bundles_path, output):
    from .common import read_jsonl,new_run,write_jsonl,report,ratio
    bundles=read_jsonl(bundles_path)
    ids=[b['pair_id'] for b in bundles]
    if len(set(ids))!=len(ids):raise ValueError('Duplicate pair ID')
    out=new_run(output,'M4',[bundles_path],{'llm_calls':0},[__file__])
    queue=[]
    for b in bundles:
        queue.extend(build_queue(b['pair_id'],b['original'],b['steer'],b['alignment'],
                                 b.get('image_path',''),b.get('image_sha256'),b.get('lexical')))
    write_jsonl(out/'verification_queue.jsonl',queue)
    total=sum(len(b[s]['facts']) for b in bundles for s in ('original','steer'))
    links=[link for c in queue for link in c['token_links']]
    metrics={'pairs':len(bundles),'input_facts':total,'backfill_refs':sum(len(c['refs']) for c in queue),
             'queue_coverage':ratio(sum(len(c['refs']) for c in queue),total),'unique_claims':len(queue),
             'shared_claims':sum(len(c['refs'])==2 for c in queue),
             'span_link_rate':ratio(sum(l['status']=='linked' for l in links),len(links)),
             'image_manifest_available':sum(bool(c['image_path'] and c['image_sha256']) for c in queue),
             'llm_calls':0}
    report(out,'M4 验证队列与词语关联',metrics,['结构覆盖率不证明主体对应或视觉命题正确；缺图不会删除事实名册。'])
    return metrics


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--bundles',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();execute(a.bundles,a.output)
