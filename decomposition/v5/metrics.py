"""Frozen entity-aware exact semantic-structure scoring, not JSON equality.

No LLM judge or prediction-driven alias expansion. Hungarian alignment uses
entity metadata alone. Modality, polarity, role, count unit/scope are scored.
"""
import json
import re
from collections import Counter
from .schema import REGISTRY,TYPES

def assignment(weights):
    # Rectangular maximum-weight Hungarian algorithm, padded with dummy nodes.
    nr=len(weights);nc=len(weights[0]) if nr else 0;n=max(nr,nc)
    if not n:return []
    costs=[[1-(weights[i][j] if i<nr and j<nc else 0) for j in range(n)] for i in range(n)]
    u=[0.]*(n+1);v=[0.]*(n+1);p=[0]*(n+1);way=[0]*(n+1)
    for i in range(1,n+1):
        p[0]=i;j0=0;mins=[float('inf')]*(n+1);used=[False]*(n+1)
        while True:
            used[j0]=True;i0=p[j0];delta=float('inf');j1=0
            for j in range(1,n+1):
                if not used[j]:
                    cur=costs[i0-1][j-1]-u[i0]-v[j]
                    if cur<mins[j]:mins[j]=cur;way[j]=j0
                    if mins[j]<delta:delta=mins[j];j1=j
            for j in range(n+1):
                if used[j]:u[p[j]]+=delta;v[j]-=delta
                else:mins[j]-=delta
            j0=j1
            if p[j0]==0:break
        while True:
            j1=way[j0];p[j0]=p[j1];j0=j1
            if not j0:break
    return [(p[j]-1,j-1) for j in range(1,n+1) if 0<p[j]<=nr and j<=nc]

def canonical(e):return REGISTRY['canonical_aliases'].get(e['canonical'],e['canonical'])

def tokens(e):
    return set(re.findall(r'[a-z]+',' '.join(s['quote'] for s in e.get('mentions',[])).lower()))-{'a','an','the','of','is','are'}

def align_entities(pred,gold):
    pe=pred.get('entities',[]);ge=gold.get('entities',[])
    weights=[]
    for e in pe:
        row=[]
        for g in ge:
            if canonical(e)!=canonical(g) or e['kind']!=g['kind'] or e.get('group_link')!=g.get('group_link'):row.append(0);continue
            et,gt=tokens(e),tokens(g);overlap=len(et&gt)/max(1,len(et|gt))
            score=.65+.35*overlap
            # Resolve duplicate classes via mentions, never by matching fact predicates.
            if e['kind']=='context':score=1
            row.append(score)
        weights.append(row)
    pairs=assignment(weights);mapping={};ambiguous=[]
    for i,j in pairs:
        if weights[i][j]<.65:continue
        score=weights[i][j]
        if sum(abs(x-score)<1e-10 for x in weights[i] if x>=.65)>1:
            ambiguous.append(pe[i]['id']);continue
        mapping[pe[i]['id']]=ge[j]['id']
    # Group bindings are semantic: incompatible parent mappings invalidate child mapping.
    gmap={e['id']:e for e in ge}
    for e in pe:
        if e['id'] in mapping and e.get('group_parent'):
            if mapping.get(e['group_parent'])!=gmap[mapping[e['id']]].get('group_parent'):mapping.pop(e['id'])
    return mapping,ambiguous

def val(v):
    if isinstance(v,str):return {'wooden':'wood','black and white':'black_and_white','several':'several'}.get(v.lower().strip(),v.lower().strip())
    return v

def fact_key(f,doc,mapping,core=False):
    def anchor(e):return mapping.get(e,'UNMATCHED:'+e)
    # Local alternative/scope labels do not themselves carry semantic identity.
    group=f.get('alternative_group')
    alt=tuple(sorted(x['predicate'] for x in doc.get('facts',[]) if group and x.get('alternative_group')==group)) if group else ()
    scope=f.get('event_scope','caption')
    if scope!='caption':scope=tuple(sorted(s['sentence_id'] for s in f['source_spans']))
    key=[f['type'],anchor(f['subject']),REGISTRY['predicate_aliases'].get(f['predicate'],f['predicate']),f.get('assertion'),f.get('polarity','positive'),scope,alt]
    if not core:
        key += [anchor(f['object']) if 'object' in f else None,f.get('object_role'),val(f.get('value')),f.get('comparator'),f.get('unit')]
        event=next((x for x in doc.get('facts',[]) if x['id']==f.get('event_ref')),None)
        key.append(fact_key(event,doc,mapping,core=True) if event else None)
    return tuple(key)

def prf(tp,fp,fn):
    p=tp/(tp+fp) if tp+fp else None;r=tp/(tp+fn) if tp+fn else None
    return {'tp':tp,'fp':fp,'fn':fn,'precision':p,'recall':r,'f1':2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None}

def compare(pred,gold):
    mapping,amb=align_entities(pred,gold);identity={e['id']:e['id'] for e in gold.get('entities',[])}
    per={};details={}
    for t in TYPES:
        pc=Counter(fact_key(f,pred,mapping) for f in pred.get('facts',[]) if f['type']==t)
        gc=Counter(fact_key(f,gold,identity) for f in gold.get('facts',[]) if f['type']==t)
        tp=sum((pc&gc).values());fp=sum((pc-gc).values());fn=sum((gc-pc).values());per[t]=prf(tp,fp,fn)
        details[t]={'extra':[repr(k) for k in (pc-gc).elements()],'missing':[repr(k) for k in (gc-pc).elements()]}
    total=prf(*(sum(x[k] for x in per.values()) for k in ['tp','fp','fn']))
    pe=[e for e in pred.get('entities',[]) if e['kind']!='context'];ge=[e for e in gold.get('entities',[]) if e['kind']!='context'];emt=sum(e['id'] in mapping for e in pe)
    roles_p=[f for f in pred.get('facts',[]) if f['type']=='action' and 'object' in f];roles_g=[f for f in gold.get('facts',[]) if f['type']=='action' and 'object' in f]
    rp=Counter(fact_key(f,pred,mapping) for f in roles_p);rg=Counter(fact_key(f,gold,identity) for f in roles_g)
    return {'overall':total,'by_type':per,'entity_alignment':prf(emt,len(pe)-emt,len(ge)-emt),'ambiguous_alignment':amb,'action_roles':prf(sum((rp&rg).values()),sum((rp-rg).values()),sum((rg-rp).values())),'mapping':mapping,'details':details}

def projected(doc,reference):
    mapping,_=align_entities(doc,reference)
    return Counter(fact_key(f,doc,mapping) for f in doc.get('facts',[]))

def change_score(base_pred,changed_pred,base_gold,changed_gold):
    bp=projected(base_pred,base_gold);cp=projected(changed_pred,base_gold)
    bg=projected(base_gold,base_gold);cg=projected(changed_gold,base_gold)
    expected=Counter({('removed',k):v for k,v in (bg-cg).items()})+Counter({('added',k):v for k,v in (cg-bg).items()})
    observed=Counter({('removed',k):v for k,v in (bp-cp).items()})+Counter({('added',k):v for k,v in (cp-bp).items()})
    return {**prf(sum((expected&observed).values()),sum((observed-expected).values()),sum((expected-observed).values())),'expected_delta':[repr(k) for k in expected.elements()],'observed_delta':[repr(k) for k in observed.elements()]}
