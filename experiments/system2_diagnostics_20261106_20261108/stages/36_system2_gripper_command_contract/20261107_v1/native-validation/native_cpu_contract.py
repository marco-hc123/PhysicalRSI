"""Use real frozen primitive classes with mocked observe/step/plan; no GPU."""
import sys,json,copy,tempfile,types
from pathlib import Path
R=Path('/mnt/data/physical-RSI');O=Path(__file__).resolve().parent
I=R/'result/25_system2_integration_20261030T050100Z/integration-sources'
sys.path[:0]=[str(O/'code'),str(I),str(I/'framework-validation-v3')]
from gripper_contract import GripperContract
cfg=json.loads((R/'result/36_postgrasp_diagnosis_20261107/runtimes/logging_only-v2.json').read_text())['policy_spec']['configuration']
state={f'{a}_arm_joint_state':[0.]*6 for a in ('left','right')};state.update({f'{a}_ee_joint_state':[.44] for a in ('left','right')})
(O/'scratch').mkdir(exist_ok=True);rows=[]
with tempfile.TemporaryDirectory(dir=O/'scratch') as tmp:
 for latch in [False,True]:
  actions=[];backend=types.SimpleNamespace(output=Path(tmp),counter=0,last_record=None)
  p=GripperContract(latch_gripper_commands=latch,diagnostic_backend=backend,observe=lambda **kw:copy.deepcopy(state),plan=lambda **kw:[[.01,0,0,0,0,0]],step=lambda action,**kw:actions.append(copy.deepcopy(action)),perceive=None,dimensions=cfg['dimensions'],joint_limits=cfg['joint_limits'],max_joint_step=.25,timeout_s=180,max_waypoints=500,gripper_steps=6)
  p.gripper(arm='right',command=0);result=p.approach(arm='right',position_m=[0,0,1.01],quaternion_wxyz=[1,0,0,0]);assert len(actions)==7;assert actions[-1]['right_ee_joint_state']==([0.] if latch else [.44]);assert result['state']['right_ee_joint_state']==[.44];assert result['action_steps']==1
  rows.append(dict(latch=latch,step_calls=len(actions),movement_gripper_command=actions[-1]['right_ee_joint_state'],returned_actual_gripper=result['state']['right_ee_joint_state']))
result=dict(state='passed',gpu_used=False,actual_frozen_primitive_classes=True,rows=rows)
(O/'native-cpu-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
