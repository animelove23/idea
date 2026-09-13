"""Evaluate all reusable legacy object/attribute claims; preserve full-claim labels."""
import argparse,json,random,re
from collections import Counter
from pathlib import Path
from analysis_skeleton.common import read_json,read_jsonl,write_json,write_jsonl,check_frozen,sha
from analysis_skeleton.evidence_verifier_v2.experiment import FlashStage
from analysis_skeleton.evidence_verifier_v1.compiler import compile_evidence
from analysis_skeleton.evidence_verifier_v1.experiment import score
from analysis_skeleton.framework_v2.runtime import SafeStage
from .batch import execute

SOURCE=Path('outputs/legacy_object_attribute_reuse/all_object_attribute_labels.jsonl')
DIRECT={'color','material','size','shape'}
# Reviewed only against the current textual slot definition, without model outputs.
REMAP={'195269:original:f9':'material','256003:original:f17':'size','256003:original:f18':'size',
       '317188:steer:f8':'material','32284:original:f3':'material','578655:original:f12':'color'}
COMPOSITE=re.compile(r'\b(two|three|four|five|six|seven|eight|nine|ten|thirteen|at least|pair of|group consists|red|green|blue|white|black|yellow|pink|purple|small|large|wooden|metal|left|right|middle|standing)\b|\d',re.I)

def scope_slot(row):
    if row['semantic_type']=='entity':return 'existence'
    if row['legacy_category'] in DIRECT:return row['legacy_category']
    return REMAP.get(row['case_id'])

def prepare(root):
    root=Path(root)
    if root.exists() and any(root.iterdir()):raise ValueError('new_directory_required')
    root.mkdir(parents=True,exist_ok=True);rows=read_jsonl(SOURCE);assert len(rows)==635
    shots=read_jsonl('outputs/evidence_verifier_v1/shots.jsonl');write_jsonl(root/'shots.jsonl',shots)
    shot_hashes={r['input']['image_sha256'] for r in shots};dev_ids={str(r['image_id']) for r in read_jsonl('analysis_skeleton/fixtures/expansion20/pairs.jsonl')}
    kept=[];excluded=[];tasks=[]
    for row in rows:
        slot=scope_slot(row)
        reason='fewshot_image_overlap' if row['input']['image_sha256'] in shot_hashes else 'outside_current_attribute_slots' if slot is None else None
        if reason:
            excluded.append({'case_id':row['case_id'],'image_id':row['image_id'],'reason':reason,'category':row['legacy_category'],'statement':row['input']['statement'],'source_reference_label':row['reference_label']});continue
        item={**row,'mapped_slot':slot,'partition':'previous_20_image_development' if row['image_id'] in dev_ids else 'additional_legacy_images',
              'possible_composite_entity_claim':row['semantic_type']=='entity' and bool(COMPOSITE.search(row['input']['statement']))}
        kept.append(item)
        tasks.append({'task_id':row['case_id'],'case_id':row['case_id'],'image_id':row['image_id'],'semantic_type':row['semantic_type'],
                      'condition':'sufficiency','input':{**row['input'],'claim_type':row['semantic_type']}})
    random.Random(20260919).shuffle(tasks);write_jsonl(root/'tasks.jsonl',tasks);write_jsonl(root/'references.jsonl',kept);write_jsonl(root/'excluded.jsonl',excluded)
    write_json(root/'protocol.json',{'source_rows':635,'cases':len(kept),'images':len({r['image_id'] for r in kept}),
        'by_type':dict(Counter(r['semantic_type'] for r in kept)),'excluded':dict(Counter(r['reason'] for r in excluded)),
        'factor':'No new visual modification; test frozen latest Flash sufficiency verifier on complete retained legacy labels',
        'model':'deepseek-flash','all_selected_rows_tested':True,'selection_before_predictions':True,'reference_labels_unchanged':True,
        'current_attribute_slots':['color','material','size','shape','state(open,closed,wet,dry,broken,intact)'],
        'remapped_legacy_categories':REMAP,'out_of_scope':'Remaining generic attributes and states are language/age/appearance/weather/posture/subjective/relational/nonasserted or outside the six state values.',
        'primary_score':'Agreement with original full-claim labels, not pure object-recognition accuracy; existing count/color/location modifiers in entity claims are preserved.',
        'supplementary_score':'Conservative regex flags possible composite entity claims; no reference/model answers used by flag. Unflagged subset is diagnostic, not adjudicated pure-entity gold.',
        'no_alignment_input_to_verifier':True,'no_reference_in_requests':True,'no_visual_vote_or_roi':True,'workers':4,
        'pass_goal':'Entity agreement strictly >90%; report whole denominator and every label. No production promotion without compatible independent reference.'})
    print(read_json(root/'protocol.json'),flush=True)

def run(root,resume=False):
    root=Path(root);s=SafeStage(FlashStage(root/'shots.jsonl','sufficiency'));rows=read_jsonl(root/'references.jsonl')
    files=[root/n for n in ('references.jsonl','shots.jsonl','protocol.json','excluded.jsonl')]+[SOURCE,Path('analysis_skeleton/evidence_verifier_v1/prompt.txt'),Path('analysis_skeleton/evidence_verifier_v2/sufficiency.txt')]
    files += [r['input']['image_path'] for r in rows]+[r['input']['image_path'] for r in read_jsonl(root/'shots.jsonl')]
    code=[__file__,'analysis_skeleton/evidence_verifier_v2/experiment.py','analysis_skeleton/evidence_verifier_v1/stage.py','analysis_skeleton/evidence_verifier_v1/compiler.py','analysis_skeleton/framework_v2/runtime.py','analysis_skeleton/llm.py','analysis_skeleton/m5_verify.py']
    execute(root,{'sufficiency':s},{'sufficiency':lambda raw,t:compile_evidence(raw,t['semantic_type'])},files,code,resume)

def report(root):
    root=Path(root);check_frozen(root/'run');rows=read_jsonl(root/'run/results.jsonl');refs={r['case_id']:r for r in read_jsonl(root/'references.jsonl')}
    assert len(rows)==len(refs) and {r['case_id'] for r in rows}==set(refs)
    scored=[{**r,'reference_label':refs[r['case_id']]['reference_label']} for r in rows]
    def group(rr):return {k:score([r for r in rr if k=='all' or r['semantic_type']==k],sum(k=='all' or r['semantic_type']==k for r in rr)) for k in ('all','entity','attribute')}
    metrics={'all_retained':group(scored)}
    for partition in ('previous_20_image_development','additional_legacy_images'):
        metrics[partition]=group([r for r in scored if refs[r['case_id']]['partition']==partition])
    unflagged=[r for r in scored if r['semantic_type']=='entity' and not refs[r['case_id']]['possible_composite_entity_claim']]
    metrics['unflagged_entity_diagnostic']=score(unflagged,len(unflagged));metrics['reference_status']='legacy_Codex_visual_annotations_not_independently_adjudicated_gold'
    metrics['new_api_calls']=read_json(root/'call_metrics.json')['new_api_calls'];metrics['entity_above_90']=metrics['all_retained']['entity']['agreement']>0.9
    metrics['models']=[{'requested':a,'returned':b,'count':n} for (a,b),n in Counter((r['audit']['identity']['model'],r['audit'].get('response_model')) for r in rows).items()]
    metrics['original_case_count']=635;metrics['tested_case_count']=len(rows);metrics['excluded_case_count']=len(read_jsonl(root/'excluded.jsonl'))
    write_json(root/'metrics.json',metrics)
    write_jsonl(root/'bad_cases.jsonl',[{**r,'reference':refs[r['case_id']]} for r in rows if r['prediction'].get('label')!=refs[r['case_id']]['reference_label']])
    print(json.dumps(metrics,ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run','report']);p.add_argument('--output',required=True);p.add_argument('--resume',action='store_true');a=p.parse_args()
    if a.action=='run':run(a.output,a.resume)
    else:globals()[a.action](a.output)
