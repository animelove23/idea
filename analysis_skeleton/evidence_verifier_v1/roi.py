"""Bounded, model-proposed ROI follow-up; select without reference labels."""
import copy,json,math,random
from pathlib import Path
from PIL import Image
from analysis_skeleton.common import read_json,read_jsonl,write_json,write_jsonl,sha,digest,new_run,check_frozen
from analysis_skeleton.framework_v2.runtime import SafeStage,Checkpoints
from .stage import EvidenceStage
from .compiler import compile_evidence

POLICY={'eligible':'entity label uncertain with predicted bbox area <=0.15 and a visual limitation','max_area_fraction':0.15,'limitations':['blur','occlusion','ambiguous_identity','category_boundary'],'padding_each_side':0.25,'max_extra_production_calls':1,'views':'full original plus one original-pixel crop','no_gold_or_handpicked_coordinates':True,'experimental_controls':'one fresh full-image repeat and one fresh ROI request per eligible case'}

def eligible(row):
    p=row.get('prediction',{});e=p.get('evidence',{});b=e.get('bbox')
    return row['semantic_type']=='entity' and p.get('label')=='uncertain' and isinstance(b,list) and len(b)==4 and e.get('limitation') in POLICY['limitations'] and 0<(b[2]-b[0])*(b[3]-b[1])/1e6<=POLICY['max_area_fraction']

def create_crop(payload,bbox,path):
    if sha(payload['image_path'])!=payload['image_sha256']:raise ValueError('source_changed')
    with Image.open(payload['image_path']) as im:
        im=im.convert('RGB');w,h=im.size
        l,t,r,b=[bbox[0]*w/1000,bbox[1]*h/1000,bbox[2]*w/1000,bbox[3]*h/1000]
        px=(r-l)*POLICY['padding_each_side'];py=(b-t)*POLICY['padding_each_side']
        box=[max(0,math.floor(l-px)),max(0,math.floor(t-py)),min(w,math.ceil(r+px)),min(h,math.ceil(b+py))]
        if box[0]>=box[2] or box[1]>=box[3]:raise ValueError('empty_roi')
        im.crop(box).save(path,format='PNG')
    return {'image_path':str(Path(path).resolve()),'image_sha256':sha(path),'pixel_box':box,'source_size':[w,h],'source_sha256':payload['image_sha256']}

class ROIStage(EvidenceStage):
    def __init__(self,shots_path,manifest_hash,**kwargs):
        super().__init__(shots_path,**kwargs);self.identity={**self.identity,'roi_policy':POLICY,'roi_manifest':manifest_hash}
    def messages(self,payload):
        messages=super().messages(payload);crop=payload['roi_view']
        if crop['source_sha256']!=payload['image_sha256']:raise ValueError('roi_source_mismatch')
        with Image.open(payload['image_path']) as original,Image.open(crop['image_path']) as local:
            expected=original.convert('RGB').crop(crop['pixel_box'])
            if expected.size!=local.size or expected.tobytes()!=local.convert('RGB').tobytes():raise ValueError('roi_pixels_changed')
        messages[-1]['content'] += [{'type':'text','text':json.dumps({'additional_view_of_same_image':crop['pixel_box'],'full_image_size':crop['source_size']})},{'type':'image_url','image_url':{'url':self._image(crop),'detail':'original'}}]
        return messages

def prepare(root):
    root=Path(root);source=read_jsonl(root/'run/results.jsonl');inputs={r['case_id']:r for r in read_jsonl(root/'inputs.jsonl')}
    records=[]
    for row in source:
        if row['condition']!='evidence' or not eligible(row):continue
        record=copy.deepcopy(inputs[row['case_id']]);record['input']['claim_type']='entity'
        directory=root/'roi_views';directory.mkdir(exist_ok=True)
        record['input']['roi_view']=create_crop(record['input'],row['prediction']['evidence']['bbox'],directory/(row['case_id']+'.png'))
        record['source_response_id']=row['audit']['response_id'];record['source_evidence']=row['prediction']['evidence'];records.append(record)
    if (root/'roi_cases.jsonl').exists():raise ValueError('roi_already_prepared')
    write_jsonl(root/'roi_cases.jsonl',records);write_json(root/'roi_policy.json',POLICY)
    order=[(r['case_id'],c) for r in records for c in ('full_repeat','roi')];random.Random(20260917).shuffle(order);write_json(root/'roi_order.json',order)
    print({'eligible_cases':[r['case_id'] for r in records],'planned_extra_calls':len(order)})

def run(root):
    root=Path(root);rows=read_jsonl(root/'roi_cases.jsonl');by_id={r['case_id']:r for r in rows};order=read_json(root/'roi_order.json')
    stages={'full_repeat':SafeStage(EvidenceStage(root/'shots.jsonl')),'roi':SafeStage(ROIStage(root/'shots.jsonl',sha(root/'roi_cases.jsonl')))}
    out=root/'roi_run';files=[root/'roi_cases.jsonl',root/'roi_policy.json',root/'roi_order.json',root/'shots.jsonl',root/'run/results.jsonl',Path(__file__).parent/'prompt.txt']
    files += [r['input']['image_path'] for r in rows]+[r['input']['roi_view']['image_path'] for r in rows]+[r['input']['image_path'] for r in stages['full_repeat'].source.shots]
    new_run(out,'model_proposed_roi_followup',files,{'stages':{c:s.identity for c,s in stages.items()},'order':order,'fresh':True,'policy':POLICY},[__file__,Path(__file__).parent/'stage.py',Path(__file__).parent/'compiler.py','analysis_skeleton/framework_v2/runtime.py'])
    cp=Checkpoints(out/'checkpoints',digest(read_json(out/'manifest.json')),cache_mode='fresh');results=[]
    for i,(cid,c) in enumerate(order):
        check_frozen(out);payload=copy.deepcopy(by_id[cid]['input'])
        if c=='full_repeat':payload.pop('roi_view')
        v=cp.call(cid+':'+c,stages[c],payload,lambda raw:compile_evidence(raw,'entity'))
        results.append({'case_id':cid,'condition':c,'status':v['status'],'prediction':v.get('value',{}),'audit':v.get('audit',{})})
        write_jsonl(out/'results.jsonl',results);print(f"{i+1}/{len(order)} {cid} {c}: {v.get('value',{}).get('label',v['status'])}",flush=True)
    write_json(root/'roi_calls.json',{'new_api_calls':cp.new_api_calls,'eligible':len(rows),'requests':len(results)})

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['prepare','run']);p.add_argument('--output',required=True);a=p.parse_args()
    prepare(a.output) if a.phase=='prepare' else run(a.output)
