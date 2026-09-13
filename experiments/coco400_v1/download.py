"""Download official COCO archives with resumable ranges; extract with CRC checks."""
import concurrent.futures as cf
import hashlib
import json
import os
import time
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path('datasets/coco2014')
ARCHIVES = {
    'val2014.zip': 'https://s3.amazonaws.com/images.cocodataset.org/zips/val2014.zip',
    'annotations_trainval2014.zip': 'https://s3.amazonaws.com/images.cocodataset.org/annotations/annotations_trainval2014.zip',
}
CHUNK = 32 * 1024 * 1024


def checksum(path, algorithm='sha256'):
    h=hashlib.new(algorithm)
    with path.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()


def download(name,url):
    out=ROOT/'archives'/name; parts=ROOT/'downloads'/name
    parts.mkdir(parents=True,exist_ok=True);out.parent.mkdir(parents=True,exist_ok=True)
    with urllib.request.urlopen(urllib.request.Request(url,method='HEAD'),timeout=45) as r:
        total=int(r.headers['Content-Length']);etag=r.headers.get('ETag','').strip('"')
    meta={'url':url,'bytes':total,'etag':etag,'chunk_bytes':CHUNK}
    meta_path=parts/'source.json'
    if meta_path.exists():assert json.loads(meta_path.read_text())==meta,'remote_archive_changed'
    else:meta_path.write_text(json.dumps(meta),encoding='utf-8')
    count=(total+CHUNK-1)//CHUNK
    if not out.exists():
        def block(i):
            begin=i*CHUNK;end=min(total,begin+CHUNK)-1;size=end-begin+1
            path=parts/f'{i:04d}.part'
            if path.exists() and path.stat().st_size==size:return i,size,True
            for attempt in range(5):
                try:
                    req=urllib.request.Request(url,headers={'Range':f'bytes={begin}-{end}','User-Agent':'COCO400-research-download/1.0'})
                    with urllib.request.urlopen(req,timeout=90) as response:
                        assert response.status==206
                        assert response.headers.get('Content-Range')==f'bytes {begin}-{end}/{total}'
                        with path.open('wb') as f:
                            for b in iter(lambda:response.read(1024*1024),b''):f.write(b)
                    assert path.stat().st_size==size
                    return i,size,False
                except Exception:
                    if attempt==4:raise
                    time.sleep(min(2**attempt,8))
        complete=0;started=time.time()
        with cf.ThreadPoolExecutor(max_workers=4) as pool:
            for future in cf.as_completed([pool.submit(block,i) for i in range(count)]):
                i,n,reused=future.result();complete+=n
                print(json.dumps({'archive':name,'downloaded_bytes':complete,'total_bytes':total,'percent':round(100*complete/total,2),'elapsed_s':round(time.time()-started),'resumed_block':reused}),flush=True)
        temp=out.with_suffix('.zip.assembling')
        with temp.open('wb') as target:
            for i in range(count):
                with (parts/f'{i:04d}.part').open('rb') as source:
                    for b in iter(lambda:source.read(4*1024*1024),b''):target.write(b)
        assert temp.stat().st_size==total;os.replace(temp,out)
    assert out.stat().st_size==total
    if '-' not in etag:assert checksum(out,'md5')==etag
    archive_sha=checksum(out)
    print(json.dumps({'archive':name,'download_complete':True,'sha256':archive_sha}),flush=True)
    extracted=0;dest=ROOT.resolve()
    with zipfile.ZipFile(out) as z:
        for entry in z.infolist():
            target=(dest/entry.filename).resolve()
            assert target.is_relative_to(dest),'unsafe_zip_path'
            if entry.is_dir():target.mkdir(parents=True,exist_ok=True);continue
            target.parent.mkdir(parents=True,exist_ok=True)
            # Read through ZipExtFile so every member's CRC is checked.
            with z.open(entry) as source,target.open('wb') as output:
                for b in iter(lambda:source.read(1024*1024),b''):output.write(b)
            assert target.stat().st_size==entry.file_size
            extracted+=1
            if extracted%5000==0:print(json.dumps({'archive':name,'extracted_files':extracted}),flush=True)
    record={**meta,'sha256':archive_sha,'crc_checked_extracted_files':extracted,'archive_path':str(out.resolve())}
    (ROOT/(name+'.verified.json')).write_text(json.dumps(record,indent=2),encoding='utf-8')
    print(json.dumps({'archive':name,'complete':True,'extracted_files':extracted}),flush=True)
    return record


if __name__=='__main__':
    ROOT.mkdir(parents=True,exist_ok=True)
    with cf.ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda item:download(*item),ARCHIVES.items()))
    (ROOT/'download_manifest.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
