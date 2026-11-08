"""Native qualification, distinct from scored robot-policy episodes."""
import json,sys
from pathlib import Path
O=Path(__file__).resolve().parent
from prepare_phase import config,I,read_json,atomic_json,NativeRuntime
task,role,count=sys.argv[1],sys.argv[2],int(sys.argv[3])
assert task in ['general_pickup','classify_objects'] and role in ['smoke','development','heldout']
cfg=read_json(O/'runtime-template.json')
cfg['simulator_environment'].pop('PHYSICALRSI_SIDECAR_ROOT',None)
runtime=NativeRuntime(cfg)
root=O/'layouts'/task/role
if (root/'cases.json').exists():
    from PhysicalRSI_baselines.robodojo.evidence import verify_case
    cases=read_json(root/'cases.json')
    for row in cases:verify_case(row,root)
    assert len(cases)==count
else:
    assert not root.exists(),'Incomplete layout generation requires reconciliation'
    comparison=read_json(O/'selection'/f'{task}.json') if role=='heldout' else None
    cases=runtime.cases(tasks=[task],count=count,split='validation' if role=='heldout' else 'development',output=root,comparison=comparison)
    atomic_json(root/'cases.json',cases)
print(json.dumps(dict(task=task,role=role,qualified=len(cases),root=str(root))))
