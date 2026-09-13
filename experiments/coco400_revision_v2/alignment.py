"""Separate referent identity from description specificity; validate with legacy ID safeguards."""
import copy
from pathlib import Path
from analysis_skeleton.common import read_jsonl,sha
from analysis_skeleton.llm import FewShotStage
from analysis_skeleton.framework_v2.contracts import validate_alignment as legacy

ROOT=Path(__file__).parent
CHANGES={'equivalent','generalized','specialized','part_whole','collection_change','unresolved','absent'}


def validate(raw,original,steer):
    r=copy.deepcopy(raw);changes={}
    for e in r['entities']:
        change=e.get('description_change')
        if change not in CHANGES:raise ValueError('explicit_description_change_required')
        if e['status']=='matched' and change not in {'equivalent','generalized','specialized'}:
            raise ValueError('only_same_referent_equivalence_or_specificity_can_match')
        if e['status']=='matched':changes[(e['original'][0],e['steer'][0])]=change
        if e['status'] in {'original_only','steer_only'} and change!='absent':raise ValueError('absence_change_required')
    facts={s:{f['id']:f for f in d['facts']} for s,d in [('original',original),('steer',steer)]}
    transitions=[]
    for edge in r['alignments']:
        if edge['status']=='description_changed':
            if len(edge['original'])!=1 or len(edge['steer'])!=1:raise ValueError('change_requires_one_to_one')
            a,b=facts['original'][edge['original'][0]],facts['steer'][edge['steer'][0]]
            change=changes.get((a['entity_id'],b['entity_id']))
            if a['type']!='entity' or b['type']!='entity' or change not in {'generalized','specialized'}:
                raise ValueError('description_changed_requires_known_same_subject')
            transitions.append((tuple(edge['original']),tuple(edge['steer']),change));edge['status']='retained'
        elif edge['status']=='retained' and len(edge['original'])==len(edge['steer'])==1:
            a,b=facts['original'].get(edge['original'][0],{}),facts['steer'].get(edge['steer'][0],{})
            if a.get('type')=='entity' and changes.get((a.get('entity_id'),b.get('entity_id'))) in {'generalized','specialized'}:
                raise ValueError('specificity_change_must_not_be_retained')
    out=legacy(r,original,steer)
    for edge in out['alignments']:
        for a,b,change in transitions:
            if tuple(edge['original'])==a and tuple(edge['steer'])==b and edge['status']=='retained':
                edge.update(status='modified',description_change=change,reason='description_'+change)
    out['description_transitions']=[{'original':list(a),'steer':list(b),'change':c} for a,b,c in transitions
        if any(e.get('description_change')==c and tuple(e['original'])==a and tuple(e['steer'])==b for e in out['alignments'])]
    return out


class AlignStage(FewShotStage):
    def __init__(self,config='decomposition/api_config.local.json',transport=None):
        super().__init__('align',config,transport,model='deepseek-flash')
        self.rules_path=ROOT/'align.txt';self.shots_path=ROOT/'align_shots.jsonl'
        self.rules=self.rules_path.read_text(encoding='utf-8');self.shots=read_jsonl(self.shots_path)
        assert len(self.shots)==8
        self.identity.update(prompt_sha=sha(self.rules_path),shots_sha=sha(self.shots_path),contract='identity_and_specificity_v2',code_sha=sha(__file__))
