"""Hydrate only the ten preregistered System 1 reference scenes and dependencies."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path('/mnt/data/physical-RSI')
OUT=Path(sys.argv[1]); SOURCE=ROOT/'assets/robodojo-complete-source'
split=json.loads((ROOT/'result/23_protocol_freeze_20261029T132917Z/data-splits.json').read_text())
text=(ROOT/'result/cloud_download_subset.py').read_text()
namespace={'__name__':'subset_library'}
sys.argv=['hydrate',str(OUT/'task-assets')]
exec(compile(text.split('\ntry:\n    layouts=')[0],'subset_library','exec'),namespace)
inventory,stage,records=namespace['inventory'],namespace['stage'],namespace['records']
refs=split['system1_reference_validation']
entries=inventory([r['path'] for r in refs])
for row in entries:
    registered=next(r for r in refs if r['path']==row['path'])
    assert row['sha256']==registered['content_sha256'] and row['size']==registered['content_bytes']
stage(entries,'reference_layout_metadata')
baseline=json.loads((SOURCE/'Assets/Eval_Layout/RoboDojo/arx_x5/0/classify_objects_0.json').read_text())
prefixes=set();layouts=[]
for row in refs:
    data=json.loads((SOURCE/row['path']).read_text())
    for key in ['Room','Table','Ground','Background']:
        assert data.get(key)==baseline.get(key), 'Unreviewed shared scene dependency: '+key
    for section in ['Rigid','Geometry','Articulation','Deformable']:
        for category,instances in data.get(section,{}).items():
            for obj in instances:
                kind='Clutter' if obj.get('type')=='cluttered' else section
                prefixes.add(f"Assets/Object/RoboDojo/{kind}/{category}/{int(obj['category_idx']):05d}/")
    layouts.append(dict(row,materialized_now=True))
selected={p for p in namespace['blobs'] if any(p.startswith(prefix) for prefix in prefixes)}
assert all(any(p.startswith(prefix) for p in selected) for prefix in prefixes)
stage(inventory(selected),'reference_object_dependencies')
(OUT/'task-assets/manifest.json').write_text(json.dumps(dict(verified=True,layouts=layouts,files=list(records.values())),indent=2)+'\n')
(OUT/'preparation-status.json').write_text(json.dumps(dict(complete=True,stage='complete',
    utc=datetime.now(timezone.utc).isoformat(),verified_files=len(records),
    verified_bytes=sum(r['size'] for r in records.values()),downloaded_files=sum(r['downloaded'] for r in records.values())),indent=2)+'\n')
print(json.dumps(dict(complete=True,verified_files=len(records))))
