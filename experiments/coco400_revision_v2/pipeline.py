"""Profile-selected final pipeline; preserves upstream framework data and audits."""
import copy
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
from .local_alignment import validate_local as validate_alignment
from .guard import GuardStage
from analysis_skeleton.final_v1.decompose import FinalDecomposeStage,normalize_final
from analysis_skeleton.final_v1.visual import FinalVisualStage,validate as validate_proposition
from analysis_skeleton.final_v1.context import build_context,document_context,identity as context_identity
from analysis_skeleton.final_v1.statistics import strict_analysis
from analysis_skeleton.final_v1.routing import TypedVisualStage,read_routing_manifest,routing_inputs,validate_typed,contract_for
from analysis_skeleton.evidence_verifier_v2.experiment import FlashStage
from analysis_skeleton.evidence_verifier_v1.compiler import compile_evidence
from analysis_skeleton.framework_v2.runtime import SafeStage,ResponseCache,Checkpoints,CheckpointIntegrityError,diagnostic
from analysis_skeleton.framework_v2.queue import build_queue
from analysis_skeleton.framework_v2.ledger import production


MODEL='deepseek-flash'


def validate_profile(profile):
    if not isinstance(profile,dict):
        raise ValueError('explicit_profile_dictionary_required')
    required={'decompose_candidate','visual_candidate','value_anchors','state_support','visual_shots_path'}
    if set(profile)!=required:raise ValueError('profile_requires_exact_public_fields')
    if profile['decompose_candidate'] not in ('owner','control'):raise ValueError('invalid_decompose_candidate')
    if profile['visual_candidate'] not in ('proposition','context','typed'):raise ValueError('invalid_visual_candidate')
    if any(type(profile[k]) is not bool for k in ('value_anchors','state_support')):raise ValueError('profile_flags_must_be_boolean')
    if not isinstance(profile['visual_shots_path'],str) or not Path(profile['visual_shots_path']).is_file():
        raise ValueError('visual_shots_path_must_exist')
    if profile['visual_candidate']=='typed':read_routing_manifest(profile['visual_shots_path'])
    return copy.deepcopy(profile)


def make_stages(profile,config):
    decompose=(FinalDecomposeStage(config) if profile['decompose_candidate']=='owner'
               else FewShotStage('decompose',config,model=MODEL))
    if profile['visual_candidate']=='typed':
        visual=TypedVisualStage(profile['visual_shots_path'],config)
    else:
        source=(FinalVisualStage(profile['visual_shots_path'],config)
                if profile['visual_candidate']=='proposition'
                else FlashStage(profile['visual_shots_path'],'sufficiency',config))
        visual=SafeStage(source)
    return {'decompose':SafeStage(decompose),
            'align':SafeStage(GuardStage(config)),
            'verify':visual}


def enrich_queue(items,docs):
    result=[]
    for item in items:
        q=copy.deepcopy(item);contexts=[];kinds=set()
        try:
            if not q['refs']:raise ValueError('claim_without_refs')
            for ref in q['refs']:
                doc=docs[ref['side']]
                fact=next(f for f in doc['facts'] if f['id']==ref['fact_id'])
                entity=next(e for e in doc['entities'] if e['id']==fact['entity_id'])
                kinds.add(fact['type'])
                contexts.append({**ref,'context':build_context(doc,entity,fact),
                                 'audit':document_context(doc,entity,fact)['audit']})
            if len(kinds)!=1 or not kinds<={'entity','attribute'}:raise ValueError('mixed_or_invalid_claim_types')
            q['claim_type']=next(iter(kinds))
            q['entity_context']=contexts[0]['context']
            q['final_context_audit']={'by_ref':contexts,'query_source_ref':copy.deepcopy(q['refs'][0]),
                                      'contexts_exactly_equal':len({digest(c['context']) for c in contexts})==1,
                                      'shared_visual_referent_independently_verified':False}
        except (KeyError,StopIteration,ValueError,TypeError):
            q['routing_error']='claim_context_or_type_unresolved'
        result.append(q)
    return result


def image_error(path,expected):
    try:
        if not path or not expected or sha(path)!=expected:return 'image_missing_or_hash_mismatch'
        with Image.open(path) as im:im.verify()
        return None
    except (OSError,ValueError):return 'image_unavailable_or_corrupt'


def execute(pairs_path,output,pair_ids=None,config='decomposition/api_config.local.json',cache_path=None,
            cache_mode='fresh',resume=False,condition_id='final_v1',replicate_id='r1',stages=None,parser=None,profile=None):
    # The inherited cross-run response cache predates the visual claim_type
    # contract. Same-run checkpoints include the complete payload and remain safe.
    # Reject before reading profile/config/data or constructing an API stage.
    if cache_mode!='fresh' or cache_path:
        raise ValueError('final_v1_supports_fresh_and_same_run_resume_only')
    profile_path=Path(profile) if isinstance(profile,(str,Path)) else None
    profile=validate_profile(read_json(profile_path) if profile_path else profile)
    roster=read_jsonl(pairs_path);by_id={p['pair_id']:p for p in roster}
    ids=list(by_id) if pair_ids is None else pair_ids
    if len(by_id)!=len(roster) or len(ids)!=len(set(ids)) or set(ids)-by_id.keys():raise ValueError('duplicate_or_unknown_pair_id')
    if not condition_id or not replicate_id:raise ValueError('condition_and_replicate_required')
    selected=[by_id[i] for i in ids]
    caption_ids=[p[s]['caption_id'] for p in selected for s in ('original','steer') if p.get(s) is not None]
    if len(caption_ids)!=len(set(caption_ids)):raise ValueError('duplicate_caption_id')
    parser=parser or LexicalRecorder();locator=SourceLocator(parser)
    if stages is None:
        stages=make_stages(profile,config)
    if set(stages)!={'decompose','align','verify'}:raise ValueError('all_three_stages_required')
    cache=ResponseCache(read_jsonl(cache_path) if cache_path else [])
    files=[pairs_path,profile['visual_shots_path'],*([profile_path] if profile_path else []),*([cache_path] if cache_path else []),
           *[ROOT/'prompts'/f'{s}.txt' for s in stages],*[ROOT/'shots'/f'{s}.jsonl' for s in stages]]
    files += [ROOT/'final_v1/decompose_rules.txt',ROOT/'final_v1/visual_rules.txt',Path(__file__).parent/'align.txt',Path(__file__).parent/'align_shots.jsonl',
              ROOT/'evidence_verifier_v1/prompt.txt',ROOT/'evidence_verifier_v2/sufficiency.txt']
    files += [p['image_path'] for p in selected if p.get('image_path') and Path(p['image_path']).is_file()]
    if profile['visual_candidate']=='typed':files += routing_inputs(profile['visual_shots_path'])
    else:files += [r['input']['image_path'] for r in read_jsonl(profile['visual_shots_path'])]
    code=[*Path(__file__).parent.glob('*.py'),*(ROOT/'framework_v2').glob('*.py'),
          *ROOT.glob('*.py'),*(ROOT/'repair_v1').glob('*.py'),
          ROOT/'decompose_iteration_v1/value_anchor.py',ROOT/'evidence_verifier_v1/stage.py',
          ROOT/'evidence_verifier_v1/compiler.py',ROOT/'evidence_verifier_v2/experiment.py',
          ROOT/'expansion20/scorer_sensitivity.py',Path('decomposition/storage.py'),Path('decomposition/pos_parser.py')]
    visual_validator=(validate_typed if profile['visual_candidate']=='typed' else
                      validate_proposition if profile['visual_candidate']=='proposition' else compile_evidence)
    identity={'profile':profile,'context':context_identity(),'condition_id':condition_id,'replicate_id':replicate_id,'pair_ids':ids,'cache_mode':cache_mode,
              'cache_fingerprint':cache.fingerprint,'nlp':parser.identity,'stages':{s:v.identity for s,v in stages.items()},
              'transport_timeouts':{s:getattr(getattr(getattr(v,'source',None),'config',None),'timeout',None) for s,v in stages.items()},
              'image_manifest':[{'pair_id':p['pair_id'],'image_path':p.get('image_path'),'sha256':p.get('image_sha256')} for p in selected]}
    out=Path(output)
    if resume:
        manifest=check_frozen(out)
        if manifest['config']!=identity:raise CheckpointIntegrityError('resume_run_identity_changed')
    else:
        new_run(out,'revision_v2_first_pass_pipeline',files,identity,code);manifest=read_json(out/'manifest.json')
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
                    r=checkpoints.call(key,stages['decompose'],{'text':c['text']},lambda raw:normalize_final(raw,c['text'],c['caption_id'],value_anchors=profile['value_anchors'],state_support=profile['state_support']))
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
                items=enrich_queue(items,docs)
                phase='verify';error=image_error(bundle['image_path'],bundle['image_sha256']);values=[]
                for item in items:
                    if item.get('routing_error'):
                        values.append({'claim_id':item['claim_id'],'label':None,'status':'technical_failure','reason':item['routing_error']});continue
                    if error:values.append({'claim_id':item['claim_id'],'label':None,'status':'image_unavailable','reason':error});continue
                    r=checkpoints.call(f'{pid}:verify:{item["claim_id"]}',stages['verify'],item,lambda raw,kind=item['claim_type']:visual_validator(raw,kind))
                    calls.append(r)
                    values.append({'claim_id':item['claim_id'],'label':None,'status':r['status'],**r.get('value',{}),
                                   'audit':r.get('audit',{}),
                                   'compiler_contract':contract_for(item['claim_type']) if profile['visual_candidate']=='typed' else profile['visual_candidate']})
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
        write_json(out/'strict_analysis.json',strict_analysis(ledger))
        if (out/'m6/manifest.json').exists():check_frozen(out/'m6')
        else:export_m6(out/'bundles.jsonl',out/'verification_queue.jsonl',out/'verification.jsonl',out/'m6')
        metrics={'selected_pairs':len(selected),'analyzed_pairs':len(bundles),'facts':len(ledger),'claims':len(queue),
                 'pending_claims':sum(v['label'] is None for v in verification),'failed_pairs':len(failed),
                 'call_status_counts':{s:sum(r['status']==s for r in calls) for s in sorted({r['status'] for r in calls})},
                 'new_api_calls_this_invocation':checkpoints.new_api_calls,'resumed_checkpoints':checkpoints.resumed,
                 'cache_hits':sum(bool(r.get('audit',{}).get('cache_hit')) for r in calls),
                 'shared_claims':sum(len(q['refs'])>1 for q in queue),
                 'alignment_technical_facts':sum(r['alignment_axis']=='technical_unresolved' for r in ledger),
                 'reference_truth_available':False,'research_accuracy_validated':False,'release_profile':profile,
                 'recommended_semantic_statistics':'strict_analysis.json',
                 'legacy_m6_statistics':'historical_parent_policy_not_strict_supported_denominator',
                 'visual_routing_failures':sum(bool(q.get('routing_error')) for q in queue)}
        write_json(out/'metrics.json',metrics)
        return metrics
