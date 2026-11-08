"""Check that the candidate edit changes only the first transport target."""
from pathlib import Path
import json,hashlib,copy
H=Path(__file__).resolve().parent;inp=json.loads((H/'inputs.json').read_text())
class Robot:
 def __init__(self,layout):
  self.events=[];self.n=0;self.objects={}
  for i,r in enumerate(layout['Geometry']['basket']):self.objects[f'basket_{i+1}']=dict(pose=r['default_pos']+[1,0,0,0],dims=inp['geometry']['object_sizes']['basket'])
  for c,rows in layout['Rigid'].items():
   c={'action_camera':'camera'}.get(c,c)
   for i,r in enumerate(rows):self.objects[f'{c}_{i+1}']=dict(pose=r['default_pos']+[1,0,0,0],dims=inp['geometry']['object_sizes'].get(c,[.06,.04,.04]))
 def scene(self):return dict(objects=copy.deepcopy(self.objects))
 def approach(self,**kwargs):
  self.n+=1;self.events.append(dict(method='approach',**kwargs));return dict(primitive_error='no_collision_free_path') if self.n==4 else {}
 def gripper(self,**kwargs):self.events.append(dict(method='gripper',**kwargs));return {}
source=(H/'candidates/original_transport/candidate.py').read_text();modified=(H/'candidates/offset_transport/candidate.py').read_text()
assert modified.replace("            destination = [bx - 0.0175, by - 0.035, 1.01]\n            if abs(bx) < 0.1:\n                destination = [bx + (-0.065 if arm == 'left' else 0.065), by - 0.055, 0.99]\n            if not move(arm, destination):","            if not move(arm, [bx, by, 1.01]):")==source
rows=[]
for i,layout in enumerate(inp['layouts']):
 traces=[]
 for s in [source,modified]:
  ns={};exec(compile(s,'<candidate-contract>','exec'),ns);robot=Robot(layout);ns['policy'](robot,{});assert robot.n==4;traces.append(robot.events)
 a,b=traces;assert a[:-1]==b[:-1];x,y,z=a[-1]['position_m'];expected=[x+(-.065 if a[-1]['arm']=='left' else .065),y-.055,.99] if abs(x)<.1 else [x-.0175,y-.035,1.01]
 assert b[-1]['position_m']==expected and a[-1]['quaternion_wxyz']==b[-1]['quaternion_wxyz'] and a[-1]['arm']==b[-1]['arm']
 rows.append(dict(layout=i,control=a,treatment=b))
out=dict(state='passed',fixture_cases=5,new_native_cases=0,api_calls=0,lab_gpu_used=False,source_edit_only_transport_block=True,rows=rows,scope='Synthetic first-transport contract check, no physics score')
(H/'cpu-contract-results.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(state='passed',fixture_cases=5)))
