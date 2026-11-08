"""Read immutable generation evidence from lab and relay via the local computer."""
import argparse,base64,json,hashlib,sys
from pathlib import Path
from remote_ops import H,C,L,CLOUD,LAB,call
parser=argparse.ArgumentParser();parser.add_argument('batch',choices=['sampling','round2']);args=parser.parse_args()
batch=args.batch
code=f'''from pathlib import Path
import json,base64
r=Path({L!r});assert (r/{(batch+'-generation-complete.json')!r}).exists()
plan=json.loads((r/{(batch+'-generation.json')!r}).read_text())
names=['ledger.json','generation-status.json',{(batch+'-generation-complete.json')!r},{(batch+'-generation.json')!r},'model-access.json']
for row in plan['requests']:
 names+=[row['file'],'responses/'+row['id']+'.json']
 names+=[str(p.relative_to(r)) for p in (r/'candidates'/row['id']).rglob('*') if p.is_file()]
print(json.dumps([dict(path=n,content=base64.b64encode((r/n).read_bytes()).decode()) for n in names]))
'''
rows=json.loads(call(LAB,code,timeout=120))
for row in rows:
 p=H/'generation-records'/batch/row['path'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(row['content']))
code=f'''from pathlib import Path
import sys,json,base64,hashlib
r=Path({C!r});rows=json.load(sys.stdin)
for row in rows:
 p=r/row['path'];assert p.resolve().is_relative_to(r.resolve());b=base64.b64decode(row['content']);p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists() and p.read_bytes()!=b:
  assert p.name in ['ledger.json','generation-status.json'],'Immutable generation artifact changed'
  prior=r/'generation-snapshots'/{batch!r}/p.name;prior.parent.mkdir(parents=True,exist_ok=True);assert not prior.exists();prior.write_bytes(p.read_bytes())
 p.write_bytes(b);assert hashlib.sha256(p.read_bytes()).hexdigest()==hashlib.sha256(b).hexdigest()
print(json.dumps(dict(state='generation_relay_verified',files=len(rows),batch={batch!r})))
'''
print(call(CLOUD,code,True,json.dumps(rows),timeout=120))
