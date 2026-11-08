"""Resume a sealed archive, preserving source hardlinks across bounded batches."""
import datetime,hashlib,json,os,shlex,subprocess,sys,threading,time
from pathlib import Path
from remote_ops import H,C,L,LAB,CLOUD,call
D=L+'/native-validation';S=D+'.incoming';M=json.loads((H/'source-manifest.json').read_text());rows=M['files']
digest=hashlib.sha256((H/'source-manifest.json').read_bytes()).hexdigest()
Q=H/'transfer-hardlink-resume';Q.mkdir(exist_ok=False)
def status(state,**extra):
    v=dict(state=state,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**extra)
    (Q/'status.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v),flush=True)
status('source_metadata')
meta=json.loads(call(CLOUD,f'''from pathlib import Path
import json,os,stat,hashlib
r=Path({C!r});p=r/'migration/source-manifest.json';assert hashlib.sha256(p.read_bytes()).hexdigest()=={digest!r};m=json.loads(p.read_text());out=[]
for x in m['files']:
 p=r/x['path'];s=p.stat();assert p.is_file() and not p.is_symlink() and s.st_size==x['bytes'];out.append([s.st_dev,s.st_ino,stat.S_IMODE(s.st_mode),s.st_mtime_ns])
print(json.dumps(out))''',True,timeout=120))
assert len(meta)==len(rows);(Q/'source-metadata.json').write_text(json.dumps(meta)+'\n')
groups={}
for i,x in enumerate(meta):groups.setdefault(tuple(x[:2]),[]).append(i)
for ids in groups.values():
    assert len({(rows[i]['sha256'],rows[i]['bytes'],tuple(meta[i][2:])) for i in ids})==1
status('initial_audit',files=len(rows),source_inode_groups=len(groups),source_unique_inode_bytes=sum(rows[x[0]]['bytes'] for x in groups.values()))
audit=f'''from pathlib import Path
import hashlib,json,sys,datetime
r=Path({S!r});L=Path({L!r});assert r.is_dir() and not Path({D!r}).exists();m=json.loads((r/'migration/source-manifest.json').read_text());wanted=json.load(sys.stdin);verified=[];bad=[];cache={{}}
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
for i in wanted:
 x=m['files'][i];p=r/x['path'];assert p.resolve().is_relative_to(r.resolve()) and not p.is_symlink()
 if not p.exists():continue
 s=p.stat();k=(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)
 if k not in cache:cache[k]=sha(p)
 if s.st_size==x['bytes'] and cache[k]==x['sha256']:verified.append(i)
 else:
  q=L/'transfer-recovery/quarantined-hardlink-resume'/x['path'];q.parent.mkdir(parents=True,exist_ok=True)
  if q.exists():q=q.with_name(q.name+'.'+datetime.datetime.now().strftime('%H%M%S%f'))
  p.rename(q);bad.append(dict(index=i,preserved=str(q)))
print(json.dumps(dict(verified=verified,quarantined=bad)))'''
def inspect(ids):return json.loads(call(LAB,audit,payload=json.dumps(ids),timeout=180))
first=inspect(list(range(len(rows))));(Q/'initial-audit.json').write_text(json.dumps(first,indent=2)+'\n');verified=set(first['verified'])
canonical={};needed=[]
for key,ids in groups.items():
    chosen=next((i for i in ids if i in verified),ids[0]);canonical[key]=chosen
    if chosen not in verified:needed.append(chosen)
plan=dict(initial_verified_files=len(verified),unique_files_to_transfer=len(needed),unique_bytes_to_transfer=sum(rows[i]['bytes'] for i in needed),groups=[dict(canonical=canonical[k],indices=v) for k,v in groups.items()],source_manifest_sha256=digest,scope='Preserve original source inode hardlinks, not content-only deduplication. All file paths and source contents retained; source modes and mtimes restored. Completed original streams were reconciled before restart.')
(Q/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');status('transfer',**{k:plan[k] for k in ['initial_verified_files','unique_files_to_transfer','unique_bytes_to_transfer']},verified_new_unique_bytes=0)
batches=[];done_bytes=0;number=0
while needed:
    batch=[];size=0
    while needed and (not batch or (size+rows[needed[0]]['bytes']<=64*1024*1024 and len(batch)<800)):
        i=needed.pop(0);batch.append(i);size+=rows[i]['bytes']
    number+=1
    for attempt in [1,2]:
        names=b''.join(rows[i]['path'].encode()+b'\0' for i in batch)
        source='sudo -n tar -C '+shlex.quote(C)+" --use-compress-program='gzip -1' --no-recursion --null -cf - -T -"
        dest='tar -xzf - --no-same-owner --warning=no-timestamp -C '+shlex.quote(S)
        t=time.monotonic()
        with (Q/f'batch{number:03}-attempt{attempt}-source.log').open('wb') as se,(Q/f'batch{number:03}-attempt{attempt}-destination.log').open('wb') as de:
            src=subprocess.Popen(CLOUD+[source],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=se)
            dst=subprocess.Popen(LAB+[dest],stdin=src.stdout,stdout=de,stderr=de);src.stdout.close();errors=[]
            def feed():
                try:src.stdin.write(names);src.stdin.close()
                except (OSError,BrokenPipeError) as e:errors.append(type(e).__name__)
            th=threading.Thread(target=feed);th.start()
            try:dc=dst.wait(timeout=180);sc=src.wait(timeout=15)
            except subprocess.TimeoutExpired:
                src.terminate();dst.terminate();sc=src.wait(timeout=15);dc=dst.wait(timeout=15)
            th.join(timeout=15)
        result=inspect(batch);good=set(result['verified']);missing=[i for i in batch if i not in good]
        record=dict(batch=number,attempt=attempt,indices=batch,logical_bytes=sum(rows[i]['bytes'] for i in batch),elapsed_s=time.monotonic()-t,source_exit=sc,destination_exit=dc,missing_after=len(missing),quarantined=result['quarantined'],writer_errors=errors)
        batches.append(record);(Q/'batches.json').write_text(json.dumps(batches,indent=2)+'\n')
        done_bytes+=sum(rows[i]['bytes'] for i in good if i not in verified);verified.update(good)
        status('transfer',verified_new_unique_bytes=done_bytes,unique_bytes_to_transfer=plan['unique_bytes_to_transfer'],batch=number,missing_after=len(missing))
        if not missing:break
        if attempt==2:raise RuntimeError('Repeated compressed batch failure; preserve all verified partial files')
        batch=missing
status('restore_source_hardlinks',source_inode_groups=len(groups),verified_new_unique_bytes=done_bytes)
payload=dict(metadata=meta,groups=plan['groups'])
restore=f'''from pathlib import Path
import os,sys,json,hashlib
r=Path({S!r});v=json.load(sys.stdin);m=json.loads((r/'migration/source-manifest.json').read_text());count=0
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
for g in v['groups']:
 i=g['canonical'];x=m['files'][i];p=r/x['path'];assert p.is_file() and sha(p)==x['sha256'];mode,mtime=v['metadata'][i][2:];os.chmod(p,mode);os.utime(p,ns=(mtime,mtime))
 for j in g['indices']:
  y=m['files'][j];q=r/y['path'];assert q.resolve().is_relative_to(r.resolve()) and not q.is_symlink()
  if q.exists():assert q.stat().st_size==y['bytes'] and sha(q)==y['sha256'];os.chmod(q,mode);os.utime(q,ns=(mtime,mtime))
  else:q.parent.mkdir(parents=True,exist_ok=True);os.link(p,q);count+=1
print(json.dumps(dict(restored_hardlink_paths=count)))'''
restored=json.loads(call(LAB,restore,payload=json.dumps(payload),timeout=300));(Q/'hardlinks-restored.json').write_text(json.dumps(restored,indent=2)+'\n')
status('final_verification',**restored)
final=inspect(list(range(len(rows))));assert len(final['verified'])==len(rows) and not final['quarantined'];(Q/'final-audit.json').write_text(json.dumps(final,indent=2)+'\n')
finalize=f'''from pathlib import Path
import json,hashlib,datetime
S=Path({S!r});D=Path({D!r});assert not D.exists();p=S/'migration/source-manifest.json';assert hashlib.sha256(p.read_bytes()).hexdigest()=={digest!r};m=json.loads(p.read_text());summary=json.loads((S/'FINAL_SUMMARY.json').read_text());assert summary['state']=='completed';assert sum(len(list((S/x/'native-campaign/runs').rglob('*.mp4'))) for x in summary['completed_native_phases'])==m['videos']
v=dict(state='verified',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_root={C!r},destination={D!r},verified_files=len(m['files']),logical_bytes=m['logical_bytes'],manifest_sha256={digest!r},native_cases=m['native_cases'],videos=m['videos'],new_api_calls=summary['paid_api_requests'],lab_gpu_used=False,transfer_verified_in_batches=True,source_hardlinks_restored=True)
(S/'migration/ARCHIVE_VERIFIED.json').write_text(json.dumps(v,indent=2)+chr(10));S.rename(D);print(json.dumps(v))'''
proof=json.loads(call(LAB,finalize));(Q/'ARCHIVE_VERIFIED.json').write_text(json.dumps(proof,indent=2)+'\n')
call(CLOUD,f"from pathlib import Path;import sys;p=Path({C!r})/'migration/LAB_ARCHIVE_VERIFIED.json';assert not p.exists();p.write_text(sys.stdin.read());print('archive proof saved')",True,json.dumps(proof,indent=2)+'\n')
for name in ['FINAL_SUMMARY.json','REPORT.txt','REPRODUCE.txt','protocol.json','selection-final.json','stage-accounting.csv']:
    raw=call(LAB,f"from pathlib import Path;print((Path({D!r})/{name!r}).read_text(),end='')")
    (H/name).write_text(raw)
    call(LAB,f"from pathlib import Path;import sys;p=Path({L!r})/{name!r};b=sys.stdin.read();assert not p.exists() or p.read_text()==b;p.write_text(b);print('saved')",payload=raw)
original=json.loads((H/'return-status.json').read_text());original.update(state='verified',verification=proof,recovery='transfer-hardlink-resume/',completed_utc=proof['utc']);(H/'return-status.json').write_text(json.dumps(original,indent=2)+'\n')
status('verified',verification=proof)
