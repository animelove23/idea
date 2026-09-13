"""Strict v5 validation. Repair only unique sentence-scoped case mismatches."""
import copy
import json
import re
from pathlib import Path
from decomposition.source_document import source_sentences

REGISTRY = json.loads(Path(__file__).with_name('registry.json').read_text(encoding='utf-8'))
TYPES = ('object','attribute','action','relation','count')

class ProtocolError(ValueError):
    pass

def need(ok, path, message):
    if not ok: raise ProtocolError(f'{path}: {message}')

def sentences(text):
    cursor=0; result=[]
    for s in source_sentences(text):
        start=text.index(s['text'],cursor); cursor=start+len(s['text'])
        result.append({**s,'start':start,'end':cursor})
    return result

def spans(items, text, path, repairs):
    need(isinstance(items,list) and bool(items),path,'nonempty spans required')
    sm={s['sentence_id']:s for s in sentences(text)}; out=[]
    for i,item in enumerate(items):
        at=f'{path}[{i}]';need(isinstance(item,dict),at,'span object required')
        need(set(item)<= {'sentence_id','quote','occurrence','start','end'},at,'unexpected span fields')
        sid=item.get('sentence_id'); q=item.get('quote')
        need(sid in sm and isinstance(q,str) and bool(q),at,'known sentence_id and nonempty quote required')
        s=sm[sid]
        # A quoted word must not accidentally resolve inside another word (it/suitcase).
        pattern=(r'(?<!\w)' if q[0].isalnum() or q[0]=='_' else '')+re.escape(q)+(r'(?!\w)' if q[-1].isalnum() or q[-1]=='_' else '')
        matches=list(re.finditer(pattern,s['text']))
        if not matches:
            matches=list(re.finditer(pattern,s['text'],re.IGNORECASE))
            need(len(matches)==1,at,f'quote={q!r} has no unique case-insensitive match in {sid}: {s["text"]!r}')
            fixed=s['text'][matches[0].start():matches[0].end()]
            repairs.append({'path':at+'.quote','old':q,'new':fixed,'rule':'unique_sentence_case_match'})
            q=fixed
        occ=item.get('occurrence',0)
        need(len(matches)==1 or 'occurrence' in item,at,'multiple exact occurrences; supply occurrence index, do not guess')
        need(type(occ) is int and 0<=occ<len(matches),at,'occurrence index invalid')
        m=matches[occ]; out.append({'sentence_id':sid,'quote':q,'start':s['start']+m.start(),'end':s['start']+m.end()})
    return out

def records(items,text,path,repairs):
    need(isinstance(items,list),path,'list required')
    result=[]
    for i,x in enumerate(items):
        need(isinstance(x,dict) and isinstance(x.get('reason'),str) and bool(x['reason']),f'{path}[{i}]','reason required')
        need(set(x)<= {'reason','source_spans','candidates','entity_ids'},f'{path}[{i}]','unsupported fields')
        result.append({**x,'source_spans':spans(x.get('source_spans'),text,f'{path}[{i}].source_spans',repairs)})
    return result

def validate_entities(payload,text):
    p=copy.deepcopy(payload); repairs=[]
    need(isinstance(p,dict) and set(p)=={'entities','unresolved','excluded'},'stage_a','exactly entities/unresolved/excluded required')
    need(isinstance(p['entities'],list),'entities','list required')
    ids=set()
    for i,e in enumerate(p['entities']):
        path=f'entities[{i}]'
        need(isinstance(e,dict) and {'id','canonical','kind','mentions'}<=set(e),path,'id/canonical/kind/mentions required')
        need(set(e)<= {'id','canonical','kind','mentions','group_parent','group_link','partition_id'},path,'unexpected fields')
        need(isinstance(e['id'],str) and re.fullmatch('e[1-9][0-9]*',e['id']) and e['id'] not in ids,path+'.id','unique local e ID required')
        ids.add(e['id'])
        need(isinstance(e['canonical'],str) and re.fullmatch('[a-z][a-z0-9_]*',e['canonical']),path+'.canonical','snake_case category required')
        e['canonical']=REGISTRY['canonical_aliases'].get(e['canonical'],e['canonical'])
        need(e['kind'] in {'single','group','part'},path+'.kind','single/group/part; ctx_image is program-provided')
        e['mentions']=spans(e['mentions'],text,path+'.mentions',repairs)
        for key in ('group_parent','group_link','partition_id'): e.setdefault(key,None)
        need(e['partition_id'] is None or isinstance(e['partition_id'],str),path+'.partition_id','string or null required')
    em={e['id']:e for e in p['entities']}
    for i,e in enumerate(p['entities']):
        path=f'entities[{i}]'
        parent=e['group_parent']
        need((parent is None)==(e['group_link'] is None),path+'.group_parent','parent/link must both be null or present')
        if parent is not None:
            need(parent in ids and parent!=e['id'] and em[parent]['kind']=='group',path+'.group_parent','group_parent must reference another group')
            need(e['group_link'] in {'subset_of','member_of'},path+'.group_link','invalid group_link')
            seen={e['id']}; cursor=parent
            while cursor:
                need(cursor in em and cursor not in seen,path+'.group_parent','unknown ancestor or group cycle');seen.add(cursor);cursor=em[cursor]['group_parent']
    # Stable local IDs from first verified source location, never infer identity.
    p['entities'].sort(key=lambda e:(min(s['start'] for s in e['mentions']),e['id']))
    remap={e['id']:f'e{i}' for i,e in enumerate(p['entities'],1)}
    for e in p['entities']:
        e['id']=remap[e['id']]
        if e['group_parent']:e['group_parent']=remap[e['group_parent']]
    for name in ('unresolved','excluded'):
        p[name]=records(p[name],text,name,repairs)
        for x in p[name]:
            if 'entity_ids' in x:
                need(all(e in remap for e in x['entity_ids']),name,'unknown entity reference')
                x['entity_ids']=[remap[e] for e in x['entity_ids']]
    p['entities'].append({'id':'ctx_image','canonical':'image','kind':'context','mentions':[], 'group_parent':None,'group_link':None,'partition_id':None})
    return p,repairs

def validate_facts(payload,entity_table,text):
    p=copy.deepcopy(payload); repairs=[]
    need(isinstance(p,dict) and set(p)=={'facts','unresolved','excluded'},'stage_b','exactly facts/unresolved/excluded required')
    need(isinstance(p['facts'],list),'facts','list required')
    ids={e['id'] for e in entity_table}; fids=set(); unknown=[]
    common={'id','type','subject','predicate','assertion','polarity','source_spans'}
    for i,f in enumerate(p['facts']):
        path=f'facts[{i}]'
        need(isinstance(f,dict) and common<=set(f),path,'missing common fields')
        need(isinstance(f['id'],str) and re.fullmatch('f[1-9][0-9]*',f['id']) and f['id'] not in fids,path+'.id','unique f ID required');fids.add(f['id'])
        t=f['type'];need(t in TYPES,path+'.type','invalid fact type')
        shape={'object':set(),'attribute':{'value'},'action':{'object','object_role'},'relation':{'object','event_ref'},'count':{'value','comparator','unit'}}[t]
        need(set(f)<=common|shape|{'event_scope','alternative_group'},path,'unexpected fields for type')
        need(f['subject'] in ids,path+'.subject','must reference frozen entity table')
        need(isinstance(f['predicate'],str) and re.fullmatch('[a-z][a-z0-9_]*',f['predicate']),path+'.predicate','snake_case required')
        f['predicate']=REGISTRY['predicate_aliases'].get(f['predicate'],f['predicate'])
        need(f['assertion'] in {'asserted','speculative'},path+'.assertion','invalid assertion')
        need(f['polarity'] in {'positive','negative'},path+'.polarity','positive/negative required')
        if t=='object':need(f['predicate']=='exists' and f['subject']!='ctx_image',path,'object must be exists of non-context')
        if t in {'attribute','count'}:
            v=f.get('value');need((isinstance(v,str) and bool(v)) or type(v) is int,path+'.value','nonempty string or integer required')
        if t=='count':
            need(f['predicate']=='count' and f.get('comparator') in REGISTRY['comparators'] and f.get('unit') in REGISTRY['units'],path,'count/comparator/unit required')
            need((f['comparator']=='lexical' and isinstance(f['value'],str)) or (f['comparator']!='lexical' and type(f['value']) is int and f['value']>=0),path,'lexical string vs numeric comparator mismatch')
        if t=='relation':need('object' in f,path,'relation object required')
        if 'object' in f:need(f['object'] in ids,path+'.object','must reference frozen entity table')
        if t=='action':
            need(('object' in f)==('object_role' in f),path,'action object and object_role required together')
            if 'object' in f:need(f['object_role'] in REGISTRY['object_roles'],path+'.object_role','invalid role')
            need(f['predicate'] not in {'holds','wears'},path,'holds/wears are relations')
        f['source_spans']=spans(f['source_spans'],text,path+'.source_spans',repairs)
        f.setdefault('event_scope','caption');f.setdefault('alternative_group',None)
        need(isinstance(f['event_scope'],str) and bool(f['event_scope']),path,'event_scope string required')
        need(f['alternative_group'] is None or isinstance(f['alternative_group'],str),path,'alternative_group string or null required')
        f['verification']='pending';f['source']=' … '.join(s['quote'] for s in f['source_spans'])
        if f['predicate'] not in REGISTRY[t]:unknown.append({'fact_id':f['id'],'type':t,'predicate':f['predicate'],'reason':'unknown_predicate'})
    actions={f['id'] for f in p['facts'] if f['type']=='action'}
    for i,f in enumerate(p['facts']):
        if 'event_ref' in f:need(f['event_ref'] in actions,f'facts[{i}].event_ref','must reference an action in this caption')
    for key in ('unresolved','excluded'):p[key]=records(p[key],text,key,repairs)
    p['registry_queue']=unknown
    return p,repairs

def model_entities(entities):
    return [{**e,'mentions':[{k:v for k,v in s.items() if k not in {'start','end'}} for s in e['mentions']]} for e in entities]

def model_facts(facts):
    return [{k:([{a:b for a,b in s.items() if a not in {'start','end'}} for s in v] if k=='source_spans' else v) for k,v in f.items() if k not in {'verification','source'}} for f in facts]
