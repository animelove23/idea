"""One image call, inspectable evidence fields, code-owned decision boundaries."""
import copy,json
from pathlib import Path
from analysis_skeleton.common import read_jsonl,sha
from analysis_skeleton.m5_verify import VisualStage

ROOT=Path(__file__).parent
LIMITATIONS={'none','blur','occlusion','ambiguous_identity','category_boundary','nonvisual_claim','grayscale','missing_scale'}

def validate_evidence(raw,claim_type):
    if not isinstance(raw,dict):raise ValueError('evidence_object_required')
    if not {'claim_type','candidate_status','region_status','bbox','observed_category','scope','visible_cues','limitation','attribute_status'}<=raw.keys():raise ValueError('missing_evidence_fields')
    if 'label' in raw:raise ValueError('model_must_not_choose_final_label')
    if raw.get('claim_type')!=claim_type or claim_type not in ('entity','attribute'):raise ValueError('claim_type_mismatch')
    state=raw.get('candidate_status');region=raw.get('region_status');lim=raw.get('limitation');prop=raw.get('attribute_status')
    if not isinstance(state,str) or state not in {'matches','alternative','not_found','unresolved'}:raise ValueError('invalid_candidate_status')
    if not isinstance(region,str) or region not in {'inspectable','limited'}:raise ValueError('invalid_region_status')
    if not isinstance(lim,str) or lim not in LIMITATIONS:raise ValueError('invalid_limitation')
    if not isinstance(prop,str) or prop not in {'supported','contradicted','unresolved','not_applicable'}:raise ValueError('invalid_attribute_status')
    for key in ('observed_category','scope','visible_cues'):
        if not isinstance(raw.get(key),str) or not raw[key].strip():raise ValueError('missing_'+key)
    box=raw.get('bbox')
    if box is not None:
        if not isinstance(box,list) or len(box)!=4 or any(type(x) is not int or not 0<=x<=1000 for x in box):raise ValueError('invalid_bbox')
        if box[0]>=box[2] or box[1]>=box[3]:raise ValueError('empty_bbox')
    if state in ('matches','alternative') and box is None:raise ValueError('identified_candidate_requires_bbox')
    if state=='not_found' and box is not None:raise ValueError('absent_candidate_must_not_have_bbox')
    if state=='unresolved' and lim=='none':raise ValueError('unresolved_requires_limitation')
    if claim_type=='entity' and prop!='not_applicable':raise ValueError('entity_must_not_have_attribute_verdict')
    if claim_type=='attribute' and prop=='not_applicable':raise ValueError('attribute_verdict_required')
    decisive=region=='inspectable' and lim=='none'
    if decisive and state in ('alternative','not_found'):label='hallucinated';rule='visible_alternative_or_inspected_absence'
    elif decisive and state=='matches':
        if claim_type=='entity' or prop=='supported':label='supported';rule='identified_referent_and_supported_proposition'
        elif prop=='contradicted':label='hallucinated';rule='identified_referent_and_visible_attribute_contradiction'
        else:label='uncertain';rule='attribute_unresolved'
    else:label='uncertain';rule='referent_or_evidence_unresolved'
    return {'label':label,'reason':raw['visible_cues'],'evidence':copy.deepcopy(raw),'decision_rule':rule,
            'evidence_source':'model_observation_not_independently_grounded','bbox_verified':False,
            'attribute_support_blocked_by_referent':claim_type=='attribute' and prop=='supported' and label!='supported'}

def make_evidence_shots(original):
    annotations={
    'v1':dict(candidate_status='matches',region_status='inspectable',bbox=[60,500,935,830],observed_category='horses',scope='horses in the foreground field',visible_cues='Several four-legged animals with elongated equine heads, manes and tails are visible.',limitation='none',attribute_status='not_applicable'),
    'v2':dict(candidate_status='alternative',region_status='inspectable',bbox=[15,15,995,980],observed_category='cat',scope='the animal filling the image',visible_cues='The visible animal has a feline face, triangular ears and cat paws; it is not a dog.',limitation='none',attribute_status='not_applicable'),
    'v3':dict(candidate_status='unresolved',region_status='limited',bbox=[420,240,830,730],observed_category='small vegetable pieces',scope='small pieces in the stew',visible_cues='Orange pieces are visible in sauce, but their shape and surface do not resolve the ingredient category.',limitation='category_boundary',attribute_status='not_applicable'),
    'v4':dict(candidate_status='matches',region_status='inspectable',bbox=[155,595,340,770],observed_category='pillow',scope='the pillow near the left side of the bed',visible_cues='The pillow has a visible blue fabric area around its printed pattern.',limitation='none',attribute_status='supported'),
    'v5':dict(candidate_status='matches',region_status='inspectable',bbox=[30,20,985,950],observed_category='bowl',scope='the bowl holding the meal',visible_cues='The visible rim and sides of the bowl are light-colored rather than black.',limitation='none',attribute_status='contradicted'),
    'v6':dict(candidate_status='matches',region_status='inspectable',bbox=[395,745,610,995],observed_category='tie',scope='the tie below the shirt collar',visible_cues='A striped tie is visible, but the photograph is grayscale and does not establish its actual hue.',limitation='grayscale',attribute_status='unresolved')}
    result=copy.deepcopy(original)
    for row in result:
        expected=row['output']['label'];raw={'claim_type':row['semantic_type'],**annotations[row['example_id']]}
        assert validate_evidence(raw,row['semantic_type'])['label']==expected
        row['output']=raw
    return result

class EvidenceStage(VisualStage):
    def __init__(self,shots_path,config_path='decomposition/api_config.local.json',transport=None):
        super().__init__(config_path,transport=transport)
        self.rules_path=ROOT/'prompt.txt';self.rules=self.rules_path.read_text(encoding='utf-8')
        rows=read_jsonl(shots_path)
        if rows!=make_evidence_shots(self.shots):raise ValueError('only_predeclared_evidence_demonstrations_allowed')
        self.shots=rows;self.shots_path=shots_path
        self.identity={**self.identity,'prompt_sha':sha(self.rules_path),'shots_sha':sha(shots_path),'evidence_contract':'evidence_verifier_v1','decision_code_sha':sha(__file__)}
    def user(self,payload):
        message=super().user(payload)
        text=json.loads(message['content'][0]['text']);text['claim_type']=payload['claim_type']
        message['content'][0]['text']=json.dumps(text,ensure_ascii=False)
        return message
    def messages(self,payload):
        messages=[{'role':'system','content':self.rules}]
        for row in self.shots:
            messages += [self.user({**row['input'],'claim_type':row['semantic_type']}),{'role':'assistant','content':json.dumps(row['output'],ensure_ascii=False)}]
        return messages+[self.user(payload)]
