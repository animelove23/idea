"""Primary v5 batch entry point; v4 command remains available for old runs."""
import argparse
import csv
import json
from pathlib import Path
from .caption_parser import load_sources,caption_row
from .pos_parser import SpacyParser
from .config import API_CONFIG_PATH,load_api_config
from .storage import digest,write_json,write_jsonl,output_lock
from .v5.pipeline import DecomposerV5,V5Failure,prompts
from .v5 import VERSION

def main():
    p=argparse.ArgumentParser(description='Five-dimensional v5 two-stage decomposer')
    p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--shots',choices=[0,8],type=int,default=8);p.add_argument('--method');p.add_argument('--decode');p.add_argument('--limit',type=int);p.add_argument('--prepare-only',action='store_true');p.add_argument('--resume',action='store_true');p.add_argument('--api-config',type=Path,default=API_CONFIG_PATH)
    p.add_argument('--spacy-model',default='en_core_web_md',help='Caption-level POS only; never passed to semantic model')
    a=p.parse_args()
    if a.limit is not None and a.limit<1:p.error('--limit must be positive')
    records,failures=load_sources([{'path':str(a.input.resolve()),'method':a.method,'decode':a.decode}],a.limit)
    parser=SpacyParser(a.spacy_model)
    ps=prompts(a.shots);config=None if a.prepare_only else load_api_config(a.api_config)
    protocol={'version':VERSION,'shots':a.shots,'prompts':ps,'input_digest':digest(records),'model':config.model if config else None,'base_url':config.base_url if config else None,'max_tokens':config.max_tokens if config else None,'thinking':'disabled','temperature':0,'code':{f.name:digest(f.read_text(encoding='utf-8')) for f in Path(__file__).with_name('v5').iterdir() if f.is_file()}}
    protocol['pos_parser']=parser.identity
    with output_lock(a.output):
        path=a.output/'manifest.json'
        if path.exists():
            if not a.resume or json.loads(path.read_text(encoding='utf-8'))!=protocol:raise ValueError('Existing run requires --resume with identical input/config/version; use new output for prepare->execute')
        else:write_json(path,protocol)
        (a.output/'checkpoints').mkdir(exist_ok=True);write_json(a.output/'input_failures.json',failures)
        client=DecomposerV5(config,shots=a.shots,frozen_prompts=ps) if config else None
        saved=[]
        for r in records:
            ck=a.output/'checkpoints'/f"{digest(r['sample_id'])}.json"
            if ck.exists():result=json.loads(ck.read_text(encoding='utf-8'))
            elif a.prepare_only:result={'sample_id':r['sample_id'],'status':'prepared','caption':r,'request':{'id':'caption','text':r['caption']}}
            else:
                try:
                    d,audit=client.decompose(r['caption']);result={'sample_id':r['sample_id'],'status':'success','caption':r,'document':{**d,'id':r['sample_id']},'audit':audit}
                except V5Failure as e:result={'sample_id':r['sample_id'],'status':'failed','caption':r,'error':str(e),'audit':e.audit}
            write_json(ck,result);saved.append(result);print(r['sample_id'],result['status'],flush=True)
        write_jsonl(a.output/'results.jsonl',saved);write_jsonl(a.output/'samples.jsonl',[r['document'] for r in saved if r['status']=='success'])
        caption_rows=[]
        for r in saved:
            pos,n=parser.parse(r['caption']['caption']);caption_rows.append({**caption_row(r['caption'],n,pos),'semantic_status':r['status']})
        for name in ['captions','entities','facts']:
            rows=caption_rows if name=='captions' else [{'sample_id':r['sample_id'],**item} for r in saved if r['status']=='success' for item in r['document'][name]]
            fields=list(dict.fromkeys(k for row in rows for k in row))
            with (a.output/f'{name}.csv').open('w',encoding='utf-8-sig',newline='') as f:
                writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
                for row in rows:writer.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in row.items()})
        return int(bool(failures) or any(r['status']=='failed' for r in saved))

if __name__=='__main__':raise SystemExit(main())
