"""Index verified native archives and hash new derived evidence after all work stops."""
import datetime,hashlib,json,os
from pathlib import Path
L=Path('/mnt/data/joey_tr/physical-RSI/result/32_system2_lift_gate_diagnosis/20261106_v1')
def read(p):return json.loads(Path(p).read_text())
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
s=read(L/'FINAL_SUMMARY.json');assert s['state']=='completed' and s['accounting']['new_native_cases']==20
resources=read(L/'completion-resource-check.json')
assert not resources['lab']['owned_experiment_processes'] and not resources['execution_server']['owned_experiment_processes']
for sub in ['planning-recovery','planning-return','perception-replay']:assert read(L/sub/'status.json')['state']=='completed'
native=[]
for relative in ['native-validation','retreat-followup/native-validation']:
    N=L/relative;v=read(N/'migration/ARCHIVE_VERIFIED.json');m=N/'migration/source-manifest.json'
    assert v['state']=='verified' and v['manifest_sha256']==sha(m)
    assert read(N/'analysis/independent-validation.json')['state']=='passed'
    native.append(dict(root=relative,verification=relative+'/migration/ARCHIVE_VERIFIED.json',source_manifest=relative+'/migration/source-manifest.json',manifest_sha256=sha(m),verified_files=v['verified_files'],logical_bytes=v['logical_bytes'],videos=v['videos'],native_cases=v['native_cases'],verification_scope='All payload hashes were checked during atomic archive return; this seal checks the verified manifest identity without rerunning simulation or redundantly rehashing its full payload.'))
files=[];symlinks=[]
excluded_names={'EVIDENCE_INDEX.json','CONTINUATION.txt','local-coordination-status.json'}
for p in sorted(L.rglob('*')):
    rel=p.relative_to(L)
    if any(rel.is_relative_to(Path(x['root'])) for x in native):continue
    if 'cache' in rel.parts or 'tmp' in rel.parts or '__pycache__' in rel.parts:continue
    if p.name in excluded_names:continue
    if p.is_symlink():symlinks.append(dict(path=str(rel),target=os.readlink(p)));continue
    if p.is_file():files.append(dict(path=str(rel),bytes=p.stat().st_size,sha256=sha(p)))
index=dict(schema='physicalrsi.stage-evidence-index/v1',state='sealed',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    root=str(L),accounting=s['accounting'],native_archives=native,derived_files=files,derived_file_count=len(files),derived_logical_bytes=sum(x['bytes'] for x in files),symlinks=symlinks,
    exclusions=['Installed model/environment/scene assets are referenced by frozen provenance, not duplicated here.','Runtime compilation/download cache and temporary directories excluded from evidence hashes but left on disk.','Mutable continuation/coordination records excluded.','Earlier35 native episodes are historical references, not new cases.'],
    main_report='REPORT.txt',main_summary='FINAL_SUMMARY.json',all_experiments_stopped=True)
(L/'EVIDENCE_INDEX.json').write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(state='sealed',native_cases=sum(x['native_cases'] for x in native),native_videos=sum(x['videos'] for x in native),native_files=sum(x['verified_files'] for x in native),derived_files=len(files),index=str(L/'EVIDENCE_INDEX.json'))))
