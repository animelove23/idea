"""Original-pixel image views for scientific inference, without semantic selection."""
import copy
import json
from pathlib import Path
from PIL import Image
from analysis_skeleton.common import sha,write_json,read_json,digest
from analysis_skeleton.m5_verify import VisualStage

POLICY={'version':'four_overlap_original_pixels_v1','grid':[2,2],'crop_fraction':[3,5],
        'resize':False,'reconstruction':False,'full_image_retained':True,'order':['top_left','top_right','bottom_left','bottom_right']}

def boxes(width,height):
    if width<2 or height<2:raise ValueError('image_too_small')
    cw=(3*width+4)//5; ch=(3*height+4)//5
    return [(0,0,cw,ch),(width-cw,0,width,ch),(0,height-ch,cw,height),(width-cw,height-ch,width,height)]

def prepare_views(payload,directory):
    path=Path(payload['image_path']); expected=payload['image_sha256']
    if sha(path)!=expected:raise ValueError('source_image_hash_mismatch')
    out=Path(directory)/expected; manifest=out/'views.json'
    if manifest.exists():
        record=read_json(manifest)
        validate_views(payload,record)
        return record
    out.mkdir(parents=True,exist_ok=True)
    with Image.open(path) as im:
        source=im.convert('RGB'); w,h=source.size; views=[]
        for name,box in zip(POLICY['order'],boxes(w,h)):
            target=out/(name+'.png');source.crop(box).save(target,format='PNG')
            views.append({'name':name,'box':list(box),'image_path':str(target.resolve()),'image_sha256':sha(target)})
    record={'policy':POLICY,'source_sha256':expected,'source_size':[w,h],'views':views}
    write_json(manifest,record);validate_views(payload,record)
    return record

def validate_views(payload,record):
    if record['policy']!=POLICY or record['source_sha256']!=payload['image_sha256']:raise ValueError('view_identity_mismatch')
    if sha(payload['image_path'])!=payload['image_sha256']:raise ValueError('source_image_changed')
    with Image.open(payload['image_path']) as im:
        source=im.convert('RGB');w,h=source.size
        if record['source_size']!=[w,h] or len(record['views'])!=4:raise ValueError('view_geometry_mismatch')
        for item,name,box in zip(record['views'],POLICY['order'],boxes(w,h)):
            if item['name']!=name or item['box']!=list(box):raise ValueError('view_geometry_mismatch')
            if sha(item['image_path'])!=item['image_sha256']:raise ValueError('view_file_changed')
            with Image.open(item['image_path']) as crop:
                expected=source.crop(box)
                if crop.size!=expected.size or crop.convert('RGB').tobytes()!=expected.tobytes():raise ValueError('view_pixels_changed')

class MultiViewStage(VisualStage):
    def __init__(self,config_path='decomposition/api_config.local.json',transport=None,view_records=None):
        super().__init__(config_path,transport=transport)
        self.view_records=copy.deepcopy(view_records or {})
        self.identity={**self.identity,'query_view_policy':POLICY,'view_manifest_sha':digest(self.view_records)}

    def messages(self,payload):
        # Deliberately leave all six few-shot messages and the original query unchanged.
        messages=super().messages(payload)
        record=self.view_records[payload['image_sha256']]
        validate_views(payload,record)
        for item in record['views']:
            descriptor={'view_of_same_image':item['name'],'original_pixel_box':item['box'],'original_size':record['source_size']}
            messages[-1]['content'].append({'type':'text','text':json.dumps(descriptor)})
            messages[-1]['content'].append({'type':'image_url','image_url':{'url':self._image(item),'detail':'original'}})
        return messages
