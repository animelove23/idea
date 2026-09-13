"""One independent, evidence-focused review; original full image always retained."""
import base64,copy,io,json
from PIL import Image
from analysis_skeleton.common import sha
from analysis_skeleton.final_v1.routing import TypedVisualStage,validate_typed
from analysis_skeleton.framework_v2.runtime import SafeStage

REVIEW_RULES='''Independent evidence review. Do not assume caption claims are true. First locate the intended referent using the full image and caption anchors. Then inspect only the requested proposition. An optional detail image is an unverified proposed region from the SAME original image, not proof of correct identity; reject it if it does not correspond. Bboxes in your response MUST use coordinates of the FULL image on 0..1000. For an attribute, resolve its owner first; do not transfer a property from a nearby different object. If blur, grayscale, occlusion or missing scale prevents a verdict, retain unresolved. Inspect the whole image before not_found; a crop cannot establish absence. Use the same exact JSON evidence schema as the demonstrations. Never return label or an attribute_status of not_applicable for an attribute request.'''


def detail(payload):
    box=payload.get('review_bbox')
    if not isinstance(box,list) or len(box)!=4 or any(type(v)is not int or not 0<=v<=1000 for v in box):return None
    if box[0]>=box[2] or box[1]>=box[3]:return None
    if sha(payload['image_path'])!=payload['image_sha256']:raise ValueError('image_hash_changed')
    with Image.open(payload['image_path']) as im:
        w,h=im.size;x0,y0,x1,y1=box
        # Context padding, no synthesized pixels, sharpening, recoloring or inpainting.
        pad=max(40,round(max(x1-x0,y1-y0)*.2))
        region=(max(0,(x0-pad)*w//1000),max(0,(y0-pad)*h//1000),min(w,(x1+pad)*w//1000),min(h,(y1+pad)*h//1000))
        if region[2]-region[0]<8 or region[3]-region[1]<8:return None
        stream=io.BytesIO();im.convert('RGB').crop(region).save(stream,format='PNG')
        return 'data:image/png;base64,'+base64.b64encode(stream.getvalue()).decode('ascii')


class ReviewStage(TypedVisualStage):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        for kind,stage in self.stages.items():
            source=stage.source;old_messages=source.messages
            def messages(payload,old=old_messages):
                safe={k:copy.deepcopy(v) for k,v in payload.items() if k in {'image_path','image_sha256','statement','entity_context','claim_type'}}
                out=old(safe);out[0]['content']+='\n'+REVIEW_RULES
                out[-1]['content'][0]['text']+='\nReview task: '+payload.get('review_focus','locate referent and inspect the proposition')
                crop=detail(payload)
                if crop:out[-1]['content'] += [{'type':'text','text':'Unverified detail proposal; locate it in the full image before use.'},
                    {'type':'image_url','image_url':{'url':crop,'detail':'original'}}]
                return out
            source.messages=messages
            source.identity={**source.identity,'review_code_sha':sha(__file__),'review_round':2,'blind_to_first_verdict':True,'detail_policy':'unverified_bbox_plus_padding_full_image_always'}
            self.stages[kind]=SafeStage(source)
        self.identity={**self.identity,'review_code_sha':sha(__file__),'review_round':2,
            'contracts':{k:copy.deepcopy(v.identity) for k,v in self.stages.items()}}


def merge(first,second):
    result=copy.deepcopy(first)
    if second.get('status')!='complete':return result
    new=second['value']
    if first.get('label') in (None,'uncertain'):
        return {**result,**new,'review_source_response_id':second.get('audit',{}).get('response_id')}
    if new['label']!=first['label']:
        result.update(label='uncertain',reason='independent_review_disagrees_with_first_verdict',review_conflict=True)
    return result
