"""Portable, read-only archive verification. Does not run policies or use a GPU/API.

Usage: python3 audit_archive.py /path/to/20261105_v1
"""
import hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[1] if len(sys.argv)>1 else Path(__file__).resolve().parent).resolve()
manifest=json.loads((root/'migration/source-manifest.json').read_text())
cache={};errors=[]
for row in manifest['files']:
    p=root/row['path']
    if not p.resolve().is_relative_to(root) or p.is_symlink() or not p.is_file():errors.append(row['path']);continue
    s=p.stat();key=(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)
    if key not in cache:
        h=hashlib.sha256()
        with p.open('rb') as stream:
            for b in iter(lambda:stream.read(1024*1024),b''):h.update(b)
        cache[key]=h.hexdigest()
    if s.st_size!=row['bytes'] or cache[key]!=row['sha256']:errors.append(row['path'])
assert not errors,dict(mismatches=len(errors),sample=errors[:10])
d=json.loads((root/'analysis/matrix-analysis.json').read_text())
assert d['complete'] and d['qualified_cases']==35
for row in d['episodes']:
    receipt=json.loads((root/row['receipt']).read_text())
    raw=json.loads((root/row['result_file']).read_text())['details'][str(row['layout_id'])]
    assert receipt['natural_terminal'] and receipt['native_exit_code']==0
    assert receipt['success']==raw['success']==row['success']
    assert receipt['episode_score']==raw['score']==row['normalized_score']
    assert receipt['layout_sha256']==row['layout_sha256']
assert len(d['videos'])==105 and all((root/v['file']).is_file() for v in d['videos'])
print(json.dumps(dict(state='passed',files=len(manifest['files']),native_cases=35,videos=105,source_manifest_sha256=hashlib.sha256((root/'migration/source-manifest.json').read_bytes()).hexdigest(),scope='Portable integrity and raw-result consistency only; no new native execution, no rerun of original privileged runtime validation'),indent=2))
