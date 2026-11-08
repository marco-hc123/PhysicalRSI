"""No GPU: exercise the complete assembly wrapper with inert backend stubs."""
import ast,json,sys,types
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H/'code-v2'))
from structured_feedback import assemble,transform_driver
tree=ast.parse((H/'driver-contract-provenance/code_execution.py').read_text())
original=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='_DRIVER' for t in n.targets))
parent=types.ModuleType('PhysicalRSI_baselines');sub=types.ModuleType('PhysicalRSI_baselines.robodojo');driver=types.SimpleNamespace(_DRIVER=original);sub.code_execution=driver
sys.modules['PhysicalRSI_baselines']=parent;sys.modules['PhysicalRSI_baselines.robodojo']=sub
backend=types.ModuleType('gripper_contract');backend.assemble=lambda *a,**k:'inert-backend';sys.modules['gripper_contract']=backend
root=H/'assembly-fixture';identity=dict(episode='fixture',actor='0')
result=assemble(None,configuration=dict(output=str(root)),identity=identity,own=lambda x:x)
assert result=='inert-backend' and driver._DRIVER==transform_driver(original)
p=root/'fixture/0/driver-contract.jsonl';assert p.is_file()
report=dict(state='passed',fixtures=1,new_native_cases=0,gpu_used=False,api_calls=0,scope='Assembly wrapper logging and exact driver transform; inert backend,not physical correctness')
(H/'cpu-assembly-v2.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
