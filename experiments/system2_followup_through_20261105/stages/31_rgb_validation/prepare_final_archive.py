"""Snapshot completed experiment evidence, excluding software/cache payloads."""
import datetime,hashlib,json,os
from pathlib import Path
R=Path('/mnt/data/physical-RSI/result/31_rgb_supplement_20261105')
M=R/'migration';M.mkdir(exist_ok=True)
def read(p):return json.loads(p.read_text())
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
assert read(R/'native-campaign/status.json')['state']=='diagnostic_matrix_completed'
assert read(R/'analysis/matrix-analysis.json')['qualified_cases']==35
assert read(R/'analysis/independent-validation.json')['state']=='passed'
assert (R/'analysis/REPORT.txt').is_file()
cohort={}
for p in sorted((M/'manifests').glob('*.json')):
    d=read(p);assert d['valid_native_cases']==5
    for row in d['files']:assert row['path'] not in cohort;cohort[row['path']]=row
assert len(list((M/'manifests').glob('*.json')))==7
dirs=['analysis','environment','resource-verification','native-preparation','rgb-smoke','protocol','native-campaign']
selected=[];symlinks=[]
for name in dirs:
    for p in sorted((R/name).rglob('*')):
        rel=str(p.relative_to(R))
        if p.is_symlink():symlinks.append(dict(path=rel,target=os.readlink(p),archived_as='metadata only'));continue
        if not p.is_file() or '__pycache__' in p.parts or p.suffix=='.pyc' or p.name=='controller.lock':continue
        if rel.startswith('native-campaign/runs/'):assert rel in cohort;continue
        selected.append(p)
for p in sorted(R.iterdir()):
    if p.is_file() and (p.suffix in ['.py','.log'] or p.name in ['resource-source-sha256.json','transfer-source-inventory.json','RESULT_README.txt','REPRODUCE.txt']):selected.append(p)
selected.extend(sorted((M/'manifests').glob('*.json')))
selected.extend(p for p in M.iterdir() if p.is_file() and p.name in ['transport-recovery.json','cohort-transfer-log.json'])
scope=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_root=str(R),
  destination='/mnt/data/joey_tr/physical-RSI/result/31_system2_rgb_validation/20261105_v1',
  include='All35 native receipts,7 valid cohort outputs,105 original videos,30 saved-candidate execution traces,all candidate sources/harnesses, excluded deployment attempt, frozen protocol, reports/figures/keyframes, reference contracts,resource/version checks, relevant preparation logs/scripts',
  exclusions=['Installed Python/IsaacSim environments','Released weights and complete simulation assets already indexed by frozen hash manifests','Download parts/cache and transport/network benchmark binary payloads','Repeated historical reference trees','Mutable continuation files and empty controller lock; immutable completion snapshot retained'],
  omitted_symlinks=symlinks,source_to_archive='Relative paths under source root are preserved; external referenced primitive scenes are copied with analysis/reference-path-map.json',
  lab_writes='Only the authorized project result subtree',new_paid_api_calls=0,new_paid_cost_usd=0)
(M/'archive-scope.json').write_text(json.dumps(scope,ensure_ascii=False,indent=2)+'\n');selected.append(M/'archive-scope.json')
rows=list(cohort.values());cache={}
for p in sorted(set(selected)):
    s=p.stat();key=(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)
    digest=cache.setdefault(key,sha(p))
    assert p.stat().st_mtime_ns==s.st_mtime_ns,'Source changed during snapshot'
    rows.append(dict(path=str(p.relative_to(R)),bytes=s.st_size,sha256=digest))
assert len(rows)==len({x['path'] for x in rows})
manifest=dict(schema='physicalrsi.rgb-supplement.archive/v1',utc=scope['utc'],files=sorted(rows,key=lambda x:x['path']),file_count=len(rows),logical_bytes=sum(x['bytes'] for x in rows),valid_native_cases=35,videos=105,source_root=str(R),destination=scope['destination'])
(M/'source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
transfer=sorted({str(p.relative_to(R)) for p in selected}|{'migration/source-manifest.json'})
assert all('\n' not in s and not s.startswith('/') and '..' not in Path(s).parts for s in transfer)
(M/'metadata-transfer-list.txt').write_text('\n'.join(transfer)+'\n')
print(json.dumps(dict(manifest_sha256=sha(M/'source-manifest.json'),file_count=len(rows),logical_bytes=manifest['logical_bytes'],metadata_files=len(transfer),omitted_symlinks=len(symlinks))))
