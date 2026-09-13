"""Project existing visual labels without generating or changing any judgments."""
import argparse
from collections import Counter
from pathlib import Path
from .common import read_json,read_jsonl,write_json,write_jsonl,sha

LABELS={'true':'supported','hallucination':'hallucinated','uncertain':'uncertain'}

def export(output):
    out=Path(output)
    if out.exists() and any(out.iterdir()):raise ValueError('use_new_output_directory')
    source=Path('outputs/visual40_v1');alignments={str(r['pair_id']):r for r in read_jsonl(source/'alignment.jsonl')}
    records=[];excluded=[];files={str(source/'alignment.jsonl'):sha(source/'alignment.jsonl')};images=set()
    for lp in sorted((source/'labels').glob('*.json')):
        labels=read_json(lp);pp=source/'pairs'/lp.name;pair=read_json(pp);image_id=str(pair['image_id'])
        files.update({str(lp):sha(lp),str(pp):sha(pp)});images.add(image_id)
        image=Path(pair['image_path']);assert sha(image)==labels['image_sha256']
        for side in ('original','steer'):
            facts=pair[side]['facts'];ids=[f['id'] for f in facts];assert len(ids)==len(set(ids))
            mapping={}
            for label,new_label in LABELS.items():
                for fid in labels[side][label]:
                    assert fid in ids and fid not in mapping
                    mapping[fid]=(label,new_label)
            assert set(mapping)==set(ids),f'incomplete legacy labels: {image_id}/{side}'
            for fact in facts:
                key=f'{image_id}:{side}:{fact["id"]}'
                keep=fact['type']=='entity' or (fact['type']=='attribute' and fact['category']!='counting')
                if not keep:
                    excluded.append({'case_id':key,'type':fact['type'],'category':fact['category'],'reason':'count_excluded' if fact['category']=='counting' else 'outside_entity_attribute_scope'})
                    continue
                edges=[edge for edge in alignments[image_id]['fact_alignment'] if fact['id'] in edge.get(side+'_fact_ids',[])]
                records.append({'case_id':key,'image_id':image_id,'side':side,'source_fact_id':fact['id'],
                    'semantic_type':fact['type'],'legacy_category':fact['category'],
                    'input':{'image_path':str(image.resolve()),'image_sha256':labels['image_sha256'],'statement':fact['fact'],
                        'entity_context':{'source_window':fact['source'],'context_role':'Original text evidence only; not visual truth.'}},
                    'legacy_label':mapping[fact['id']][0],'reference_label':mapping[fact['id']][1],
                    'reference_status':'reused_legacy_visual_annotation','annotator':labels.get('annotator'),
                    'human_reviewed':labels.get('human_reviewed',False),'image_review_notes':labels.get('notes',''),
                    'source_fact':fact,'source_caption_id':pair[side]['id'],'source_label_file':str(lp),
                    'source_pair_file':str(pp),'alignment_records':edges,
                    'contract_status':'legacy_claim_unchanged_current_scope_not_yet_adjudicated',
                    'attribute_slot_review_required':fact['type']=='attribute' and fact['category'] in ('attribute','state'),
                    'warning':'The label belongs to the complete original claim. Do not transfer it to a rewritten or split proposition without review.'})
    assert len({r['case_id'] for r in records})==len(records)
    manual_path=Path('实验结果/exp_results/caption_review_20/manual_reviews.json');manual=read_json(manual_path)
    current={str(r['image_id']) for r in read_jsonl('analysis_skeleton/fixtures/expansion20/pairs.jsonl')}
    summary={'legacy_fact_labeled_images':len(images),'legacy_text_review_images':len(manual),'overlapping_images':sorted(images&set(manual)),
        'unique_images_in_two_collections':len(images|set(manual)),'current_fixed_test_images':len(current),
        'current_test_images_in_legacy_fact_set':len(images&current),'current_test_images_in_text_review_set':len(set(manual)&current),
        'retained_rows':len(records),'by_type':dict(Counter(r['semantic_type'] for r in records)),
        'by_category':dict(Counter(r['legacy_category'] for r in records)),'by_label':dict(Counter(r['reference_label'] for r in records)),
        'excluded_rows':len(excluded),'excluded_by_category':dict(Counter(r['category'] for r in excluded)),
        'attribute_slot_review_required':sum(r['attribute_slot_review_required'] for r in records),
        'new_api_calls':0,'new_visual_annotations':0,'labels_changed':0,
        'not_yet_current_m5_evaluation':'Original complete claims retained; exact current-schema projection and parent binding require checking. Text-only reviews were not promoted to fact labels.'}
    out.mkdir(parents=True,exist_ok=True)
    write_jsonl(out/'all_object_attribute_labels.jsonl',records);write_jsonl(out/'excluded_rows.jsonl',excluded)
    write_json(out/'summary.json',summary);write_json(out/'provenance.json',{'source_hashes':files,'manual_review_source':str(manual_path),'manual_review_sha256':sha(manual_path),'export_code_sha256':sha(__file__)})
    print(summary)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();export(a.output)
