"""Seal completed evidence and source closure for a verified lab archive."""
import datetime,hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
O=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
summary=read(O/'FINAL_SUMMARY.json');assert summary['state']=='completed'
closure={};count=0;videos=0
for stage in summary['stage_accounting']:
    root=O/stage['phase'];d=read(root/'analysis/summary.json');assert d['state']=='verified'
    campaign=read(root/'native-campaign/campaign.json');count+=d['valid_native_episodes']
    videos+=len(list((root/'native-campaign/runs').rglob('*.mp4')))
    for entry in campaign['entries']:
        cfg=read(Path(entry['runtime']))
        for inventory in [cfg.get('files',{}),cfg.get('policy_files',{}),cfg.get('policy_spec',{}).get('files',{})]:
            for name,expected in inventory.items():
                if name in closure:
                    assert closure[name]['sha256']==expected;continue
                source=Path(name);assert sha(source)==expected
                row=dict(source=name,sha256=expected,bytes=source.stat().st_size)
                if source.is_relative_to(O):row['archive']=str(source.relative_to(O))
                elif source.stat().st_size<=50*1024*1024:
                    target=O/'source-closure/objects'/expected/source.name;target.parent.mkdir(parents=True,exist_ok=True)
                    if not target.exists():shutil.copy2(source,target)
                    assert sha(target)==expected;row['archive']=str(target.relative_to(O))
                else:row['reference_only']='Pre-existing large dependency; content hash retained, no new experiment output omitted.'
                closure[name]=row
assert count==summary['actual_native_episodes'] and videos==summary['actual_videos']==3*count
(O/'source-closure').mkdir(exist_ok=True);(O/'source-closure/path-map.json').write_text(json.dumps(list(closure.values()),indent=2)+'\n')
subprocess.run([sys.executable,'-B',str(O/'check_evidence_security.py')],check=True)
M=O/'migration';M.mkdir(exist_ok=True);assert not (M/'source-manifest.json').exists()
files=[];links=[];cache={}
for p in sorted(O.rglob('*')):
    if p.is_symlink():links.append(dict(path=str(p.relative_to(O)),target=os.readlink(p)));continue
    if not p.is_file() or p.name.endswith('.lock') or p.name=='CONTINUATION.json' or '__pycache__' in p.parts:continue
    if p.name in ['seal.log','finalization.log']:continue  # Active process logs copied separately after closure.
    st=p.stat();key=(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns)
    if key not in cache:cache[key]=sha(p)
    assert st.st_mtime_ns==p.stat().st_mtime_ns
    files.append(dict(path=str(p.relative_to(O)),bytes=st.st_size,sha256=cache[key]))
manifest=dict(schema='physicalrsi.multitask.archive/v1',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=files,file_count=len(files),logical_bytes=sum(x['bytes'] for x in files),native_cases=count,videos=videos,excluded_symlinks=links,source_root=str(O),destination='/mnt/data/joey_tr/physical-RSI/result/43_system2_multitask/20261108_v1/native-validation')
(M/'source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(dict(state='snapshot_ready',files=len(files),bytes=manifest['logical_bytes'],native_cases=count,videos=videos,sha256=sha(M/'source-manifest.json'))))
