"""Verified execution-host -> local pipe -> lab migration, never outside project."""
import datetime
import json
from pathlib import Path
import shlex
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'rgb_supplement_20261105'))
from remote import CLOUD,LAB
HERE=Path(__file__).resolve().parent
C='/mnt/data/physical-RSI/result/33_retreat_recovery_20261106'
L='/mnt/data/joey_tr/physical-RSI/result/32_system2_lift_gate_diagnosis/20261106_v1/retreat-followup'
D=L+'/native-validation'
def call(host,script,sudo=False,timeout=60):
    p=subprocess.run(host+[('sudo -n ' if sudo else '')+'python3 -B -c '+shlex.quote(script)],capture_output=True,text=True,timeout=timeout)
    if p.returncode:raise RuntimeError(p.stderr[-2000:])
    return json.loads(p.stdout)
source=call(CLOUD,f'''from pathlib import Path
import json,hashlib
r=Path({C!r});p=r/'migration/source-manifest.json';m=json.loads(p.read_text());print(json.dumps(dict(manifest_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),files=m['file_count'],logical_bytes=m['logical_bytes'])))''',True)
call(LAB,f'''from pathlib import Path
import json
d=Path({D!r});s=Path({(D+'.incoming')!r});assert not d.exists();assert not s.exists(),'Partial transfer requires resume audit';s.mkdir();print(json.dumps({{'staging':str(s)}}))''')
record=dict(state='transferring',started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source=C,destination=D,route='cloud -> local SSH pipe -> lab',**source)
(HERE/'return-status.json').write_text(json.dumps(record,indent=2)+'\n')
with (HERE/'return-source.log').open('wb') as se,(HERE/'return-destination.log').open('wb') as de:
    src=subprocess.Popen(CLOUD+['sudo -n tar -C '+shlex.quote(C)+' --verbatim-files-from --no-recursion -cf - -T '+shlex.quote(C+'/migration/transfer-list.txt')],stdout=subprocess.PIPE,stderr=se)
    dst=subprocess.Popen(LAB+['tar -xf - --no-same-owner -C '+shlex.quote(D+'.incoming')],stdin=src.stdout,stdout=de,stderr=de)
    src.stdout.close();dc=dst.wait();sc=src.wait()
if sc or dc:raise RuntimeError(f'Transfer needs diagnosis: source={sc}, destination={dc}; retain staging')
verified=call(LAB,f'''from pathlib import Path
import datetime,json,hashlib
r=Path({(D+'.incoming')!r});p=r/'migration/source-manifest.json';assert hashlib.sha256(p.read_bytes()).hexdigest()=={source['manifest_sha256']!r};m=json.loads(p.read_text());cache={{}}
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
for row in m['files']:
 p=r/row['path'];assert p.resolve().is_relative_to(r.resolve()) and p.is_file() and not p.is_symlink();s=p.stat();assert s.st_size==row['bytes'];key=(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)
 if key not in cache:cache[key]=sha(p)
 assert cache[key]==row['sha256'],row['path']
assert len(list((r/'native-campaign/runs').rglob('*.mp4')))==30
assert json.loads((r/'analysis/independent-validation.json').read_text())['state']=='passed'
v=dict(state='verified',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_root={C!r},destination={D!r},verified_files=len(m['files']),logical_bytes=m['logical_bytes'],manifest_sha256={source['manifest_sha256']!r},native_cases=10,videos=30,new_api_calls=0,lab_gpu_used=False)
(r/'migration/ARCHIVE_VERIFIED.json').write_text(json.dumps(v,indent=2)+'\\n');r.rename(Path({D!r}));print(json.dumps(v))
''',timeout=240)
record.update(state='verified',completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),verification=verified)
(HERE/'return-status.json').write_text(json.dumps(record,indent=2)+'\n')
call(CLOUD,f'''from pathlib import Path
import json
p=Path({(C+'/migration/LAB_ARCHIVE_VERIFIED.json')!r});p.write_text({json.dumps(verified,indent=2)!r}+'\\n');print(json.dumps({{'saved':True}}))''',True)
print(json.dumps(record))
