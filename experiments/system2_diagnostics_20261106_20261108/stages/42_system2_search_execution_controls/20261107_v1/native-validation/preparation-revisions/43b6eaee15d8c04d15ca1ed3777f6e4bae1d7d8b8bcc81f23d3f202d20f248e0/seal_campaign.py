"""Snapshot completed research evidence, resolving external evidence symlinks."""
import datetime,hashlib,json,os,shutil
from pathlib import Path
O=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
summary=read(O/'FINAL_SUMMARY.json');assert summary['state']=='completed'
mapping=[];video_count=0;case_count=0
for phase in summary['completed_native_phases']:
 root=O/phase;assert read(root/'analysis/independent-validation.json')['state']=='passed'
 campaign=read(root/'native-campaign/campaign.json');case_count+=campaign['planned_cases']
 for case in campaign['cases']:
  source=Path(campaign['layout_root'])/case['file'];target=root/'analysis/reference-layouts'/case['file'];target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert sha(source)==sha(target)
  else:shutil.copy2(source,target)
  mapping.append(dict(source=str(source),archive=str(target.relative_to(O)),sha256=sha(target)))
 for actor in read(root/'analysis/matrix-analysis.json')['actors']:
  base=(root/actor['process_record']).parents[3]/'primitive-service'
  for source in base.rglob('*'):
   if not source.is_file():continue
   target=root/'analysis/referenced-primitive-services'/actor['condition']/actor['actor_episode_id']/source.relative_to(base)
   target.parent.mkdir(parents=True,exist_ok=True)
   if target.exists():assert sha(source)==sha(target)
   else:shutil.copy2(source,target)
   mapping.append(dict(source=str(source),archive=str(target.relative_to(O)),sha256=sha(target)))
 video_count+=len(list((root/'native-campaign/runs').rglob('*.mp4')))
assert video_count==3*case_count
(O/'reference-path-map.json').write_text(json.dumps(mapping,indent=2)+'\n')
closure={}
for phase in summary['completed_native_phases']:
 campaign=read(O/phase/'native-campaign/campaign.json')
 for entry in campaign['entries']:
  cfg=read(Path(entry['runtime']))
  for inventory in [cfg.get('files',{}),cfg.get('policy_files',{}),cfg.get('policy_spec',{}).get('files',{})]:
   for name,expected in inventory.items():
    source=Path(name);assert sha(source)==expected
    if name in closure:assert closure[name]['sha256']==expected;continue
    row=dict(source=name,sha256=expected,bytes=source.stat().st_size)
    if source.stat().st_size<=50*1024*1024:
     target=O/'source-closure/objects'/expected/source.name;target.parent.mkdir(parents=True,exist_ok=True)
     if not target.exists():shutil.copy2(source,target)
     assert sha(target)==expected;row['archive']=str(target.relative_to(O))
    else:row['reference_only']='Large installed dependency; original path and verified content hash retained. Not a new experiment output.'
    closure[name]=row
(O/'source-closure').mkdir(exist_ok=True)
(O/'source-closure/path-map.json').write_text(json.dumps(list(closure.values()),indent=2)+'\n')
M=O/'migration';M.mkdir(exist_ok=True);assert not (M/'source-manifest.json').exists()
files=[];symlinks=[];cache={}
for p in sorted(O.rglob('*')):
 if p.is_symlink():symlinks.append(dict(path=str(p.relative_to(O)),target=os.readlink(p)));continue
 if not p.is_file() or p.name.endswith('.lock') or p.name=='CONTINUATION.json' or '__pycache__' in p.parts:continue
 st=p.stat();key=(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns)
 if key not in cache:cache[key]=sha(p)
 assert st.st_mtime_ns==p.stat().st_mtime_ns
 files.append(dict(path=str(p.relative_to(O)),bytes=st.st_size,sha256=cache[key]))
manifest=dict(schema='physicalrsi.search-controls.archive/v1',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=files,file_count=len(files),logical_bytes=sum(x['bytes'] for x in files),native_cases=case_count,videos=video_count,excluded_symlinks=symlinks,source_root=str(O),destination=read(O/'protocol.json')['lab_root']+'/native-validation')
(M/'source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(dict(state='snapshot_ready',files=len(files),bytes=manifest['logical_bytes'],manifest_sha256=sha(M/'source-manifest.json'),native_cases=case_count,videos=video_count)))
