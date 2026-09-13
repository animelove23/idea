"""Freeze completed outputs after integrity checks and verify report links."""
import re
from pathlib import Path
from analysis_skeleton.common import read_json,read_jsonl,write_json,sha

ROOT=Path('outputs/coco400_final_v1')


def main():
    assert read_json(ROOT/'observations/integrity.json')['passed']
    assert read_json(ROOT/'run_summary.json')['status']=={'exported':400}
    assert len(read_jsonl(ROOT/'observations/observation_pairs.jsonl'))==400
    assert (ROOT/'observations/case_gallery.html').read_text(encoding='utf-8').count('<article ')==400
    links=0
    for name in ('RESULTS.md','MOTIVATION.md','CASE_REVIEW.md'):
        doc=ROOT/name
        for link in re.findall(r'\]\(([^)]+)\)',doc.read_text(encoding='utf-8')):
            assert (doc.parent/link).resolve().is_file(),(name,link)
            links+=1
    target=ROOT/'result_manifest.json'
    assert not target.exists(),'result_manifest_already_frozen'
    paths=set()
    for base in (ROOT,Path('experiments/coco400_v1')):
        paths.update(p for p in base.rglob('*') if p.is_file() and p!=target and '__pycache__' not in p.parts
            and p.suffix not in ('.tmp','.lock','.pyc'))
    paths.add(Path('datasets/coco2014/download_manifest.json'))
    manifest={'status':'complete_exploratory_automatic_observations','pairs':400,
        'api_calls':5682,'original_framework_unchanged':True,'local_report_links_checked':links,
        'semantic_accuracy_validated':False,'files':{str(p.resolve()):sha(p) for p in sorted(paths)}}
    write_json(target,manifest)
    print({'files_frozen':len(paths),'report_links_checked':links,'result_manifest':str(target.resolve())})


if __name__=='__main__':main()
