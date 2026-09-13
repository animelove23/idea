"""Generic versioned pipeline; resume fixed checkpoints, isolate failed pairs and claims."""
import argparse
from pathlib import Path
from PIL import Image
from decomposition.storage import output_lock
from analysis_skeleton.common import read_jsonl,read_json,write_json,write_jsonl,write_csv,new_run,check_frozen,sha,digest
from analysis_skeleton.contracts import model_document
from analysis_skeleton.llm import FewShotStage,ROOT
from analysis_skeleton.m5_verify import VisualStage,validate_label
from analysis_skeleton.m1_lexical import LexicalRecorder
from analysis_skeleton.repair_v1.context import SourceLocator
from analysis_skeleton.m6_analysis import execute as export_m6
from .contracts import normalize_document,validate_alignment
from .runtime import SafeStage,ResponseCache,Checkpoints,CheckpointIntegrityError,diagnostic
from .queue import build_queue
from .ledger import production


def image_error(path,expected):
    try:
        if not path or not expected or sha(path)!=expected:return 'image_missing_or_hash_mismatch'
        with Image.open(path) as im:im.verify()
        return None
    except (OSError,ValueError):return 'image_unavailable_or_corrupt'


def execute(pairs_path,output,pair_ids=None,config='decomposition/api_config.local.json',cache_path=None,
            cache_mode='fresh',resume=False,condition_id='engineering_v2',replicate_id='r1',stages=None,parser=None):
    roster=read_jsonl(pairs_path);by_id={p['pair_id']:p for p in roster}
    ids=list(by_id) if pair_ids is None else pair_ids
    if len(by_id)!=len(roster) or len(ids)!=len(set(ids)) or set(ids)-by_id.keys():raise ValueError('duplicate_or_unknown_pair_id')
    if not condition_id or not replicate_id:raise ValueError('condition_and_replicate_required')
    selected=[by_id[i] for i in ids]
    caption_ids=[p[s]['caption_id'] for p in selected for s in ('original','steer') if p.get(s) is not None]
    if len(caption_ids)!=len(set(caption_ids)):raise ValueError('duplicate_caption_id')
    parser=parser or LexicalRecorder();locator=SourceLocator(parser)
    if stages is None:
        stages={'decompose':SafeStage(FewShotStage('decompose',config)),
                'align':SafeStage(FewShotStage('align',config)),
                'verify':SafeStage(VisualStage(config))}
    if set(stages)!={'decompose','align','verify'}:raise ValueError('all_three_stages_required')
    cache=ResponseCache(read_jsonl(cache_path) if cache_path else [])
    files=[pairs_path,*([cache_path] if cache_path else []),
           *[ROOT/'prompts'/f'{s}.txt' for s in stages],*[ROOT/'shots'/f'{s}.jsonl' for s in stages]]
    code=[*Path(__file__).parent.glob('*.py'),*ROOT.glob('*.py'),* (ROOT/'repair_v1').glob('*.py'),
          ROOT/'expansion20/scorer_sensitivity.py',Path('decomposition/storage.py'),Path('decomposition/pos_parser.py')]
    identity={'condition_id':condition_id,'replicate_id':replicate_id,'pair_ids':ids,'cache_mode':cache_mode,
              'cache_fingerprint':cache.fingerprint,'nlp':parser.identity,'stages':{s:v.identity for s,v in stages.items()},
              'transport_timeouts':{s:getattr(getattr(getattr(v,'source',None),'config',None),'timeout',None) for s,v in stages.items()},
              'image_manifest':[{'pair_id':p['pair_id'],'image_path':p.get('image_path'),'sha256':p.get('image_sha256')} for p in selected]}
    out=Path(output)
    if resume:
        manifest=check_frozen(out)
        if manifest['config']!=identity:raise CheckpointIntegrityError('resume_run_identity_changed')
    else:
        new_run(out,'framework_v2',files,identity,code);manifest=read_json(out/'manifest.json')
    with output_lock(out):
        checkpoints=Checkpoints(out/'checkpoints',digest(manifest),cache,cache_mode)
        bundles=[];queue=[];verification=[];statuses=[];failed=[];ledger=[];isolated=[];words=[];calls=[]
        for p in selected:
            check_frozen(out);pid=p['pair_id'];docs={};phase='caption'
            try:
                if any(p.get(s) is None for s in ('original','steer')):
                    statuses.append({'pair_id':pid,'status':'missing_caption','analysis_available':False});continue
                lexical={};upstream_failed=False
                for side in ('original','steer'):
                    c=p[side];phase='lexical';lexical[side]=parser.record(c['caption_id'],c['text'])
                    phase='decompose';key=f'{pid}:decompose:{side}'
                    r=checkpoints.call(key,stages['decompose'],{'text':c['text']},lambda raw:normalize_document(raw,c['text'],c['caption_id']))
                    calls.append(r)
                    if r['status']=='complete':docs[side]=r['value']
                    else:
                        upstream_failed=True
                        docs[side]={'caption_id':c['caption_id'],'text':c['text'],'entities':[],'facts':[],'excluded':[],
                                    'issues':[{'reason':'technical_decomposition_failure','call_status':r['status']}],
                                    'status':'technical_failure','source_audit':[]}
                phase='align'
                if upstream_failed:
                    aligned=validate_alignment({'entities':[],'alignments':[]},docs['original'],docs['steer'])
                else:
                    r=checkpoints.call(f'{pid}:align',stages['align'],{s:model_document(docs[s]) for s in docs},
                                       lambda raw:validate_alignment(raw,docs['original'],docs['steer']))
                    calls.append(r)
                    aligned=r.get('value') if r['status']=='complete' else None
                    if aligned is None:aligned=validate_alignment({'entities':[],'alignments':[]},docs['original'],docs['steer'])
                bundle={'pair_id':pid,**docs,'alignment':aligned,'lexical':lexical,
                        'image_path':p.get('image_path') or '', 'image_sha256':p.get('image_sha256')}
                phase='queue';items=build_queue(pid,docs['original'],docs['steer'],aligned,bundle['image_path'],bundle['image_sha256'],lexical,locator)
                phase='verify';error=image_error(bundle['image_path'],bundle['image_sha256']);values=[]
                for item in items:
                    if error:values.append({'claim_id':item['claim_id'],'label':None,'status':'image_unavailable','reason':error});continue
                    r=checkpoints.call(f'{pid}:verify:{item["claim_id"]}',stages['verify'],item,validate_label)
                    calls.append(r)
                    values.append({'claim_id':item['claim_id'],'label':None,'status':r['status'],**r.get('value',{})})
                phase='ledger';facts,events,lex,_=production(bundle,items,values)
                bundles.append(bundle);queue+=items;verification+=values;ledger+=facts;isolated+=events;words+=lex
                statuses.append({'pair_id':pid,'status':'decomposition_failure' if upstream_failed else aligned['status'],
                                 'analysis_available':True,'image_issue':error,'facts':len(facts),'claims':len(items),
                                 'pending_claims':sum(v['label'] is None for v in values)})
            except CheckpointIntegrityError:raise
            except Exception as exc:
                failed.append({'pair_id':pid,'phase':phase,'diagnostic':diagnostic(exc),'accepted_documents':docs})
                statuses.append({'pair_id':pid,'status':'unexpected_failure','phase':phase,'analysis_available':False})
            finally:
                write_jsonl(out/'pair_status.jsonl',statuses)
        for name,rows in [('bundles',bundles),('verification_queue',queue),('verification',verification),
                          ('denominator_ledger',ledger),('isolated_records',isolated),('lexical_slices',words),('failed_pairs',failed)]:
            write_jsonl(out/(name+'.jsonl'),rows)
        # Preserve any accepted facts even if an unexpected downstream bug prevented normal analysis.
        write_jsonl(out/'failed_pair_facts.jsonl',[{'pair_id':f['pair_id'],'side':s,'fact':fact,'downstream_status':'unavailable'}
            for f in failed for s,d in f['accepted_documents'].items() for fact in d['facts']])
        for name,rows in [('denominator_ledger',ledger),('lexical_slices',words)]:
            write_csv(out/(name+'.csv'),list(rows[0]) if rows else ['pair_id'],rows)
        if (out/'m6/manifest.json').exists():check_frozen(out/'m6')
        else:export_m6(out/'bundles.jsonl',out/'verification_queue.jsonl',out/'verification.jsonl',out/'m6')
        metrics={'selected_pairs':len(selected),'analyzed_pairs':len(bundles),'facts':len(ledger),'claims':len(queue),
                 'pending_claims':sum(v['label'] is None for v in verification),'failed_pairs':len(failed),
                 'call_status_counts':{s:sum(r['status']==s for r in calls) for s in sorted({r['status'] for r in calls})},
                 'new_api_calls_this_invocation':checkpoints.new_api_calls,'resumed_checkpoints':checkpoints.resumed,
                 'cache_hits':sum(bool(r.get('audit',{}).get('cache_hit')) for r in calls),
                 'shared_claims':sum(len(q['refs'])>1 for q in queue),
                 'alignment_technical_facts':sum(r['alignment_axis']=='technical_unresolved' for r in ledger),
                 'reference_truth_available':False,'research_accuracy_validated':False}
        write_json(out/'metrics.json',metrics)
        return metrics


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--pairs',required=True);p.add_argument('--output',required=True)
    p.add_argument('--pair-id',action='append');p.add_argument('--config',default='decomposition/api_config.local.json')
    p.add_argument('--cache');p.add_argument('--cache-mode',choices=['fresh','replay','reuse'],default='fresh')
    p.add_argument('--resume',action='store_true');p.add_argument('--condition-id',default='engineering_v2');p.add_argument('--replicate-id',default='r1')
    a=p.parse_args();print(execute(a.pairs,a.output,a.pair_id,a.config,a.cache,a.cache_mode,a.resume,a.condition_id,a.replicate_id))
