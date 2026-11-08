"""Seal completed stage records; never modify original native evidence."""
from pathlib import Path
import json,hashlib,datetime,os,sys
L=Path(sys.argv[1]).resolve();assert L.is_relative_to(Path('/mnt/data/joey_tr/physical-RSI/result'))
def read(p):return json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
s=read(L/'FINAL_SUMMARY.json');assert s['state']=='completed'
N=L/'native-validation';v=read(N/'migration/ARCHIVE_VERIFIED.json');assert v['state']=='verified'
assert v['native_cases']==s['accounting']['new_native_cases'] and v['videos']==s['accounting']['new_raw_videos']
assert read(N/'analysis/independent-validation.json')['state']=='passed'
manifest=N/'migration/source-manifest.json';assert sha(manifest)==v['manifest_sha256']
assert not (L/'EVIDENCE_INDEX.json').exists(),'Already sealed'
files=[];links=[]
for p in sorted(L.rglob('*')):
 rel=p.relative_to(L)
 if rel.is_relative_to(Path('native-validation')) or any(x in rel.parts for x in ['__pycache__','analysis-cache','tmp','scratch','cache']):continue
 if p.name in ['CONTINUATION.txt','CONTINUATION.json','coordination-status.json','controller.lock','EVIDENCE_INDEX.json']:continue
 if p.is_symlink():links.append(dict(path=str(rel),target=os.readlink(p)))
 elif p.is_file():files.append(dict(path=str(rel),bytes=p.stat().st_size,sha256=sha(p)))
index=dict(schema='physicalrsi.stage-evidence-index/v1',state='sealed',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),accounting=s['accounting'],main_report='REPORT.txt',main_summary='FINAL_SUMMARY.json',native_archive=dict(root='native-validation',source_manifest='native-validation/migration/source-manifest.json',manifest_sha256=v['manifest_sha256'],files=v['verified_files'],logical_bytes=v['logical_bytes'],native_cases=v['native_cases'],videos=v['videos']),derived_files=files,derived_file_count=len(files),symlinks=links,exclusions=['Already verified native files referenced by manifest; no resnapshot.','Mutable continuation and caches excluded.'])
(L/'EVIDENCE_INDEX.json').write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(state='sealed',root=str(L),native_cases=v['native_cases'],videos=v['videos'],derived_files=len(files))))
