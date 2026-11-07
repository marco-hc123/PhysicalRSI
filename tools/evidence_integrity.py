"""Verify current bytes or an explicitly archived historical manifest version."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
def manifest_bytes(row):
    expected=row['sha256'];size=int(row['bytes']);path=(ROOT/row['path']).resolve()
    if not path.is_relative_to(ROOT):raise ValueError('Manifest path escapes repository')
    if path.is_file():
        data=path.read_bytes()
        if len(data)==size and hashlib.sha256(data).hexdigest()==expected:return data
    archive=json.loads((ROOT/'provenance/manifest_archive/index.json').read_text())
    key=row['path']+'@'+expected
    if key not in archive:raise ValueError('Unarchived manifest mismatch: '+row['path'])
    entry=archive[key];saved=(ROOT/entry['archived_path']).resolve()
    if not saved.is_relative_to(ROOT):raise ValueError('Archive path escapes repository')
    data=saved.read_bytes()
    if len(data)!=size or hashlib.sha256(data).hexdigest()!=expected:raise ValueError('Historical archive hash mismatch: '+row['path'])
    return data
