"""CPU action-contract regression with measured gripper blocked at .44."""
import sys,json,tempfile,types,copy,inspect
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H/'code'))
stub=types.ModuleType('postgrasp_contract')
class Base:
 def __init__(self,**kw):self.__dict__.update(kw)
 def gripper(self,*,arm,command):
  action=copy.deepcopy(self.observed);action[arm+'_ee_joint_state']=[command]
  self.step(action,deadline=100);return {'state':copy.deepcopy(self.observed)}
stub.Backend=object;stub.Primitives=Base;stub.ObservedObstacles=object;sys.modules['postgrasp_contract']=stub
from gripper_contract import GripperContract
observed={f'{a}_arm_joint_state':[0.]*6 for a in ('left','right')};observed.update({f'{a}_ee_joint_state':[.44] for a in ('left','right')})
checks=[];(H/'scratch').mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(dir=H/'scratch') as tmp:
 for latch in [False,True]:
  sent=[];p=GripperContract(latch_gripper_commands=latch,step=lambda action,deadline:sent.append(copy.deepcopy(action)),observed=observed,dimensions={k:len(v) for k,v in observed.items()},diagnostic_backend=types.SimpleNamespace(output=Path(tmp)))
  result=p.gripper(arm='right',command=0);assert result['state']['right_ee_joint_state']==[.44]
  p.step(copy.deepcopy(observed),deadline=100);assert sent[-1]['right_ee_joint_state']==([0.] if latch else [.44]);assert observed['right_ee_joint_state']==[.44];checks.append(f'latch={latch}: subsequent move command and unchanged measured observation')
  p.gripper(arm='left',command=1);p.step(copy.deepcopy(observed),deadline=100)
  assert sent[-1]['right_ee_joint_state']==([0.] if latch else [.44]);assert sent[-1]['left_ee_joint_state']==([1.] if latch else [.44]);checks.append(f'latch={latch}: independent left/right commands')
  old=dict(p.gripper_commands)
  for invalid in [float('nan'),-1,2,True]:
   try:p.gripper(arm='right',command=invalid);raise AssertionError('bad command accepted')
   except ValueError:pass
  assert p.gripper_commands==old;checks.append(f'latch={latch}: invalid inputs preserve previous command')
  p.gripper(arm='right',command=1);p.step(copy.deepcopy(observed),deadline=100);assert sent[-1]['right_ee_joint_state']==([1.] if latch else [.44]);checks.append(f'latch={latch}: explicit reopen replaces latch')
assert list(inspect.signature(GripperContract.gripper).parameters)==['self','arm','command'];checks.append('RPC signature preserved')
result=dict(state='passed',checks=checks,check_count=len(checks),gpu_used=False,scope='CPU action-construction fixtures; does not establish physical grasp')
(H/'offline-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
