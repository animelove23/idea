"""M5: actual multi-image few-shot DeepSeek verification; never text-only fallback."""
import argparse
import base64
import json
from collections import Counter
from pathlib import Path
from PIL import Image

from .common import new_run,read_jsonl,write_json,write_jsonl,report,check_frozen,sha,ratio
from .contracts import LABELS
from .llm import FewShotStage,CallFailure,ROOT
from .metrics import prf


class VisualStage(FewShotStage):
    def __init__(self,config_path='decomposition/api_config.local.json',transport=None,model='deepseek-flash'):
        super().__init__('verify',config_path,transport,model)
        for ex in self.shots:
            self._image(ex['input'])
        self.identity['image_detail']='original'
        self.identity['vision_docs']='https://api-docs.deepseek.com/guides/vision/'
        self.identity['shot_image_hashes']=[ex['input']['image_sha256'] for ex in self.shots]

    @staticmethod
    def _image(payload):
        path=Path(payload['image_path'])
        if payload.get('image_sha256') is None or sha(path)!=payload['image_sha256']:
            raise ValueError('Image hash missing/mismatch')
        with Image.open(path) as im:
            fmt=im.format;im.verify()
        mime={'JPEG':'image/jpeg','PNG':'image/png','WEBP':'image/webp','GIF':'image/gif'}.get(fmt)
        if not mime:raise ValueError('Unsupported image format')
        return 'data:'+mime+';base64,'+base64.b64encode(path.read_bytes()).decode('ascii')

    def user(self,payload):
        if not isinstance(payload.get('statement'),str):raise ValueError('Statement required')
        text={k:payload[k] for k in ('statement','entity_context') if k in payload}
        return {'role':'user','content':[{'type':'text','text':json.dumps(text,ensure_ascii=False)},
                                         {'type':'image_url','image_url':{'url':self._image(payload),'detail':'original'}}]}

    def messages(self,payload):
        messages=[{'role':'system','content':self.rules}]
        for ex in self.shots:
            messages += [self.user(ex['input']),{'role':'assistant','content':json.dumps(ex['output'],ensure_ascii=False)}]
        return messages+[self.user(payload)]


def validate_label(raw):
    if not isinstance(raw,dict) or raw.get('label') not in LABELS or not isinstance(raw.get('reason'),str):
        raise ValueError('Explicit supported/hallucinated/uncertain label and short reason required')
    return {'label':raw['label'],'reason':raw['reason']}


def score_labels(records):
    matrix=Counter((r['reference_label'],r.get('prediction',{}).get('label','technical_failure')) for r in records)
    by_label={label:prf(matrix[(label,label)],sum(v for (g,p),v in matrix.items() if p==label),
                        sum(v for (g,p),v in matrix.items() if g==label)) for label in sorted(LABELS)}
    valid=sum(r.get('prediction',{}).get('label') in LABELS for r in records)
    decided=sum(r.get('prediction',{}).get('label') in {'supported','hallucinated'} for r in records)
    active=[v['f1'] for v in by_label.values() if v['reference'] or v['predicted']]
    return {'cases':len(records),'valid_labels':valid,'technical_failures':len(records)-valid,
            'by_label':by_label,'macro_f1':sum(active)/len(active) if active else None,
            'confusion':[{'reference':g,'prediction':p,'count':n} for (g,p),n in sorted(matrix.items())],
            'decided_coverage':ratio(decided,len(records)),
            'false_supported_rate':ratio(matrix[('hallucinated','supported')],sum(v for (g,p),v in matrix.items() if g=='hallucinated')),
            'false_hallucinated_rate':ratio(matrix[('supported','hallucinated')],sum(v for (g,p),v in matrix.items() if g=='supported')),
            'reference_status':'assistant_visual_candidate_not_human_gold','human_accuracy':None}


def execute(cases_path,output,config='decomposition/api_config.local.json'):
    cases=read_jsonl(cases_path);stage=VisualStage(config)
    shot_images={ex['input']['image_sha256'] for ex in stage.shots}
    if any(c['input']['image_sha256'] in shot_images for c in cases):raise ValueError('Few-shot/test image overlap')
    images={ex['input']['image_path'] for ex in stage.shots}|{c['input']['image_path'] for c in cases}
    out=new_run(output,'M5',[cases_path,stage.rules_path,stage.shots_path,*sorted(images)],stage.identity,
                [__file__,ROOT/'llm.py',ROOT/'metrics.py'])
    records=[]
    for c in cases:
        check_frozen(out);key=c['case_id'];write_json(out/(key+'_started.json'),{'started':True})
        record={k:c[k] for k in ('case_id','image_id','semantic_type','reference_label')}
        audit={}
        try:
            raw,audit=stage.run(c['input'])
            write_json(out/(key+'_response.json'),audit)
            record['prediction']=validate_label(raw)
        except CallFailure as exc:audit=exc.audit
        except ValueError as exc:audit={**audit,'validation_error':str(exc)}
        record['audit']=audit;records.append(record);write_json(out/(key+'.json'),record)
        print(f"M5 {key}: {record.get('prediction',{}).get('label','technical_failure')}",flush=True)
    write_jsonl(out/'results.jsonl',records)
    report(out,'M5 固定6图文few-shot视觉测评',score_labels(records),
           ['发送实际原图；query不包含参考标签、模型来源或对齐状态；图片哈希随run冻结。',
            '参考是助手看图后预写的候选标签，不是独立人工gold；本轮不能据此宣称真实准确率。',
            '模型由官方图像指南选择deepseek-flash，返回模型标识逐请求保存；没有文本替代或多模型投票。'])


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--cases',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();execute(a.cases,a.output)
