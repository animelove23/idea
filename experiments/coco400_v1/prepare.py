"""Select 400 paired greedy captions without consulting outcomes; bind verified images."""
import argparse
import copy
import json
import random
from pathlib import Path
from PIL import Image
from analysis_skeleton.common import read_json,read_jsonl,write_json,write_jsonl,sha

ROOT=Path('outputs/coco400_final_v1')
DATA=Path('datasets/coco2014')
SEED=20260912


def select():
    ROOT.mkdir(parents=True,exist_ok=True)
    if (ROOT/'selection.json').exists():raise ValueError('selection_already_frozen')
    base=Path('实验结果/exp_results')
    sources={side:next((base/folder/'llava-1.5').glob('*.jsonl')) for side,folder in
             [('original','chair_llava_baseline'),('steer','vista_chair_greedy')]}
    data={side:read_jsonl(path) for side,path in sources.items()}
    indexed={side:{str(r['image_id']):r['caption'] for r in rows} for side,rows in data.items()}
    assert all(len(data[s])==len(indexed[s])==500 for s in data)
    assert set(indexed['original'])==set(indexed['steer'])
    shots={str(r['image_id']) for r in read_jsonl('analysis_skeleton/shots/verify.jsonl')}
    eligible=sorted(set(indexed['original'])-shots,key=int)
    ids=random.Random(SEED).sample(eligible,400)
    dev={str(r['image_id']) for r in read_jsonl('outputs/legacy_visual_full_flash_v1/references.jsonl')}
    dev|={str(r['image_id']) for r in read_jsonl('analysis_skeleton/fixtures/expansion20/pairs.jsonl')}
    dev|={str(int(p.stem.rsplit('_',1)[-1])) for p in (base/'caption_review_20/images').glob('*.jpg')}
    pairs=[]
    for iid in ids:
        pairs.append({'pair_id':iid,'image_id':iid,
            'original':{'caption_id':iid+'_original','text':indexed['original'][iid]},
            'steer':{'caption_id':iid+'_steer','text':indexed['steer'][iid]},
            'stop_reason':'unknown','split':'exploratory_existing_500_greedy',
            'known_development_overlap':iid in dev})
    selection={'seed':SEED,'source_pairs':500,'eligible_pairs':len(eligible),'selected_pairs':400,
        'image_ids':ids,'excluded_visual_shot_image_ids':sorted(shots,key=int),
        'known_development_overlap_ids':sorted(set(ids)&dev,key=int),
        'known_development_overlap_count':len(set(ids)&dev),
        'selection_rule':'uniform_without_replacement_from_sorted_paired_ids_excluding_visual_shot_images',
        'outcome_labels_used_for_selection':False,'independent_holdout':False,
        'sources':{s:{'path':str(p.resolve()),'sha256':sha(p)} for s,p in sources.items()},
        'generation_configuration_evidence':'filenames_only; baseline_vs_VISTA; greedy; seed1994; max_new_tokens512; lambda0.17; loglayer25,30; logalpha0.3'}
    write_jsonl(ROOT/'selected_text_pairs.jsonl',pairs);write_json(ROOT/'selection.json',selection)
    write_json(ROOT/'profile.json',read_json('outputs/final_v1_release/profile.json'))
    write_json(ROOT/'protocol.json',{'sample_count':400,'caption_count':800,'model':'deepseek-flash',
        'workers':8,'shots':{'decompose':8,'align':8,'verify':6},'calls_per_unique_visual_claim':1,
        'decomposition_calls_planned':800,'alignment_calls_maximum':400,'visual_calls':'one per generated unique claim',
        'framework_profile':'Final v1 fixed owner+typed','api_destination':'https://api.deepseek.com',
        'api_query_excludes':'COCO annotations, CHAIR reference fields, old reference labels and audit conclusions',
        'references_used_as_visual_gold':False,'automatic_retries_on_model_failures':0,
        'selection_sha256':sha(ROOT/'selection.json'),'source_code_frozen':True,
        'execution':'8 independent pair pipelines; within each pair original frozen module order',
        'observation':'length-stratified S/H change matrices, E/A components, POS profiles, explicit unresolved cases',
        'not_a_new_model_generation_run':True})
    print({k:selection[k] for k in ['source_pairs','eligible_pairs','selected_pairs','known_development_overlap_count']})


def bind():
    assert (DATA/'download_manifest.json').is_file(),'download_and_extraction_not_complete'
    if (ROOT/'pairs.jsonl').exists():raise ValueError('bound_pairs_already_exist')
    annotations=read_json(DATA/'annotations/captions_val2014.json')
    val_ids={str(r['id']) for r in annotations['images']}
    assert len(val_ids)==40504
    pairs=read_jsonl(ROOT/'selected_text_pairs.jsonl')
    assert len(pairs)==400
    for p in pairs:
        iid=p['image_id'];assert iid in val_ids
        path=(DATA/'val2014'/f'COCO_val2014_{int(iid):012d}.jpg').resolve()
        with Image.open(path) as im:im.verify()
        p.update(image_path=str(path),image_sha256=sha(path),image_status='readable',pair_status='paired')
    assert len({p['image_sha256'] for p in pairs})==400
    shots={r['input']['image_sha256'] for r in read_jsonl('analysis_skeleton/shots/verify.jsonl')}
    assert not shots&{p['image_sha256'] for p in pairs}
    write_jsonl(ROOT/'pairs.jsonl',pairs)
    write_json(ROOT/'input_validation.json',{'pairs':400,'captions':800,'unique_images':400,
        'all_in_val2014':True,'all_images_decoded':True,'visual_shot_overlap':0,
        'dataset_validation_images':len(val_ids),'pairs_sha256':sha(ROOT/'pairs.jsonl'),
        'download_manifest_sha256':sha(DATA/'download_manifest.json')})
    print({'bound_pairs':400,'images_readable':400,'visual_shot_overlap':0})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['select','bind']);a=p.parse_args();globals()[a.phase]()
