"""Restore missing scene data from pinned Git and public LFS, verifying source SHA.

Only project-local destination writes. Lab source manifest is the authority;
public files are never accepted merely because filenames/versions appear equal.
"""
from pathlib import Path
import concurrent.futures
import datetime
import fcntl
import hashlib
import json
import os
import subprocess
import time
import urllib.parse
import urllib.request

R=Path('/mnt/data/physical-RSI')
O=R/'result/31_rgb_supplement_20261105/asset-source-recovery'
O.mkdir(exist_ok=True)
LOCK=(O/'recovery.lock').open('a');fcntl.flock(LOCK,fcntl.LOCK_EX|fcntl.LOCK_NB)
G=R/'cache/pinned-asset-metadata/robodojo-attempt2.git'
ROOT=R/'reference/data/simulation_assets/robodojo-complete-source'
CACHE=R/'cache/scene-lfs-verified';CACHE.mkdir(exist_ok=True)
COMMIT='35efbc7dedfdbeeb6e95fb749bd885d73d483e41'
assert subprocess.check_output(['git','--git-dir='+str(G),'rev-parse',COMMIT+'^{commit}'],text=True).strip()==COMMIT
source=json.loads((R/'result/31_rgb_supplement_20261105/resource-source-sha256.json').read_text())['groups']['scene_assets']
run=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
started=time.monotonic()

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()

def status(state,**extra):
    d=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),state=state,pid=os.getpid(),
           dataset_commit=COMMIT,trust='Read-only original lab source file SHA256 manifest',
           elapsed_s=time.monotonic()-started,lab_writes=False,gpu_used=False,api_calls=0,**extra)
    p=O/'status.json';q=p.with_suffix('.tmp');q.write_text(json.dumps(d,indent=2));q.replace(p)

def place(p,target,mode):
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists() or target.is_symlink():
        rel=target.relative_to(ROOT);backup=R/'cache/scene-recovery-preserved'/run/rel
        backup.parent.mkdir(parents=True,exist_ok=True);target.rename(backup)
    os.link(p,target)
    target.chmod(mode)

status('auditing_received_files')
pending=[];reused=0;digests={}
for e in source['files']:
    p=ROOT/e['path'];s=p.stat() if p.is_file() else None;digest=None
    if s and s.st_size==e['bytes']:
        key=(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)
        if key not in digests:digests[key]=sha(p)
        digest=digests[key]
    if digest==e['sha256']:reused+=1
    else:pending.append(e)

tree=subprocess.check_output(['git','--git-dir='+str(G),'ls-tree','-rz','--full-tree',COMMIT])
entries={}
for row in tree.split(b'\0'):
    if not row:continue
    meta,path=row.split(b'\t',1);mode,kind,oid=meta.split()
    if kind==b'blob':entries[path.decode()]=(int(mode,8)&0o777,oid.decode())
oids=list(dict.fromkeys(entries[e['path']][1] for e in pending if e['path'] in entries))
raw=subprocess.run(['git','--git-dir='+str(G),'cat-file','--batch'],input=('\n'.join(oids)+'\n').encode(),capture_output=True,check=True).stdout
blobs={};offset=0
for oid in oids:
    end=raw.index(b'\n',offset);header=raw[offset:end].split();assert header[0].decode()==oid and header[1]==b'blob'
    size=int(header[2]);offset=end+1;blobs[oid]=raw[offset:offset+size];offset+=size+1

objects={};metadata=[];unsupported=[]
for e in pending:
    if e['path'] not in entries:
        unsupported.append(dict(path=e['path'],reason='not_in_pinned_git_tree',bytes=e['bytes']));continue
    mode,oid=entries[e['path']];blob=blobs[oid]
    if len(blob)==e['bytes'] and hashlib.sha256(blob).hexdigest()==e['sha256']:
        metadata.append((e,blob,mode));continue
    try:
        lines=blob.decode().splitlines()
        assert lines[0]=='version https://git-lfs.github.com/spec/v1'
        lfs_oid=next(x[11:] for x in lines if x.startswith('oid sha256:'))
        size=int(next(x[5:] for x in lines if x.startswith('size ')))
        assert lfs_oid==e['sha256'] and size==e['bytes']
    except (UnicodeDecodeError,AssertionError,StopIteration,ValueError):
        unsupported.append(dict(path=e['path'],reason='upstream_bytes_differ_from_source_manifest',bytes=e['bytes']));continue
    objects.setdefault(lfs_oid,dict(oid=lfs_oid,size=size,targets=[]))['targets'].append(dict(path=e['path'],mode=mode))

(O/'recovery-plan.json').write_text(json.dumps(dict(reused_source_files=reused,git_blob_files=len(metadata),
    lfs_objects=list(objects.values()),unsupported=unsupported),indent=2))
status('restoring_git_blobs',reused_source_files=reused,git_blob_files=len(metadata),lfs_objects=len(objects),unsupported=unsupported)
for e,blob,mode in metadata:
    cached=CACHE/e['sha256']
    if not cached.exists():
        q=cached.with_suffix('.git.tmp');q.write_bytes(blob);q.replace(cached)
    assert cached.stat().st_size==e['bytes'] and sha(cached)==e['sha256']
    place(cached,ROOT/e['path'],mode)

def fetch(obj):
    dst=CACHE/obj['oid'];tmp=dst.with_suffix('.partial')
    if dst.exists():
        assert dst.stat().st_size==obj['size'] and sha(dst)==obj['oid']
        return dict(oid=obj['oid'],ok=True,cached=True,bytes=obj['size'])
    attempts=[]
    for attempt in range(1,4):
        try:
            req=urllib.request.Request('https://hf-mirror.com/datasets/RoboDojo-Benchmark/RoboDojo.git/info/lfs/objects/batch',
                data=json.dumps(dict(operation='download',transfers=['basic'],objects=[dict(oid=obj['oid'],size=obj['size'])])).encode(),
                headers={'Content-Type':'application/vnd.git-lfs+json','Accept':'application/vnd.git-lfs+json'})
            with urllib.request.urlopen(req,timeout=30) as response:batch=json.load(response)
            item=batch['objects'][0]
            if 'error' in item:raise RuntimeError('LFS object unavailable')
            download=item['actions']['download'];u=urllib.parse.urlsplit(download['href'])
            assert u.scheme=='https'
            if u.hostname=='us.aws.cdn.hf-mirror.org':u=u._replace(netloc='us.aws.cdn.hf.co')
            url=urllib.parse.urlunsplit(u)
            config='url = '+json.dumps(url)+'\n'
            for key,value in download.get('header',{}).items():
                assert '\n' not in key+value and '\r' not in key+value
                config+='header = '+json.dumps(key+': '+value)+'\n'
            with (O/(obj['oid']+'.curl.log')).open('a') as log:
                p=subprocess.run(['curl','-4','-L','--proto','=https','--proto-redir','=https','--config','-',
                    '--fail','-sS','--connect-timeout','15','--max-time','600','--speed-time','60','--speed-limit','16384',
                    '--continue-at','-','--output',str(tmp)],input=config,text=True,stdout=log,stderr=subprocess.STDOUT)
            size=tmp.stat().st_size if tmp.exists() else 0
            attempts.append(dict(attempt=attempt,curl_exit=p.returncode,bytes=size))
            if size==obj['size']:
                actual=sha(tmp)
                if actual!=obj['oid']:return dict(oid=obj['oid'],ok=False,reason='sha256_mismatch',actual_sha256=actual,attempts=attempts)
                tmp.replace(dst);return dict(oid=obj['oid'],ok=True,bytes=size,attempts=attempts)
        except Exception as exc:attempts.append(dict(attempt=attempt,error_type=type(exc).__name__))
    return dict(oid=obj['oid'],ok=False,reason='bounded_attempts_exhausted',attempts=attempts)

results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    futures={pool.submit(fetch,obj):obj for obj in objects.values()}
    while futures:
        done,_=concurrent.futures.wait(futures,timeout=10,return_when=concurrent.futures.FIRST_COMPLETED)
        for f in done:
            obj=futures.pop(f)
            try:row=f.result()
            except Exception as exc:row=dict(oid=obj['oid'],ok=False,error_type=type(exc).__name__)
            results.append(row)
            if row['ok']:
                for target in obj['targets']:place(CACHE/obj['oid'],ROOT/target['path'],target['mode'])
            print(json.dumps(row),flush=True)
        status('restoring_lfs_objects',reused_source_files=reused,git_blob_files=len(metadata),
               lfs_objects_total=len(objects),lfs_objects_verified=sum(x['ok'] for x in results),
               lfs_bytes_verified=sum(x.get('bytes',0) for x in results if x['ok']),unsupported=unsupported,
               failed_objects=[x for x in results if not x['ok']])
(O/'lfs-results.json').write_text(json.dumps(results,indent=2))
if unsupported or not all(x['ok'] for x in results):
    status('needs_review',unsupported=unsupported,failed_objects=[x for x in results if not x['ok']]);raise RuntimeError('Unverified scene files remain; no invented replacements')
status('verifying_complete_source_manifest',reused_source_files=reused,git_blob_files=len(metadata),lfs_objects_verified=len(objects))
python=R/'envs/python/cpython-3.11.17-linux-x86_64-gnu/bin/python3'
with (O/'final-source-verification.log').open('w') as log:
    p=subprocess.run([str(python),str(O.parent/'finalize_resources.py'),'scene_assets'],stdout=log,stderr=subprocess.STDOUT)
assert p.returncode==0,'Final source hash comparison failed; inspect preserved receipt'
status('all_scene_source_hashes_verified',reused_source_files=reused,git_blob_files=len(metadata),lfs_objects_verified=len(objects),file_count=len(source['files']))
