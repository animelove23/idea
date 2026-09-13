"""One identity decision; deterministic entity events, unchanged downstream schema."""
import copy
from collections import Counter
from pathlib import Path
from analysis_skeleton.common import digest,sha,read_jsonl
from analysis_skeleton.llm import FewShotStage
from analysis_skeleton.framework_v2.contracts import validate_alignment as structural
from experiments.coco400_revision_v2.alignment import validate as validate_internal,CHANGES

ROOT=Path(__file__).parent
SIDES=('original','steer')

def validate(raw,original,steer):
    if not isinstance(raw,dict) or set(raw)!={'entities','attributes'} or any(not isinstance(raw[k],list) for k in raw):
        raise ValueError('entities_and_attributes_arrays_only')
    clean=copy.deepcopy(raw);audit=[]
    for row in clean['entities']:
        if not isinstance(row,dict):continue
        change=row.get('description_change');status=row.get('status')
        bad=not isinstance(change,str) or change not in CHANGES or (status=='matched' and change not in {'equivalent','generalized','specialized'}) or (isinstance(status,str) and status in {'original_only','steer_only'} and change!='absent')
        if bad:
            audit.append({'stage':'entity','raw':copy.deepcopy(row),'reason':'description_contract_invalid'})
            row['status']='invalid_description_contract'
    # Reuse strict ID/shape/connected-conflict checks; no guessed correspondence.
    checked=structural({'entities':clean['entities'],'alignments':[]},original,steer)
    entities=checked['entities'];derived=[]
    facts={s:{f['id']:f for f in d['facts']} for s,d in zip(SIDES,(original,steer))}
    for row in entities:
        row.setdefault('description_change','unresolved')
        status=row['status']
        event={s:['entity_'+eid for eid in row[s]] for s in SIDES}
        event['reason']=row.get('reason','explicit_entity_mapping')
        if status=='matched':event['status']='retained' if row['description_change']=='equivalent' else 'description_changed'
        elif status=='original_only':event['status']='removed'
        elif status=='steer_only':event['status']='added'
        else:event['status']='unresolved'
        if 'opposite_evidence' in row:event['opposite_evidence']=copy.deepcopy(row['opposite_evidence'])
        derived.append(event)
    attrs=[]
    for row in clean['attributes']:
        well=isinstance(row,dict) and isinstance(row.get('status'),str) and row['status'] in {'retained','modified','removed','added','unresolved'} and all(isinstance(row.get(s),list) and all(isinstance(v,str) for v in row[s]) for s in SIDES)
        valid=well and all(fid in facts[s] and facts[s][fid]['type']=='attribute' for s in SIDES for fid in row[s])
        if valid:attrs.append(row);continue
        audit.append({'stage':'attribute','raw':copy.deepcopy(row),'reason':'attribute_schema_or_reference_invalid'})
        # Poison only affected attribute references, never the derived entity table.
        if isinstance(row,dict):
            for side in SIDES:
                for fid in row.get(side,[]) if isinstance(row.get(side),list) else []:
                    if isinstance(fid,str) and fid in facts[side] and facts[side][fid]['type']=='attribute':
                        attrs.append({'original':[fid] if side=='original' else [],'steer':[fid] if side=='steer' else [],'status':'invalid_attribute_row','reason':'technical_attribute_schema_invalid'})
    result=validate_internal({'entities':entities,'alignments':derived+attrs},original,steer)
    result['issues']=checked['issues']+audit+result['issues']
    result['derivation_audit']={'entity_events':copy.deepcopy(derived),'model_entity_fact_decisions':0,'missing_rows_are_technical':True,'input_contract':'entities_attributes_v3'}
    if result['issues']:result['status']='needs_review'
    for side in SIDES:
        count=Counter(fid for row in result['alignments'] for fid in row[side])
        if set(count)!=set(facts[side]) or any(n!=1 for n in count.values()):raise ValueError('fact_coverage_not_exactly_once')
    return result

def project_v2(raw,original,steer):
    """Counterfactual format replay only; cannot measure the new model's accuracy."""
    facts={s:{f['id']:f for f in d['facts']} for s,d in zip(SIDES,(original,steer))}
    attrs=[];dropped=[]
    for row in raw.get('alignments',[]):
        refs=[facts[s].get(fid) for s in SIDES for fid in row.get(s,[]) if isinstance(fid,str)] if isinstance(row,dict) else []
        if refs and all(f is not None and f['type']=='entity' for f in refs):dropped.append(row)
        else:attrs.append(row)
    return {'entities':copy.deepcopy(raw.get('entities',[])),'attributes':copy.deepcopy(attrs)},dropped

class SimplifiedAlignStage(FewShotStage):
    def __init__(self,config_path='decomposition/api_config.local.json',transport=None):
        super().__init__('align',config_path,transport,model='deepseek-flash')
        self.rules=(ROOT/'m3_rules.txt').read_text(encoding='utf-8');self.shots=read_jsonl(ROOT/'m3_shots.jsonl')
        if len(self.shots)!=8:raise ValueError('eight_shots_required')
        self.identity.update(condition='single_entity_decision_v3',prompt_sha=digest(self.rules),shots_sha=digest(self.shots),candidate_code_sha=sha(__file__))
