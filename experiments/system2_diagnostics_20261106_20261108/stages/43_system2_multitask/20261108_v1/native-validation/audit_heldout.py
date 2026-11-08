"""Geometry overlap audit after selection; never choose using heldout outcomes."""
import hashlib,json,sys
from pathlib import Path
O=Path(__file__).resolve().parent;task=sys.argv[1]
def read(p):return json.loads(p.read_text())
def digest(d):return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def geometry(p):
    d=read(p);return digest({k:d.get(k) for k in ['Rigid','Geometry','Clutter','Articulated','Table','Ground','Room']})
selected=read(O/'selection'/f'{task}.json');assert selected['frozen_at'] and not selected['heldout_seen']
root=O/'layouts'/task/'heldout';cases=read(root/'cases.json');new=[geometry(root/r['file']) for r in cases];assert len(set(new))==len(new)==5
prior=[];missing=[]
for p in O.parent.rglob('campaign.json'):
    if 'native-campaign' not in p.parts or p.is_relative_to(O/(task+'-heldout')):continue
    try:d=read(p)
    except (OSError,ValueError):continue
    for row in d.get('cases',[]):
        if row.get('task')!=task:continue
        q=Path(d['layout_root'])/row['file']
        if q.is_file():prior.append(dict(path=str(q),geometry_sha256=geometry(q)))
        else:missing.append(str(q))
old={r['geometry_sha256'] for r in prior};assert not old.intersection(new),'Heldout duplicates previous available geometry'
result=dict(state='passed',task=task,new_geometry_sha256=new,prior_unique_geometries=len(old),missing_prior_references=sorted(set(missing)),sources=prior,scope='Fresh same-sampler layouts; no identical geometry among available prior native campaigns. Not a new-object-category or official benchmark distribution claim. Unavailable prior references remain unknown.')
(root/'overlap-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='sources'}))
