"""Verify/hydrate pinned public layouts and exact transitive object directories."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib
R=Path('/mnt/data/physical-RSI');O=Path(sys.argv[1]);A=R/'assets/robodojo-complete-source'
ns={'__name__':'subset_library'};sys.argv=['hydrate',str(O/'task-assets')]
text=(R/'result/cloud_download_subset.py').read_text();exec(compile(text.split('\ntry:\n    layouts=')[0],'subset_library','exec'),ns)
inv,stage=ns['inventory'],ns['stage'];protocol=json.loads((O/'protocol.json').read_text())
paths=[f'Assets/Eval_Layout/RoboDojo/arx_x5/0/{task}_{i}.json' for task in protocol['tasks'] for i in range(6)]
entries=inv(paths);stage(entries,'layout_metadata')
base=json.loads((A/'Assets/Eval_Layout/RoboDojo/arx_x5/0/classify_objects_0.json').read_text())
prefixes=set()
for path in paths:
 data=json.loads((A/path).read_text())
 for key in ['Room','Table','Ground','Background']:assert data.get(key)==base.get(key),(path,key)
 for section in ['Rigid','Geometry','Articulation','Deformable']:
  for cat,instances in data.get(section,{}).items():
   for obj in instances:
    kind='Clutter' if obj.get('type')=='cluttered' else section
    prefixes.add(f"Assets/Object/RoboDojo/{kind}/{cat}/{int(obj['category_idx']):05d}/")
selected={p for p in ns['blobs'] if any(p.startswith(x) for x in prefixes)}
assert all(any(p.startswith(x) for p in selected) for x in prefixes)
stage(inv(selected),'object_dependencies')
records=list(ns['records'].values())
manifest=dict(verified=True,utc=datetime.now(timezone.utc).isoformat(),layouts=entries,files=records,shared_scene_matches_prior=True)
(O/'task-assets/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(O/'preparation-status.json').write_text(json.dumps(dict(complete=True,stage='complete',verified_files=len(records),verified_bytes=sum(x['size'] for x in records),downloaded_files=sum(x['downloaded'] for x in records)),indent=2)+'\n')
print(json.dumps(dict(complete=True,verified_files=len(records))))
