"""Native qualification, distinct from scored robot-policy episodes."""
import json,sys
from pathlib import Path
O=Path(__file__).resolve().parent
from prepare_phase import config,I,read_json,atomic_json,NativeRuntime
task,role,count=sys.argv[1],sys.argv[2],int(sys.argv[3])
assert task in ['general_pickup','classify_objects'] and role in ['smoke','development','heldout']
cfg=read_json(O/'runtime-template.json')
cfg['simulator_environment'].pop('PHYSICALRSI_SIDECAR_ROOT',None)
from PhysicalRSI_baselines.robodojo import layouts
from PhysicalRSI_baselines.robodojo.layout_sampling import catalog
if task not in layouts.TASKS:
    assert task=='general_pickup' and task in catalog.SUPPORTED_TASKS
    prior=list(layouts.TASKS)
    layouts.TASKS=tuple(prior+[task])
    atomic_json(O/'layout-task-registration.json',dict(task=task,previous_tasks=prior,scope='Process-local registration of a task already implemented by the frozen catalogue sampler; sampler geometry, eligibility checks and native scoring unchanged',source=str(Path(layouts.__file__)),catalog=str(Path(catalog.__file__))))
import subprocess
original_generate=layouts.generate_batch
def generate_and_materialize(*args,**kwargs):
    result=original_generate(*args,**kwargs)
    generated=Path(args[2]);manifest=read_json(generated/'manifest.json')
    if manifest['state']!='complete':return result
    assetbase=Path('/mnt/data/physical-RSI/assets/robodojo-complete-source')
    roots=set()
    for path in generated.glob('*/*/layout.json'):
        layout=read_json(path)
        for kind in ['Rigid','Clutter','Articulated']:
            for category,instances in layout.get(kind,{}).items():
                for item in instances:
                    index=item['category_idx']
                    for storage in [kind,'Rigid','Clutter']:
                        rel=f'Assets/Object/RoboDojo/{storage}/{category}/{index:05d}'
                        if (assetbase/rel).is_dir():roots.add(rel)
    atomic_json(generated/'selected-asset-roots.json',sorted(roots))
    atomic_json(O/'selected-asset-roots.json',sorted(roots))
    subprocess.run([sys.executable,'-B',str(O/'fetch_task_assets.py'),'selected'],check=True)
    return result
layouts.generate_batch=generate_and_materialize
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
