"""Snapshot completed native evidence for a portable lab archive; no reruns."""
import datetime
import hashlib
import json
import os
import shutil
from pathlib import Path
R=Path('/mnt/data/physical-RSI/result/34_capability_feedback_20261106')
def read(p):return json.loads(p.read_text())
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
s=read(R/'native-campaign/status.json');N=read(R/'native-campaign/campaign.json')['planned_cases'];assert s['state']=='diagnostic_matrix_completed' and s['completed_cases']==N
assert read(R/'analysis/independent-validation.json')['state']=='passed'
assert read(R/'analysis/matrix-analysis.json')['qualified_cases']==N
pid=read(R/'launch.json')['pid']
if Path(f'/proc/{pid}/cmdline').exists():
    assert str(R/'run_native.py').encode() not in Path(f'/proc/{pid}/cmdline').read_bytes(),'Controller still running'
c=read(R/'native-campaign/campaign.json');a=R/'analysis';mapping=[]
for case in c['cases']:
    source=Path(c['layout_root'])/case['file'];target=a/'reference-layouts'/case['file'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    mapping.append(dict(source=str(source),archive=str(target.relative_to(R)),sha256=sha(source)))
rp=Path(c['runtime']);shutil.copy2(rp,a/'frozen-runtime.json');mapping.append(dict(source=str(rp),archive='analysis/frozen-runtime.json',sha256=sha(rp)))
analysis=read(a/'matrix-analysis.json')
for actor in analysis['actors']:
    process=R/actor['process_record'];root=process.parents[3]
    dest=a/'referenced-primitive-services'/actor['condition']/actor['actor_episode_id']
    for p in sorted((root/'primitive-service').rglob('*')):
        if p.is_file():
            rel=p.relative_to(root/'primitive-service');target=dest/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
            mapping.append(dict(source=str(p),archive=str(target.relative_to(R)),sha256=sha(p)))
(a/'reference-path-map.json').write_text(json.dumps(mapping,indent=2)+'\n')
M=R/'migration';M.mkdir(exist_ok=True)
assert not (M/'source-manifest.json').exists(),'Existing snapshot must be reviewed before resnapshot'
excluded=[];files=[];cache={}
for p in sorted(R.rglob('*')):
    rel=p.relative_to(R)
    if p.is_symlink():excluded.append(dict(path=str(rel),kind='symlink',target=os.readlink(p)));continue
    if not p.is_file():continue
    if p.name in {'CONTINUATION.json','controller.lock'}:excluded.append(dict(path=str(rel),kind='mutable-status-or-lock'));continue
    st=p.stat();key=(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns)
    if key not in cache:cache[key]=sha(p)
    assert p.stat().st_mtime_ns==st.st_mtime_ns
    files.append(dict(path=str(rel),bytes=st.st_size,sha256=cache[key]))
scope=dict(native_cases=N,videos=3*N,new_api_calls=0,installed_environment_or_weights_copied=False,
    excluded=excluded,source_root=str(R),destination='/mnt/data/joey_tr/physical-RSI/result/33_system2_capability_feedback/20261106_v1/native-validation',
    note='Frozen runtime/resource manifests reference existing installation; all new original results, videos and execution evidence included. Absolute primitive-service links represented by copied data and reference-path-map.')
(M/'archive-scope.json').write_text(json.dumps(scope,indent=2)+'\n')
p=M/'archive-scope.json';files.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p)))
manifest=dict(schema='physicalrsi.native-mechanism-archive/v1',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    files=files,file_count=len(files),logical_bytes=sum(x['bytes'] for x in files),native_cases=N,videos=3*N,
    source_root=str(R),destination=scope['destination'])
(M/'source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
paths=[x['path'] for x in files]+['migration/source-manifest.json']
assert len(paths)==len(set(paths))
assert all('\n' not in p and '\r' not in p and not p.startswith('/') and '..' not in Path(p).parts for p in paths)
(M/'transfer-list.txt').write_text('\n'.join(paths)+'\n')
print(json.dumps(dict(state='snapshot_ready',files=len(files),logical_bytes=manifest['logical_bytes'],native_cases=N,videos=3*N,manifest_sha256=sha(M/'source-manifest.json'))))
