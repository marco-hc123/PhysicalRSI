"""Offline path-contract check; no planner, simulator, model or GPU execution."""
import ast,hashlib,json,os,sys,datetime
from pathlib import Path
import numpy as np
O=Path(__file__).resolve().parent
os.environ['CUDA_VISIBLE_DEVICES']=''
sys.path.insert(0,str(O/'code'))
from released_waypoints import thin_native_path
p=O/'code/closed_gripper_spacing.py';tree=ast.parse(p.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='select_closed_path')
scope=dict(np=np,thin_native_path=thin_native_path);exec(compile(ast.Module(body=[fn],type_ignores=[]),str(p),'exec'),scope)
rows=[]
for source in sorted((O/'parent/backend-traces/fixed_parent').rglob('trajectory-*.json')):
 d=json.loads(source.read_text())
 if d.get('state')!='plan_returned':continue
 row=dict(path=str(source),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),baseline_waypoints=d['executed_waypoints'])
 try:
  path,indices,check=scope['select_closed_path'](d['dense_path'],d['inputs']['start'])
  assert path[-1]==d['dense_path'][-1] and len(path)<=500
  assert all(path[k]==d['dense_path'][j] for k,j in enumerate(indices))
  row.update(state='passed',new_waypoints=len(path),endpoint_preserved=True,only_original_samples=True,diagnostic=check)
 except ValueError as e:row.update(state='rejected_by_stricter_spacing',error=str(e))
 rows.append(row)
result=dict(state='completed',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidate_module_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),paths=len(rows),passed=sum(r['state']=='passed' for r in rows),rejected=sum(r['state']!='passed' for r in rows),native_episodes=0,api_calls=0,gpu_used=False,scope='Tests all stored successful parent paths, including open-gripper moves; actual intervention would apply only while commanded closed. Path fidelity check, not physical efficacy.',rows=rows)
(O/'spacing-cpu-contract.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
