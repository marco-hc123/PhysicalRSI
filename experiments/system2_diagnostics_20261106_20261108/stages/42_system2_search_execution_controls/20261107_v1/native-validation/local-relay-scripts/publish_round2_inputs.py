"""Relay frozen round2 inputs via this laptop; publish control file LAST."""
import base64,hashlib,json
from remote_ops import H,C,L,LAB,CLOUD,call
rows=json.loads(call(CLOUD,f'''from pathlib import Path
import json,base64,hashlib
r=Path({C!r});control=json.loads((r/'round2-generation.json').read_text())
names=[x['file'] for x in control['requests']]+['execution-final.json','round2-plan.json','round2-generation.json']
print(json.dumps([dict(path=n,sha256=hashlib.sha256((r/n).read_bytes()).hexdigest(),content=base64.b64encode((r/n).read_bytes()).decode()) for n in names]))
''',True))
for row in rows:
 p=H/'round2-inputs'/row['path'];p.parent.mkdir(parents=True,exist_ok=True);b=base64.b64decode(row['content']);assert hashlib.sha256(b).hexdigest()==row['sha256']
 if p.exists():assert p.read_bytes()==b
 else:p.write_bytes(b)
print(call(LAB,f'''from pathlib import Path
import sys,json,base64,hashlib,os
r=Path({L!r});rows=json.load(sys.stdin)
status=json.loads((r/'generation-status.json').read_text())
assert status['state']=='waiting_for_batch' and status['batch']=='round2',status
pid=status['pid'];cmd=Path('/proc/'+str(pid)+'/cmdline').read_bytes();assert str(r/'run_generation.py').encode() in cmd
assert len(json.loads((r/'ledger.json').read_text()))==5
assert rows[-1]['path']=='round2-generation.json'
for row in rows:
 p=r/row['path'];assert p.resolve().is_relative_to(r.resolve());b=base64.b64decode(row['content']);assert hashlib.sha256(b).hexdigest()==row['sha256'];p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==b
 else:
  t=p.with_suffix(p.suffix+'.relay-tmp');t.write_bytes(b);t.replace(p)
print(json.dumps(dict(state='round2_inputs_relayed',files=len(rows),api_worker_pid=pid)))
''',False,json.dumps(rows)))
