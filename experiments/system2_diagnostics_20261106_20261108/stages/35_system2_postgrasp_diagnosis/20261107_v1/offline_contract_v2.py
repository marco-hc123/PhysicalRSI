"""CPU-only transparency checks for side-channel instrumentation."""
import tempfile,json,sys,types
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H/'code-v2'))
from simulator_sidecar import attach
from diagnostic_common import safe
checks=[]
class Layout:
 def get_labels_by_prefix(self,i,prefix):return ['cat0_0'] if prefix=='cat0' else []
 def get_instance_name(self,i,label):return 'object'
 def get_instance_pose(self,*args,**kwargs):return [1,2,3],[1,0,0,0]
class Env:
 def __init__(self):
  self.scene_manager=types.SimpleNamespace(layout_manager=Layout());self.robot_manager=types.SimpleNamespace(robot_list=[])
  self.env_seeds=[4];self.take_action_cnt=[17];self.calls=0;self.data=[dict(env_idx=0,state={'left':[0.]},vision='unchanged')]
 def get_obs_batch(self,*args,**kwargs):self.calls+=1;return self.data
(H/'scratch').mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(dir=H/'scratch') as d:
 e=Env();data=e.data;attach(e,d);assert e.get_obs_batch() is data and e.calls==1
 assert set(data[0])=={'env_idx','state','vision'};checks.append('same object and keys; one original observation call')
 records=[json.loads(s) for s in next(Path(d).glob('*.jsonl')).read_text().splitlines()];assert records[-1]['objects']['cat0_0']['position_world']==[1,2,3];assert records[-1]['native_action_count']==17;checks.append('side-file state and frame index captured')
 e.scene_manager=None;assert e.get_obs_batch() is data;checks.append('logging exception does not alter observation or propagate')
 stub=types.ModuleType('trajectory_contract');stub.DiagnosticBackend=object;stub.DiagnosticPrimitives=object;stub.ObservedObstacles=object;sys.modules['trajectory_contract']=stub
 from postgrasp_contract import Backend
 b=Backend.__new__(Backend);b.output=Path(d);b.counter=2;calls=[];result=types.SimpleNamespace(success=True,status='SUCCESS',position_error=.001)
 p=types.SimpleNamespace(plan_pose=lambda *args,**kwargs:(calls.append((args,kwargs)) or result))
 b.wrap_planner('left',p);assert p.plan_pose(3,x=4) is result and calls==[((3,),{'x':4})];checks.append('solver args and return identity unchanged')
 p=types.SimpleNamespace(plan_pose=lambda *args,**kwargs:(_ for _ in ()).throw(ValueError('fixture')));b.wrap_planner('right',p)
 try:p.plan_pose();raise AssertionError('missing original exception')
 except ValueError:pass
 checks.append('solver original exception propagated')
import inspect
from postgrasp_contract import Primitives
assert list(inspect.signature(Primitives.approach).parameters)==['self','arm','position_m','quaternion_wxyz']
assert list(inspect.signature(Primitives.gripper).parameters)==['self','arm','command']
checks.append('explicit RPC parameter signatures preserved')
report=dict(state='passed' ,checks=checks,gpu_used=False,paid_api_calls=0,scope='CPU mocks verify logging transparency; does not prove simulator integration')
(H/'offline-validation-v2.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
