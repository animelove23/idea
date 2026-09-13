"""Connect frozen modules for explicitly selected pairs; no reference labels in production inputs."""
import argparse
from pathlib import Path
from .common import read_jsonl,new_run,write_json,write_jsonl,check_frozen,sha,report
from .contracts import normalize_document,model_document
from .llm import FewShotStage,CallFailure,ROOT
from .m1_lexical import LexicalRecorder
from .m3_align import validate_alignment
from .m4_queue import build_queue,execute as export_queue
from .m5_verify import VisualStage,validate_label
from .m6_analysis import execute as export_analysis


def call(stage,payload,path,validator):
    write_json(path.with_name(path.stem+'_started.json'),{'started':True})
    audit={}
    try:
        raw,audit=stage.run(payload)
        write_json(path.with_name(path.stem+'_response.json'),audit)
        value=validator(raw)
        record={'status':'complete','value':value,'audit':audit}
    except CallFailure as exc:
        record={'status':'technical_failure','audit':exc.audit}
    except (ValueError,TypeError,KeyError) as exc:
        record={'status':'technical_failure','audit':audit,'validation_error':type(exc).__name__}
    write_json(path,record)
    return record


def execute(pairs_path,pair_ids,output,config='decomposition/api_config.local.json',stages=None,parser=None):
    roster=read_jsonl(pairs_path);by_id={r['pair_id']:r for r in roster}
    if len(by_id)!=len(roster):raise ValueError('Duplicate source pair ID')
    if len(set(pair_ids))!=len(pair_ids) or set(pair_ids)-by_id.keys():raise ValueError('Duplicate/unknown selected pair')
    selected=[by_id[i] for i in pair_ids]
    stages=stages or {'decompose':FewShotStage('decompose',config),'align':FewShotStage('align',config),'verify':VisualStage(config)}
    parser=parser or LexicalRecorder()
    images=[]
    for p in selected:
        path=p.get('image_path')
        if path and Path(path).is_file():images.append(path)
    # Keep all local data/code versions explicit; no credentials in manifest.
    files=[pairs_path,*[ROOT/'prompts'/f'{s}.txt' for s in stages],*[ROOT/'shots'/f'{s}.jsonl' for s in stages],*images]
    files += [ex['input']['image_path'] for ex in read_jsonl(ROOT/'shots/verify.jsonl')]
    out=new_run(output,'pipeline',files,{'pair_ids':pair_ids,'stages':{s:m.identity for s,m in stages.items()},'nlp':parser.identity},list(ROOT.glob('*.py')))
    bundles=[];verifications=[];statuses=[]
    for number,p in enumerate(selected):
        check_frozen(out);pair_id=p['pair_id'];pairdir=out/f'pair_{number:04d}';pairdir.mkdir()
        if any(p.get(s) is None for s in ('original','steer')):
            statuses.append({'pair_id':pair_id,'status':'missing_caption','analysis_available':False})
            continue
        docs={};lexical={};failed=False
        for side in ('original','steer'):
            c=p[side];lexical[side]=parser.record(c['caption_id'],c['text'])
            response=call(stages['decompose'],{'text':c['text']},pairdir/f'm2_{side}.json',
                          lambda raw:normalize_document(raw,c['text'],c['caption_id']))
            if response['status']=='complete':docs[side]=response['value']
            else:
                failed=True
                docs[side]={'caption_id':c['caption_id'],'text':c['text'],'entities':[],'facts':[],
                            'issues':[{'reason':'technical_decomposition_failure'}],'status':'technical_failure'}
        if failed:
            aligned=validate_alignment({'entities':[],'alignments':[]},docs['original'],docs['steer'])
        else:
            payload={s:model_document(docs[s]) for s in docs}
            response=call(stages['align'],payload,pairdir/'m3.json',
                          lambda raw:validate_alignment(raw,docs['original'],docs['steer']))
            aligned=response.get('value') or validate_alignment({'entities':[],'alignments':[]},docs['original'],docs['steer'])
        path=p.get('image_path') or ''
        hash_value=p.get('image_sha256')
        image_ok=bool(path and Path(path).is_file() and hash_value and sha(path)==hash_value)
        b={'pair_id':pair_id,**docs,'alignment':aligned,'lexical':lexical,'image_path':path,'image_sha256':hash_value}
        bundles.append(b);write_json(pairdir/'bundle.json',b)
        queue=build_queue(pair_id,docs['original'],docs['steer'],aligned,path,hash_value,lexical)
        write_jsonl(pairdir/'verification_queue.jsonl',queue)
        for item in queue:
            check_frozen(out)
            if not image_ok:
                v={'claim_id':item['claim_id'],'label':None,'status':'image_unavailable'}
            else:
                response=call(stages['verify'],item,pairdir/f'm5_{item["claim_id"]}.json',validate_label)
                v={'claim_id':item['claim_id'],'label':None,'status':response['status'],**response.get('value',{})}
            verifications.append(v)
        statuses.append({'pair_id':pair_id,'status':'decomposition_failure' if failed else aligned['status'],
                         'image_available':image_ok,'analysis_available':True})
        write_jsonl(out/'pair_status.jsonl',statuses)
    write_jsonl(out/'pair_status.jsonl',statuses)
    write_jsonl(out/'bundles.jsonl',bundles);write_jsonl(out/'verification.jsonl',verifications)
    export_queue(out/'bundles.jsonl',out/'m4')
    export_analysis(out/'bundles.jsonl',out/'m4/verification_queue.jsonl',out/'verification.jsonl',out/'m6')
    report(out,'冻结模块串联运行',{'selected_pairs':len(selected),'pair_statuses':statuses,
                                'verified_claims':sum(v['label'] is not None for v in verifications),
                                'pending_claims':sum(v['label'] is None for v in verifications)},
           ['无参考答案输入；串联分布不等于端到端准确率。',
            'M2技术失败的pair禁止正常对齐推断；保留可用事实，但总体召回未知，不能解释为零事实。',
            '选择的pair必须已获得所需数据外发授权；不会隐式扩大到整个清单。'])
    return statuses


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--pairs',required=True)
    p.add_argument('--pair-id',action='append',required=True);p.add_argument('--output',required=True)
    p.add_argument('--config',default='decomposition/api_config.local.json');a=p.parse_args()
    execute(a.pairs,a.pair_id,a.output,a.config)
