"""Seal final derived records plus the already verified native payload manifest."""
import datetime,hashlib,json,os
from pathlib import Path
L=Path('/mnt/data/joey_tr/physical-RSI/result/33_system2_capability_feedback/20261106_v1')
def read(p):return json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
s=read(L/'FINAL_SUMMARY.json');assert s['state']=='completed' and s['accounting']['new_native_cases']==30
resource=read(L/'completion-resource-check.json')
assert not resource['lab']['owned_experiment_processes'] and not resource['execution_server']['owned_experiment_processes']
N=L/'native-validation';v=read(N/'migration/ARCHIVE_VERIFIED.json');manifest=N/'migration/source-manifest.json'
assert v['state']=='verified' and v['native_cases']==30 and v['videos']==90 and sha(manifest)==v['manifest_sha256']
assert read(N/'analysis/independent-validation.json')['state']=='passed'
assert not (L/'EVIDENCE_INDEX.json').exists(),'Do not silently replace a sealed index'
files=[];links=[]
for p in sorted(L.rglob('*')):
 rel=p.relative_to(L)
 if rel.is_relative_to(Path('native-validation')):continue
 if '__pycache__' in rel.parts or 'cache' in rel.parts or 'tmp' in rel.parts:continue
 if p.name in ['CONTINUATION.txt','coordination-status.json','generation.lock','EVIDENCE_INDEX.json']:continue
 if p.is_symlink():links.append(dict(path=str(rel),target=os.readlink(p)));continue
 if p.is_file():files.append(dict(path=str(rel),bytes=p.stat().st_size,sha256=sha(p)))
index=dict(schema='physicalrsi.stage-evidence-index/v1',state='sealed',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),accounting=s['accounting'],
 main_report='REPORT.txt',main_summary='FINAL_SUMMARY.json',
 native_archive=dict(root='native-validation',verification='native-validation/migration/ARCHIVE_VERIFIED.json',source_manifest='native-validation/migration/source-manifest.json',manifest_sha256=sha(manifest),files=v['verified_files'],logical_bytes=v['logical_bytes'],native_cases=30,videos=90),
 derived_file_count=len(files),derived_files=files,symlinks=links,
 exclusions=['Native payload was already fully SHA-verified during atomic return; this seal verifies manifest identity.','Installed environment, weights and assets remain referenced by frozen manifests, not duplicated.','Mutable continuation, coordination, locks and runtime cache are excluded.'],
 all_experiments_stopped=True)
(L/'EVIDENCE_INDEX.json').write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(state='sealed',native_cases=30,videos=90,native_files=v['verified_files'],derived_files=len(files),index=str(L/'EVIDENCE_INDEX.json'))))
