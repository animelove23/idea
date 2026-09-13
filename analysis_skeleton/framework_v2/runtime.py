"""Bounded calls, exact provenance, and resumable checksummed request checkpoints."""
import copy
import json
import time
import traceback
from pathlib import Path
from urllib.error import HTTPError,URLError
from analysis_skeleton.common import digest,read_json,write_json
from analysis_skeleton.llm import CallFailure


def diagnostic(exc):
    # Never serialize exception bodies, headers, locals, or credential-bearing source lines.
    return {'exception_type':type(exc).__name__,
            'frames':[{'file':f.filename,'line':f.lineno,'function':f.name} for f in traceback.extract_tb(exc.__traceback__)]}


def query_payload(stage,payload):
    if stage=='decompose':return {'text':payload['text']}
    if stage=='align':return {s:payload[s] for s in ('original','steer')}
    if stage=='verify':return {k:payload.get(k) for k in ('image_sha256','statement','entity_context')}
    raise ValueError('unknown_stage')


class SafeStage:
    """Reuse frozen messages, identity, and transport, moving input preparation into the boundary."""
    def __init__(self,stage):
        self.source=stage;self.stage=stage.stage;self.identity=stage.identity
    def run(self,payload):
        start=time.monotonic();phase='input'
        audit={'stage':self.stage,'identity':self.identity,'input':copy.deepcopy(payload),'api_calls':0}
        try:
            body={'model':self.source.config.model,'messages':self.source.messages(payload),
                  'response_format':{'type':'json_object'},'temperature':0,
                  'thinking':{'type':'disabled'},'max_tokens':self.source.config.max_tokens}
            phase='transport';audit['api_calls']=1
            response=self.source.transport(body)
            phase='response';choice=response['choices'][0]
            audit.update(response_id=response.get('id'),response_model=response.get('model'),usage=response.get('usage'),
                         raw_content=choice['message'].get('content'),finish_reason=choice.get('finish_reason'))
            if choice.get('finish_reason')!='stop':raise ValueError('incomplete_response')
            raw=json.loads(audit['raw_content'])
            if not isinstance(raw,dict):raise ValueError('json_object_required')
            audit['elapsed_seconds']=time.monotonic()-start
            return raw,audit
        except Exception as exc:
            expected=isinstance(exc,(ValueError,TypeError,KeyError,IndexError,OSError,URLError))
            audit.update(error=f'HTTP {exc.code}' if isinstance(exc,HTTPError) else type(exc).__name__,
                         phase=phase,failure_kind='technical_failure' if expected else 'unexpected_failure',
                         elapsed_seconds=time.monotonic()-start,diagnostic=diagnostic(exc))
            if phase=='transport':audit['remote_outcome']='unknown'
            raise CallFailure(audit) from None


class CacheConflict(ValueError):pass
class CheckpointIntegrityError(ValueError):pass


class ResponseCache:
    """A task key explicitly selects a source response; duplicate selections are rejected."""
    def __init__(self,records=()):
        self.records={}
        for row in records:
            key=row['task_key']
            if key in self.records:raise CacheConflict('duplicate_cache_task_key')
            audit=row['audit']
            if 'error' in audit or not isinstance(audit.get('raw_content'),str):
                raise CacheConflict('cache_requires_successful_raw_response')
            self.records[key]=copy.deepcopy(row)
        self.fingerprint=digest(self.records)
    def get(self,task_key,stage,payload):
        row=self.records.get(task_key)
        if row is None:return None
        a=row['audit']
        if a['identity']!=stage.identity or query_payload(stage.stage,a['input'])!=query_payload(stage.stage,payload):return None
        if a.get('response_model')!=stage.identity.get('model'):return None
        audit=copy.deepcopy(a);audit['source_response_id']=audit.get('response_id')
        audit['reused_usage']=audit.pop('usage',None);audit['reused_elapsed_seconds']=audit.pop('elapsed_seconds',None)
        audit.update(api_calls=0,elapsed_seconds=0,cache_hit=True,cache_source=row.get('source'),input=copy.deepcopy(payload))
        return json.loads(audit['raw_content']),audit


class Checkpoints:
    def __init__(self,path,run_identity,cache=None,cache_mode='fresh'):
        if cache_mode not in ('fresh','replay','reuse'):raise ValueError('invalid_cache_mode')
        self.path=Path(path);self.path.mkdir(parents=True,exist_ok=True)
        self.run_identity=run_identity;self.cache=cache or ResponseCache();self.cache_mode=cache_mode
        self.new_api_calls=0;self.resumed=0
    def file(self,key,suffix=''):
        return self.path/(digest(key)+suffix+'.json')
    def save(self,path,value):write_json(path,{'value':value,'checksum':digest(value)})
    def load(self,path):
        try:
            record=read_json(path)
            if digest(record['value'])!=record['checksum']:raise ValueError('checksum')
            return record['value']
        except (ValueError,KeyError,TypeError) as exc:raise CheckpointIntegrityError('corrupt_checkpoint') from exc
    def call(self,key,stage,payload,validator):
        identity=digest({'run':self.run_identity,'key':key,'stage':stage.stage,'model':stage.identity,'input':payload})
        path=self.file(key)
        if path.exists():
            record=self.load(path)
            if record['identity']!=identity:raise CheckpointIntegrityError('checkpoint_identity_changed')
            if record['status']!='started':self.resumed+=1;return record
            response_path=self.file(key,'_response')
            if response_path.exists():
                saved=self.load(response_path)
                if saved['identity']!=identity:raise CheckpointIntegrityError('response_identity_changed')
                raw,audit=saved['raw'],saved['audit'];self.resumed+=1
            else:
                record.update(status='outcome_unknown',audit={'api_calls':0,'remote_outcome':'unknown'},
                              detail='Started checkpoint has no response; not resent automatically')
                self.save(path,record);return record
        else:
            self.save(path,{'identity':identity,'task_key':key,'status':'started'})
            audit={}
            try:
                hit=self.cache.get(key,stage,payload) if self.cache_mode!='fresh' else None
                if hit:raw,audit=hit
                elif self.cache_mode=='replay':
                    raise CallFailure({'stage':stage.stage,'identity':stage.identity,'input':payload,
                                       'api_calls':0,'error':'cache_miss','phase':'cache'})
                else:raw,audit=stage.run(payload)
                self.new_api_calls+=audit.get('api_calls',0)
                self.save(self.file(key,'_response'),{'identity':identity,'raw':raw,'audit':audit})
            except CallFailure as exc:
                self.new_api_calls+=exc.audit.get('api_calls',0)
                record={'identity':identity,'task_key':key,'status':exc.audit.get('failure_kind','technical_failure'),'audit':exc.audit}
                self.save(path,record);return record
            except Exception as exc:
                record={'identity':identity,'task_key':key,'status':'unexpected_failure','audit':audit,'diagnostic':diagnostic(exc)}
                self.save(path,record);return record
        try:
            value=validator(raw)
            record={'identity':identity,'task_key':key,'status':'complete','value':value,'audit':audit}
        except Exception as exc:
            expected=isinstance(exc,(ValueError,TypeError,KeyError))
            record={'identity':identity,'task_key':key,'status':'technical_failure' if expected else 'unexpected_failure',
                    'audit':audit,'phase':'validation','diagnostic':diagnostic(exc)}
        self.save(path,record)
        return record
