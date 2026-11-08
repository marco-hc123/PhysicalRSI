"""Freeze the complete released skill prefix as a descriptive capacity reference."""
import json,hashlib,copy
from pathlib import Path
O=Path(__file__).resolve().parent;D=O/'reference';R=O.parents[1]
P=R/'result/38_candidate_capacity_20261107'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
spec=read(P/'reference-spec.json')
for p,h in spec['files'].items():assert sha(Path(p))==h
spec['name']='released.first_basket_cycle.6bb861ace4b706d9'
for p in [D/'first_cycle.py',D/'reference_service.py']:spec['files'][str(p)]=sha(p)
spec['revision']=hashlib.sha256(json.dumps(spec['files'],sort_keys=True).encode()).hexdigest()
dump(D/'reference-spec.json',spec)
cfg=read(O/'runtimes/single_cycle.json');dump(D/'inherited-runtime.json',cfg)
dump(D/'environment.json',{k:cfg[k] for k in ['simulator_python','policy_python','policy_environment','simulator_environment']})
protocol=dict(parent_protocol_sha256=sha(O/'protocol.json'),code_sha256={p.name:sha(p) for p in D.glob('*.py')},planned_cases=5,limits=['Descriptive richer-API reference, not an equal-interface comparison.','First basket transfer return ends controller; internal retries and handoffs retained.','A transfer return and full task success are distinct.'],api_calls=0)
dump(D/'protocol.json',protocol)
req=read(P/'request-template.json');req['expert']=dict(name=spec['name'],revision=spec['revision']);req['harness_sha256']=sha(D/'protocol.json')
campaign=read(O/'native-campaign/campaign.json');req.update(layouts=campaign['cases'],layout_root=campaign['layout_root'])
dump(D/'request-template.json',req)
print(json.dumps(dict(state='prepared',reference_files=len(spec['files']),native_cases=5)))
