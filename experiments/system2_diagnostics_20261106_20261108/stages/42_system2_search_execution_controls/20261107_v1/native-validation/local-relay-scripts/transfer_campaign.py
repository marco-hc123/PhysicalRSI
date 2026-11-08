"""Relay verified evidence through this computer; no lab GPU or system writes."""
import datetime,hashlib,json,subprocess,sys
from pathlib import Path
from remote_ops import H,C,L,CLOUD,LAB,call
raw=call(CLOUD,f"from pathlib import Path;print((Path({C!r})/'migration/source-manifest.json').read_text(),end='')",True,timeout=120)
m=json.loads(raw);digest=hashlib.sha256(raw.encode()).hexdigest();D=L+'/native-validation';S=D+'.incoming'
assert m['destination']==D and m['native_cases']>0 and m['videos']==3*m['native_cases']
(H/'source-manifest.json').write_text(raw)
print(call(LAB,f"from pathlib import Path;import json;L=Path({L!r});S=Path({S!r});D=Path({D!r});assert not D.exists();assert not S.exists();S.mkdir(parents=True);print(json.dumps(dict(destination_created=True)))"))
v=dict(state='prepared_for_batched_relay',source=C,destination=D,files=m['file_count'],logical_bytes=m['logical_bytes'],manifest_sha256=digest,utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
(H/'return-status.json').write_text(json.dumps(v,indent=2)+'\n')
p=subprocess.run([sys.executable,str(H/'batch_archive.py')],cwd=H);assert p.returncode==0,'Preserve partial transfer and diagnose before retry'
for name in ['FINAL_SUMMARY.json','REPORT.txt','protocol.json','selection-final.json','stage-accounting.csv']:
    raw=call(CLOUD,f"from pathlib import Path;print((Path({C!r})/{name!r}).read_text(),end='')",True)
    (H/name).write_text(raw)
    print(call(LAB,f"from pathlib import Path;import sys;p=Path({L!r})/{name!r};b=sys.stdin.read();assert not p.exists() or p.read_text()==b;p.write_text(b);print('saved '+p.name)",payload=raw))
print(json.dumps(dict(state='archived',lab_root=L,lab_gpu_used=False)))
