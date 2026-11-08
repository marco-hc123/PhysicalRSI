"""Freeze both cohorts and their analysis; preserve referenced evidence."""
import datetime,hashlib,json,os,shutil
from pathlib import Path
O=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
assert read(O/'route-status.json')['state']=='native_and_validation_completed'
assert read(O/'analysis/independent-validation.json')['state']=='passed'
assert read(O/'reference/analysis/independent-validation.json')['state']=='passed'
assert read(O/'chain-analysis.json')['state']=='completed'
pid=read(O/'launch.json')['pid'];cmd=Path(f'/proc/{pid}/cmdline')
assert not cmd.exists() or str(O/'run_route.py').encode() not in cmd.read_bytes()
A=O/'analysis';mapping=[]
def copy(source,target):
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():assert sha(source)==sha(target)
    else:shutil.copy2(source,target)
    mapping.append(dict(source=str(source),archive=str(target.relative_to(O)),sha256=sha(target)))
campaign=read(O/'native-campaign/campaign.json')
for case in campaign['cases']:copy(Path(campaign['layout_root'])/case['file'],A/'reference-layouts'/case['file'])
for actor in read(A/'matrix-analysis.json')['actors']:
    process=O/actor['process_record'];root=process.parents[3]
    for p in (root/'primitive-service').rglob('*'):
        if p.is_file():copy(p,A/'referenced-primitive-services'/actor['condition']/actor['actor_episode_id']/p.relative_to(root/'primitive-service'))
spec=read(O/'reference/reference-spec.json');base=Path(next(p for p in spec['files'] if p.endswith('/model.py'))).parent
for name,wanted in spec['files'].items():
    source=Path(name);assert sha(source)==wanted
    if source.is_relative_to(base):copy(source,A/'released-controller'/source.relative_to(base))
    else:assert source.is_relative_to(O),'Unexpected external reference'
(A/'reference-path-map.json').write_text(json.dumps(mapping,indent=2)+'\n')
raw_videos=list((O/'native-campaign/runs').rglob('*.mp4'))+list((O/'reference/native').rglob('*.mp4'));assert len(raw_videos)==30
M=O/'migration';M.mkdir(exist_ok=True);assert not (M/'source-manifest.json').exists()
destination='/mnt/data/joey_tr/physical-RSI/result/41_system2_skill_chain_floor/20261107_v1/native-validation'
scope=dict(native_cases=10,videos=30,api_calls=0,lab_gpu_used=False,source_root=str(O),destination=destination,scope='Both bounded capability cohorts, original video, actor traces, post-hoc state, frozen source, and analysis. No environment, weights, private keys or API secrets.',auxiliary_video_files=sum(1 for p in O.rglob('*.mp4'))-30)
(M/'archive-scope.json').write_text(json.dumps(scope,indent=2)+'\n')
files=[];excluded=[];cache={}
for p in sorted(O.rglob('*')):
    if p.is_symlink():excluded.append(dict(path=str(p.relative_to(O)),reason='symlink; referenced primitive evidence copied separately',target=os.readlink(p)));continue
    if not p.is_file():continue
    if p.name.endswith('.lock') or p.name=='CONTINUATION.json' or '__pycache__' in p.parts:continue
    st=p.stat();key=(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns)
    if key not in cache:cache[key]=sha(p)
    assert st.st_mtime_ns==p.stat().st_mtime_ns
    files.append(dict(path=str(p.relative_to(O)),bytes=st.st_size,sha256=cache[key]))
manifest=dict(schema='physicalrsi.skill-floor-archive/v1',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=files,file_count=len(files),logical_bytes=sum(x['bytes'] for x in files),native_cases=10,videos=30,excluded_symlinks=excluded,source_root=str(O),destination=destination)
(M/'source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(dict(state='snapshot_ready',files=len(files),logical_bytes=manifest['logical_bytes'],manifest_sha256=sha(M/'source-manifest.json'),destination=destination)))
