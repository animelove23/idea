"""Two semantic stages; local auditable repair; bounded field-patch repair."""
import copy
import json
import re
import time
from pathlib import Path
from urllib.error import HTTPError
from decomposition.semantic_decomposer import DeepSeekDecomposer
from .schema import REGISTRY, ProtocolError, sentences, validate_entities, validate_facts, model_entities, model_facts

ROOT=Path(__file__).parent

def prompts(shots=8):
    if shots not in (0,8):raise ValueError('shots must be 0 or 8')
    rules=(ROOT/'rules.txt').read_text(encoding='utf-8')+'\nREGISTRY:\n'+json.dumps(REGISTRY,ensure_ascii=False)
    stages={
      'entities':rules+'\nSTAGE A ONLY. Return {entities:[{id,canonical,kind,mentions:[{sentence_id,quote,occurrence?}],group_parent:null or ID,group_link:null/member_of/subset_of,partition_id:null or string}], unresolved:[{reason,source_spans:[{sentence_id,quote}]}], excluded:[{reason,source_spans:[{sentence_id,quote}]}]}. No facts. kind is single/group/part; context ctx_image is supplied later by program.',
      'facts':rules+'\nSTAGE B ONLY. Return {facts:[{id,type,subject,predicate,assertion,polarity,source_spans:[{sentence_id,quote}], ...type-specific fields...}], unresolved:[{reason,source_spans:[{sentence_id,quote}]}], excluded:[{reason,source_spans:[{sentence_id,quote}]}]}. Use only frozen entity IDs including ctx_image. Do not return entities or verification/source display fields.'}
    if shots:
        examples=[json.loads(x) for x in (ROOT/'shots.jsonl').read_text(encoding='utf-8').splitlines()]
        if len(examples)!=8:raise ValueError('exactly 8 frozen demonstrations required')
        for i,d in enumerate(examples,1):
            inp={'id':'caption','text':d['text'],'sentences':sentences(d['text'])}
            a={'entities':model_entities([e for e in d['entities'] if e['id']!='ctx_image']),'unresolved':d['unresolved'],'excluded':d['excluded']}
            b={'facts':model_facts(d['facts']),'unresolved':[],'excluded':[]}
            stages['entities']+=f'\nEXAMPLE {i}\nINPUT:'+json.dumps(inp)+'\nOUTPUT:'+json.dumps(a)
            stages['facts']+=f'\nEXAMPLE {i}\nINPUT:'+json.dumps({**inp,'entities':d['entities']})+'\nOUTPUT:'+json.dumps(b)
    return stages

def apply_patches(payload,patch_response,error):
    if not isinstance(patch_response,dict) or set(patch_response)!={'patches'} or not isinstance(patch_response['patches'],list):raise ProtocolError('repair: patches list required')
    result=copy.deepcopy(payload)
    m=re.match(r'(entities|facts|unresolved|excluded)\[(\d+)\]',str(error))
    prefix=f'/{m[1]}/{m[2]}' if m else None
    for patch in patch_response['patches']:
        if not isinstance(patch,dict) or patch.get('op')!='replace' or set(patch)!={'op','path','value'}:raise ProtocolError('repair: replace-only patches')
        path=patch['path']
        if not isinstance(path,str) or not prefix or not (path==prefix or path.startswith(prefix+'/')):raise ProtocolError('repair: patch outside diagnosed record')
        parts=path.strip('/').split('/'); obj=result
        for part in parts[:-1]:obj=obj[int(part)] if isinstance(obj,list) else obj[part]
        key=int(parts[-1]) if isinstance(obj,list) else parts[-1]
        if isinstance(obj,dict) and key not in obj:raise ProtocolError('repair: cannot add unrelated field')
        obj[key]=patch['value']
    return result

def normalize(facts):
    seen={}; kept=[]; changes=[]; aliases={}
    for f in facts:
        key=json.dumps({k:v for k,v in f.items() if k not in {'id','source','source_spans','verification'}},sort_keys=True)
        if key in seen:
            aliases[f['id']]=seen[key];changes.append({'rule':'exact_same_scope_fact','removed':f['id'],'kept':seen[key]})
        else:seen[key]=f['id'];kept.append(copy.deepcopy(f))
    remap={f['id']:f'f{i}' for i,f in enumerate(kept,1)}
    for f in kept:
        f['id']=remap[f['id']]
        if 'event_ref' in f:f['event_ref']=remap[aliases.get(f['event_ref'],f['event_ref'])]
    return kept,changes

def warnings(text,entities,facts):
    out=[]; sm=sentences(text)
    em={e['id']:e for e in entities}
    number_words={'two':2,'three':3,'four':4,'five':5,'six':6}
    # Recall alarms only. No facts are created from lexical triggers.
    for s in sm:
        sf=[f for f in facts if any(q['sentence_id']==s['sentence_id'] for q in f['source_spans'])]
        cs=[f for f in sf if f['type']=='count']
        for token in set(re.findall(r'\b(?:two|three|four|five|six|several|multiple|few|pairs|piles)\b',s['text'],re.I)):
            low=token.lower()
            if low in {'pairs','piles'}:covered=any(f.get('unit')==low[:-1] for f in cs)
            elif low in number_words:covered=any(f.get('value')==number_words[low] for f in cs)
            else:covered=any(low in str(f.get('value','')).lower().split() for f in cs)
            if not covered:out.append({'rule':'quantity_coverage','sentence_id':s['sentence_id'],'trigger':token})
        regions=set(re.findall(r'\b(left|right|center|middle|back|front|edge)\b',s['text'],re.I))
        for region in regions:
            alternatives={'middle':{'middle','center'},'center':{'middle','center'}}.get(region.lower(),{region.lower()})
            if not any(f['type']=='relation' and any(x in f['predicate'].split('_') for x in alternatives) for f in sf):
                out.append({'rule':'spatial_region_coverage','sentence_id':s['sentence_id'],'region':region})
        if all(re.search(r'\b'+word+r'\b',s['text'],re.I) for word in ['hands','feet','crossed']):
            subjects={em[f['subject']]['canonical'] for f in sf if f['type']=='attribute' and 'crossed' in str(f.get('value',''))}
            if not {'hand','foot'}<=subjects:out.append({'rule':'independent_body_postures','sentence_id':s['sentence_id']})
    for e in entities:
        if e['kind']=='part' and not e['group_parent'] and not any(f['type']=='object' and f['subject']==e['id'] for f in facts):out.append({'rule':'body_part_existence','entity':e['id']})
        if not e.get('group_parent') and any(re.match(r'(some\b|others\b|one of them\b|the other\b)',q['quote'],re.I) for q in e['mentions']):out.append({'rule':'unlinked_subgroup_candidate','entity':e['id']})
        if e['canonical'] in {'smile','bun','ingredient','activity','work'} and any(f['type']=='object' and f['subject']==e['id'] for f in facts):out.append({'rule':'object_scope_review','entity':e['id']})
    for f in facts:
        if f['predicate'] in {'toward','belongs_to','full_of'}:out.append({'rule':'boundary_review','fact_id':f['id']})
        if f['predicate']=='sit' and next(e for e in entities if e['id']==f['subject'])['canonical'] in {'bowl','shoe','vase','plate'}:out.append({'rule':'static_sit','fact_id':f['id']})
        if f['type']=='attribute' and re.search(r'\b(left|right|center|back)\b',str(f.get('value',''))):out.append({'rule':'spatial_reference_review','fact_id':f['id']})
        source=' '.join(q['quote'] for q in f['source_spans'])
        if f['assertion']=='asserted' and re.search(r'\b(appears?|seems?|might|possibly|likely|inferred)\b',source,re.I):out.append({'rule':'modality_scope_review','fact_id':f['id']})
        if re.search(r'\b(busy|comfortable|delicious|refreshing|appetizing|appealing|elegance|enjoying)\b',str(f.get('value',''))+' '+f['predicate'].replace('_',' '),re.I):out.append({'rule':'appraisal_scope_review','fact_id':f['id']})
        if f['type']=='action' and f['predicate'] in {'pick_up','catch','serve','throw'} and re.search(r'\b(prepar\w*|try\w*|ready)\b',source,re.I):out.append({'rule':'action_phase_review','fact_id':f['id']})
        if f['type']=='action' and f.get('object')==f['subject'] and f['predicate'] in {'look_at','observe'} and not re.search(r'\b(self|himself|herself|itself|themselves|each other)\b',source,re.I):out.append({'rule':'suspicious_self_target','fact_id':f['id']})
        if f['type'] in {'action','relation'} and re.search(r'\b(work|activities)\b',source,re.I):out.append({'rule':'abstract_activity_scope_review','fact_id':f['id']})
        if f['predicate']=='includes' and re.search(r'\bamong the ingredients\b',source,re.I):out.append({'rule':'whole_part_direction_review','fact_id':f['id']})
    return out

class V5Failure(RuntimeError):
    def __init__(self,message,audit):super().__init__(message);self.audit=audit

class DecomposerV5:
    def __init__(self,config,shots=8,transport=None,frozen_prompts=None):
        self.config=config;self.prompts=frozen_prompts or prompts(shots)
        self.transport=transport or DeepSeekDecomposer(config,prompt='unused')._request

    def _stage(self,stage,inp,validator,audit):
        messages=[{'role':'system','content':self.prompts[stage]},{'role':'user','content':json.dumps(inp,ensure_ascii=False)}]
        raw=None;error=None
        for turn in range(2):
            body={'model':self.config.model,'messages':messages,'response_format':{'type':'json_object'},'thinking':{'type':'disabled'},'temperature':0,'max_tokens':self.config.max_tokens}
            attempt={'stage':stage,'attempt':turn+1,'thinking':'disabled','messages':copy.deepcopy(messages)};t=time.monotonic()
            try:
                response=self.transport(body);c=response['choices'][0]
                attempt.update(model=response.get('model'),usage=response.get('usage'),raw_content=c['message']['content'],finish_reason=c.get('finish_reason'))
                if c.get('finish_reason')!='stop':raise ProtocolError('response: incomplete')
                parsed=json.loads(c['message']['content'])
                candidate=apply_patches(raw,parsed,error) if raw is not None else parsed
                result,repairs=validator(candidate)
                attempt.update(valid=True,local_repairs=repairs,elapsed_seconds=round(time.monotonic()-t,3))
                audit['attempts'].append(attempt)
                audit['stages'][stage]={'raw_valid':turn==0 and not repairs,'repaired':turn>0 or bool(repairs),'local_repairs':repairs,'remote_patch':turn>0 and raw is not None}
                return result
            except Exception as exc:
                attempt.update(valid=False,error=str(exc) if isinstance(exc,(ProtocolError,ValueError,HTTPError)) else type(exc).__name__,elapsed_seconds=round(time.monotonic()-t,3));audit['attempts'].append(attempt)
                if isinstance(exc,HTTPError) and exc.code in {400,401,403,404}:raise V5Failure(attempt['error'],audit) from exc
                if turn==1:raise V5Failure(attempt['error'],audit) from exc
                if isinstance(exc,ProtocolError) and 'parsed' in locals() and raw is None:
                    raw=parsed;error=str(exc)
                    messages=messages+[{'role':'assistant','content':json.dumps(raw)}, {'role':'user','content':'Return ONLY {"patches":[{"op":"replace","path":"/facts/0/...","value":...}]}. Fix only the record identified by this error; no other records, no caption changes. Use exact sentence quotes from input. Error: '+error}]
                time.sleep(1)

    def decompose(self,text):
        audit={'attempts':[],'stages':{},'thinking':'disabled','cache_hit':False}
        inp={'id':'caption','text':text,'sentences':sentences(text)}
        a=self._stage('entities',inp,lambda p:validate_entities(p,text),audit)
        b=self._stage('facts',{**inp,'entities':a['entities']},lambda p:validate_facts(p,a['entities'],text),audit)
        facts,changes=normalize(b['facts'])
        result={'id':'caption','text':text,'entities':a['entities'],'facts':facts,'unresolved':a['unresolved']+b['unresolved'],'excluded':a['excluded']+b['excluded'],'registry_queue':b['registry_queue']}
        result['warnings']=warnings(text,result['entities'],facts)
        audit.update(normalization_log=changes,raw_valid=all(s['raw_valid'] for s in audit['stages'].values()),repaired=any(s['repaired'] for s in audit['stages'].values()))
        return result,audit
