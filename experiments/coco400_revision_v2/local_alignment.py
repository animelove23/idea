"""Quarantine local contract conflicts without inventing a determinate relation."""
import copy
from .alignment import validate,CHANGES


def validate_local(raw,original,steer):
    r=copy.deepcopy(raw);audit=[];blocked=set();changes={}
    for e in r['entities']:
        bad=e.get('description_change') not in CHANGES or (e.get('status')=='matched' and e.get('description_change') not in {'equivalent','generalized','specialized'})
        if bad:
            audit.append({'table':'entities','raw':copy.deepcopy(e),'reason':'identity_description_contract_conflict'})
            blocked.update((s,x) for s in ('original','steer') for x in e[s])
            e.update(status='unresolved',description_change='unresolved',reason='technical_local_identity_contract_conflict')
        if e.get('status')=='matched' and len(e['original'])==len(e['steer'])==1:changes[(e['original'][0],e['steer'][0])]=e['description_change']
    fs={s:{f['id']:f for f in d['facts']} for s,d in [('original',original),('steer',steer)]}
    for e in r['alignments']:
        refs=[(s,x) for s in ('original','steer') for x in e[s]]
        owners={(s,fs[s][x]['entity_id']) for s,x in refs if x in fs[s]}
        bad=bool(owners&blocked)
        if e.get('status') in {'retained','description_changed'} and len(e['original'])==len(e['steer'])==1:
            a,b=fs['original'].get(e['original'][0],{}),fs['steer'].get(e['steer'][0],{})
            change=changes.get((a.get('entity_id'),b.get('entity_id')))
            if e['status']=='description_changed':bad |= a.get('type')!='entity' or b.get('type')!='entity' or change not in {'generalized','specialized'}
            elif a.get('type')=='entity':bad |= change in {'generalized','specialized'}
        if bad:
            audit.append({'table':'alignments','raw':copy.deepcopy(e),'reason':'dependent_or_local_description_conflict'})
            e.update(status='unresolved',reason='technical_local_fact_contract_conflict')
    result=validate(r,original,steer);result['local_quarantine']=audit
    return result
