"""Snapshot reference outputs, inputs and complete frozen small code package."""
import json,hashlib,datetime,shutil,os
from pathlib import Path
R=Path(__file__).resolve().parent;M=R/'migration';A=R/'analysis'
def read(p):return json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
assert read(R/'status.json')['state']=='reference_completed';assert read(A/'independent-validation.json')['state']=='passed'
for pid in [read(R/'launch.json')['pid'],read(R/'ready.json')['pid']]:
 p=Path(f'/proc/{pid}/cmdline')
 if p.exists():assert str(R).encode() not in p.read_bytes(),'Owned process remains active'
req=read(R/'request-template.json');mapping=[]
for case in req['layouts']:
 source=Path(req['layout_root'])/case['file'];dest=A/'reference-layouts'/case['file'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest);mapping.append(dict(source=str(source),archive=str(dest.relative_to(R)),sha256=sha(source)))
spec=read(R/'reference-spec.json');root=Path(next(k for k in spec['files'] if k.endswith('/model.py'))).parent
for name,wanted in spec['files'].items():
 source=Path(name);assert sha(source)==wanted;dest=A/'reference-controller'/source.relative_to(root);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
(A/'reference-path-map.json').write_text(json.dumps(mapping,indent=2)+'\n')
M.mkdir(exist_ok=True);assert not (M/'source-manifest.json').exists();files=[];excluded=[]
for p in sorted(R.rglob('*')):
 rel=str(p.relative_to(R))
 if p.is_symlink():raise ValueError('Unexpected symlink '+rel)
 if not p.is_file():continue
 if p.name in ['controller.lock','CONTINUATION.json']:excluded.append(rel);continue
 st=p.stat();digest=sha(p);assert p.stat().st_mtime_ns==st.st_mtime_ns
 files.append(dict(path=rel,bytes=st.st_size,sha256=digest))
scope=dict(native_cases=5,videos=15,new_api_calls=0,source_root=str(R),destination='/mnt/data/joey_tr/physical-RSI/result/37_system2_candidate_capacity/20261107_v1/native-validation',excluded=excluded,note='All new reference results,15original videos,controller trace and code; existing environments/weights referenced.')
p=M/'archive-scope.json';p.write_text(json.dumps(scope,indent=2)+'\n');files.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p)))
m=dict(schema='physicalrsi.native-mechanism-archive/v1',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=files,file_count=len(files),logical_bytes=sum(x['bytes'] for x in files),native_cases=5,videos=15,source_root=str(R),destination=scope['destination'])
(M/'source-manifest.json').write_text(json.dumps(m,indent=2)+'\n');(M/'transfer-list.txt').write_text('\n'.join(x['path'] for x in files)+'\nmigration/source-manifest.json\n');print(json.dumps(dict(state='snapshot_ready',files=len(files),bytes=m['logical_bytes'])))
