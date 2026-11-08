"""Transfer a fresh local-relay archive by verified files in bounded batches."""
import argparse, datetime, hashlib, json, shlex, subprocess, sys, threading, time
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('--record-directory',type=Path,default=Path(__file__).resolve().parent);args=parser.parse_args()
H=args.record_directory.resolve();sys.path.insert(0,str(H.parent/'rgb_supplement_20261105'))
from remote import LAB,CLOUD
original=json.loads((H/'return-status.json').read_text());C=original['source'];D=original['destination'];L=str(Path(D).parent);S=D+'.incoming'
assert C.startswith('/mnt/data/physical-RSI/result/') and D.startswith('/mnt/data/joey_tr/physical-RSI/result/')
recovery=H/'transfer-recovery';recovery.mkdir(exist_ok=False)
for name in ['return-status.json','completion-status.json','finalization-status.json']:
    p=H/name
    if p.exists():(recovery/name).write_bytes(p.read_bytes())
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def call(host,code,sudo=False,data=None,timeout=120):
    r=subprocess.run(host+[('sudo -n ' if sudo else '')+'python3 -B -c '+shlex.quote(code)],input=data,capture_output=True,timeout=timeout)
    if r.returncode:raise RuntimeError(r.stderr.decode(errors='replace')[-1500:])
    return r.stdout
raw=subprocess.run(CLOUD+['sudo -n cat '+shlex.quote(C+'/migration/source-manifest.json')],capture_output=True,check=True,timeout=60).stdout
assert hashlib.sha256(raw).hexdigest()==original['manifest_sha256']
(recovery/'source-manifest.json').write_bytes(raw);manifest=json.loads(raw);rows=manifest['files']
assert len(rows)==original['files']
init=f'''from pathlib import Path
import sys,json,hashlib
S=Path({S!r});D=Path({D!r});assert S.is_dir() and not D.exists()
b=sys.stdin.buffer.read();assert hashlib.sha256(b).hexdigest()=={original['manifest_sha256']!r}
p=S/'migration/source-manifest.json';p.parent.mkdir(exist_ok=True)
if p.exists():assert p.read_bytes()==b
else:p.write_bytes(b)
print(json.dumps(dict(manifest_saved=True)))'''
call(LAB,init,data=raw)
audit=f'''from pathlib import Path
import datetime,hashlib,json,sys
S=Path({S!r});L=Path({L!r});rows=json.load(sys.stdin);missing=[];bad=[];verified=0;cache={{}}
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
for r in rows:
 p=S/r['path'];assert p.resolve().is_relative_to(S.resolve()) and not p.is_symlink()
 good=False
 if p.is_file():
  st=p.stat();key=(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns)
  if key not in cache:cache[key]=sha(p)
  good=st.st_size==r['bytes'] and cache[key]==r['sha256']
  if not good:
   t=L/'transfer-recovery/quarantined'/r['path'];t.parent.mkdir(parents=True,exist_ok=True)
   if t.exists():t=t.with_name(t.name+'.'+datetime.datetime.now().strftime('%H%M%S%f'))
   bad.append(dict(path=r['path'],bytes=st.st_size,sha256=cache[key],preserved=str(t.relative_to(L))))
   p.rename(t)
 if good:verified+=1
 else:missing.append(r)
print(json.dumps(dict(verified=verified,missing=missing,quarantined=bad)))'''
def inspect(subset):return json.loads(call(LAB,audit,data=json.dumps(subset).encode(),timeout=180))
initial=inspect(rows);(recovery/'initial-audit.json').write_text(json.dumps(initial,indent=2)+'\n')
print(json.dumps(dict(state='resume_audited',verified_files=initial['verified'],missing_files=len(initial['missing']),missing_bytes=sum(r['bytes'] for r in initial['missing']),quarantined=len(initial['quarantined']))),flush=True)
pending=initial['missing'];batch_number=0;records=[]
while pending:
    batch=[];size=0
    while pending and (not batch or (size+pending[0]['bytes']<=64*1024*1024 and len(batch)<800)):
        r=pending.pop(0);batch.append(r);size+=r['bytes']
    batch_number+=1
    for attempt in [1,2]:
        names=b''.join(r['path'].encode()+b'\0' for r in batch)
        assert all(not Path(r['path']).is_absolute() and '..' not in Path(r['path']).parts for r in batch)
        source='sudo -n tar -C '+shlex.quote(C)+' --no-recursion --null -cf - -T -'
        dest='tar -xf - --no-same-owner --warning=no-timestamp -C '+shlex.quote(S)
        began=time.monotonic()
        with (recovery/f'batch{batch_number:03}-attempt{attempt}-source.log').open('wb') as se,(recovery/f'batch{batch_number:03}-attempt{attempt}-destination.log').open('wb') as de:
            src=subprocess.Popen(CLOUD+[source],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=se)
            dst=subprocess.Popen(LAB+[dest],stdin=src.stdout,stdout=de,stderr=de);src.stdout.close()
            errors=[]
            def feed():
                try:src.stdin.write(names);src.stdin.close()
                except (BrokenPipeError,OSError) as exc:errors.append(type(exc).__name__)
            thread=threading.Thread(target=feed);thread.start()
            try:dc=dst.wait(timeout=100);sc=src.wait(timeout=10)
            except subprocess.TimeoutExpired:
                src.terminate();dst.terminate();sc=src.wait(timeout=10);dc=dst.wait(timeout=10)
            thread.join(timeout=10)
        checked=inspect(batch)
        record=dict(batch=batch_number,attempt=attempt,files=len(batch),bytes=size,source_exit=sc,destination_exit=dc,elapsed_s=time.monotonic()-began,missing_after=len(checked['missing']),quarantined=checked['quarantined'],writer_errors=errors)
        records.append(record);(recovery/'batches.json').write_text(json.dumps(records,indent=2)+'\n');print(json.dumps(record),flush=True)
        if not checked['missing']:break
        if attempt==2:raise RuntimeError('Repeated batch failure; retain all verified partial data')
        batch=checked['missing'];size=sum(r['bytes'] for r in batch)
final=inspect(rows);assert not final['missing'];(recovery/'final-audit.json').write_text(json.dumps(final,indent=2)+'\n')
finalize=f'''from pathlib import Path
import datetime,json,hashlib
S=Path({S!r});D=Path({D!r});assert not D.exists();p=S/'migration/source-manifest.json';assert hashlib.sha256(p.read_bytes()).hexdigest()=={original['manifest_sha256']!r}
m=json.loads(p.read_text());assert len(list((S/'native-campaign/runs').rglob('*.mp4')))==m['videos'];assert json.loads((S/'analysis/independent-validation.json').read_text())['state']=='passed'
v=dict(state='verified',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_root={C!r},destination={D!r},verified_files=len(m['files']),logical_bytes=m['logical_bytes'],manifest_sha256={original['manifest_sha256']!r},native_cases=m['native_cases'],videos=m['videos'],new_api_calls=0,lab_gpu_used=False,transfer_verified_in_batches=True)
(S/'migration/ARCHIVE_VERIFIED.json').write_text(json.dumps(v,indent=2)+'\\n');S.rename(D);print(json.dumps(v))'''
verified=json.loads(call(LAB,finalize))
payload=json.dumps(dict(transfer_mode='Fresh bounded-batch relay; no initial full-stream transfer attempted.',source_manifest_sha256=original['manifest_sha256'],initial_verified_files=initial['verified'],initial_quarantined=initial['quarantined'],batches=records,final_verification=verified),indent=2).encode()
call(LAB,f"from pathlib import Path;import sys,json;p=Path({L!r})/'transfer-recovery';p.mkdir(exist_ok=True);(p/'recovery-report.json').write_bytes(sys.stdin.buffer.read());print(json.dumps(dict(saved=True)))",data=payload)
call(CLOUD,f"from pathlib import Path;import sys,json;p=Path({C!r})/'migration/LAB_ARCHIVE_VERIFIED.json';assert not p.exists();p.write_bytes(sys.stdin.buffer.read());print(json.dumps(dict(saved=True)))",True,json.dumps(verified,indent=2).encode())
original.update(state='verified',completed_utc=utc(),verification=verified,recovery='transfer-recovery/batches.json')
(H/'return-status.json').write_text(json.dumps(original,indent=2)+'\n')
(H/'completion-status.json').write_text(json.dumps(dict(stage='native_archive_verified',updated_utc=utc(),archive=original,verified_without_native_rerun=True,finalization='Run final analysis after verified archive'),indent=2)+'\n')
print(json.dumps(dict(state='native_archive_verified',verification=verified)),flush=True)
