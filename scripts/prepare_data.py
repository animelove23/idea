"""Bind public COCO files and emit portable pair inputs; no model/network calls."""
import argparse,hashlib,json,shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):return [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()]
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--coco-root',type=Path,default=ROOT/'datasets/coco2014/val2014');args=parser.parse_args()
    source=args.coco_root.resolve()
    if not source.is_dir():raise SystemExit('COCO directory missing; supply --coco-root pointing to val2014.')
    required={}
    for entry in json.loads((ROOT/'assets/verification_images/manifest.json').read_text(encoding='utf-8')):
        if sha(ROOT/entry['path'])!=entry['sha256']:raise ValueError('Bundled fixture image hash mismatch')
    def walk(x):
        if isinstance(x,dict):
            if 'image_path' in x and isinstance(x['image_path'],str) and x['image_path'].startswith('datasets/coco2014/'):
                rel=x['image_path'];expected=x.get('image_sha256')
                if expected and required.get(rel) not in (None,expected):raise ValueError('Conflicting image hashes: '+rel)
                required[rel]=expected or required.get(rel)
            for v in x.values():walk(v)
        elif isinstance(x,list):
            for v in x:walk(v)
    for directory in ['analysis_skeleton','outputs/final_v1_m5']:
        for p in (ROOT/directory).rglob('*.jsonl'):
            walk(rows(p))
    pairs=rows(ROOT/'results/coco400_final_v1/selected_text_pairs.jsonl')
    for pair in pairs:
        rel=f"datasets/coco2014/val2014/COCO_val2014_{int(pair['image_id']):012d}.jpg"
        required.setdefault(rel,None);pair['image_path']=rel
    for rel,expected in required.items():
        src=source/Path(rel).name;dest=ROOT/rel
        if not src.is_file():raise FileNotFoundError(src)
        actual=sha(src)
        if expected and expected!=actual:raise ValueError('Image hash mismatch: '+src.name)
        dest.parent.mkdir(parents=True,exist_ok=True)
        if src!=dest.resolve():shutil.copy2(src,dest)
    for pair in pairs:pair['image_sha256']=sha(ROOT/pair['image_path'])
    out=ROOT/'inputs';out.mkdir(exist_ok=True)
    for name,data in [('coco400_pairs.jsonl',pairs),('sample_pair.jsonl',pairs[:1])]:
        (out/name).write_text(''.join(json.dumps(v,ensure_ascii=False)+'\n' for v in data),encoding='utf-8')
    print(json.dumps({'validated_images':len(required),'pairs':len(pairs),'sample_pairs':1,'model_calls':0}))

if __name__=='__main__':main()
