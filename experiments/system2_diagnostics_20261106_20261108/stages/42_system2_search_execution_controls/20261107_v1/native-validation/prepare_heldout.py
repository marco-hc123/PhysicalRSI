"""Generate native-qualified unseen layouts only after strategy selection freezes."""
import datetime,json,sys
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[1]
I=R/'result/25_system2_integration_20261030T050100Z/integration-sources'
sys.path[:0]=[str(I),str(I/'framework-validation-v3')]
from PhysicalRSI_core.infra.storage import atomic_json,read_json,file_digest,digest
from PhysicalRSI_baselines.robodojo.native_runtime import NativeRuntime
selection=read_json(O/'selection-final.json')
assert selection['frozen_at'] and selection['heldout_seen']==False
cfg=read_json(selection['runtime_reference']);runtime=NativeRuntime(cfg)
sys.path.insert(0,str(Path(selection['runtime_reference']).parent.parent/'code'))
out=O/'heldout-layouts';assert not out.exists()
# Audit hashes of all previous native cases without reading evaluation outcomes.
seen=set();provenance=[];geometry_seen=set();geometry_audit=[]
def geometry_identity(path):
 layout=read_json(path)
 return digest({key:layout.get(key) for key in ['Rigid','Geometry','Table','Ground','Room']})
for p in (R/'result').rglob('campaign.json'):
 if 'native-campaign' not in p.parts:continue
 try:d=read_json(p)
 except (ValueError,OSError):continue
 values=[x.get('layout_sha256') for x in d.get('cases',[]) if isinstance(x,dict)]
 if values:
  seen.update(x for x in values if x);provenance.append(dict(path=str(p),sha256=file_digest(p),layout_hashes=values))
  for case in d.get('cases',[]):
   if not isinstance(case,dict) or not case.get('file'):continue
   root=Path(d.get('layout_root','/nonexistent'))
   path=root/case['file'];row=dict(path=str(path),available=path.is_file())
   if path.is_file():
    row['geometry_sha256']=geometry_identity(path);geometry_seen.add(row['geometry_sha256'])
   geometry_audit.append(row)
for p in (R/'result').rglob('cases.json'):
 try:d=read_json(p)
 except (ValueError,OSError):continue
 if isinstance(d,list):
  values=[x.get('layout_sha256') for x in d if isinstance(x,dict)]
  if values:seen.update(x for x in values if x);provenance.append(dict(path=str(p),sha256=file_digest(p),layout_hashes=values))
atomic_json(O/'heldout-prior-layout-audit.json',dict(prior_unique_hashes=len(seen),sources=provenance,geometry_sources=geometry_audit,prior_geometry_hashes=sorted(geometry_seen),unavailable_geometry_references=sum(not x['available'] for x in geometry_audit),scope='Case identities and physical-layout configuration only; no prior outcome selection'))
cases=runtime.cases(tasks=['classify_objects'],count=5,split='validation',output=out,comparison=selection)
assert len(cases)==5 and len({x['layout_sha256'] for x in cases})==5
assert not any(x['layout_sha256'] in seen for x in cases),'Duplicate prior geometry; do not evaluate as unseen'
new_geometry=[geometry_identity(out/x['file']) for x in cases]
assert len(set(new_geometry))==5 and not any(x in geometry_seen for x in new_geometry)
atomic_json(O/'heldout-eligibility.json',dict(state='passed',selection_sha256=file_digest(O/'selection-final.json'),layout_hashes=[x['layout_sha256'] for x in cases],geometry_hashes=new_geometry,prior_unique_hashes=len(seen),prior_geometry_hashes_checked=len(geometry_seen),unavailable_prior_geometry_references=sum(not x['available'] for x in geometry_audit),new_native_initializations=5,new_scored_episodes=0,scope='Fresh layouts generated only after strategy freeze by the same native task generator. No exact matches to available prior layout or geometry identities. This is not a controlled new-category test; object/category overlap must be reported, and unavailable prior references remain an audit limitation.',utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
plan=dict(entries=selection['unique_entries'],cases=cases,layout_root=str(out),selection='Locked strategies; no tuning or selection on heldout results',research_role='Five fresh unseen generated layouts from same task distribution')
atomic_json(O/'heldout-plan.json',plan)
print(json.dumps(dict(heldout_layouts=5,strategies=len(plan['entries']),scored_cases=5*len(plan['entries']))))
