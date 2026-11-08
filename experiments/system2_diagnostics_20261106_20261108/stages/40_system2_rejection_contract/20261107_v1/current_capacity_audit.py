"""Symbolic coverage audit. This is NOT a simulator, score or grasp experiment."""
import copy, hashlib, json, math, ast
from pathlib import Path
H=Path(__file__).resolve().parent
inputs=json.loads((H/'capacity-inputs.json').read_text());source=(H/'candidates/structured_rejection/candidate.py').read_text()
assert hashlib.sha256(source.encode()).hexdigest()=='e21e333cd2f169c3d73be952e5fa6f2ca7e2f4e48042f5873fff64abc6f67e88'
class IdealRobot:
 def __init__(self,layout):
  self.objects={};self.positions={};self.held={};self.events=[];self.moved=set();self.baskets=[]
  for i,row in enumerate(layout['Geometry']['basket']):
   p=list(row['default_pos']);self.baskets.append(p)
   self.objects[f'basket_{i+1}']=dict(pose=p+[1,0,0,0],dims=inputs['geometry']['object_sizes']['basket'])
  for category,rows in layout['Rigid'].items():
   category={'action_camera':'camera'}.get(category,category)
   for i,row in enumerate(rows):
    self.objects[f'{category}_{i+1}']=dict(pose=list(row['default_pos'])+[1,0,0,0],dims=inputs['geometry']['object_sizes'].get(category,[.06,.04,.04]))
  self.initial=copy.deepcopy(self.objects)
 def scene(self):return dict(objects=copy.deepcopy(self.objects))
 def approach(self,*,arm,position_m,quaternion_wxyz):
  self.positions[arm]=list(position_m);self.events.append(dict(method='approach',arm=arm,position=position_m))
  if arm in self.held:self.objects[self.held[arm]]['pose'][:2]=position_m[:2]
  return {'state':{},'action_steps':1}
 def gripper(self,*,arm,command):
  self.events.append(dict(method='gripper',arm=arm,command=command))
  if command==0:
   xy=self.positions[arm][:2];choices=[(math.dist(xy,o['pose'][:2]),k) for k,o in self.objects.items() if not k.startswith('basket_') and k not in self.moved]
   if choices and min(choices)[0]<.025:self.held[arm]=min(choices)[1]
  elif arm in self.held:
   key=self.held.pop(arm)
   basket=min(self.baskets,key=lambda p:math.dist(self.objects[key]['pose'][:2],p[:2]))
   assert math.dist(self.objects[key]['pose'][:2],basket[:2])<.12,'Abstract delivery intent ambiguous'
   self.objects[key]['pose'][:3]=basket[:];self.moved.add(key)
  return {'state':{},'action_steps':1}
rows=[]
for label,program in [('current_fixed_six',source),('only_extend_to_complete_initial_count',source.replace('range(6)','range(max(6, len(items)))'))]:
 ns={};exec(compile(program,'<saved-candidate-symbolic-audit>','exec'),ns)
 for i,layout in enumerate(inputs['layouts']):
  robot=IdealRobot(layout);ns['policy'](robot,{})
  remaining=sorted(k for k in robot.objects if not k.startswith('basket_') and k not in robot.moved)
  row=dict(condition=label,layout_id=i,source_layout_sha256=inputs['cases'][i]['layout_sha256'],objects=sum(len(x) for x in layout['Rigid'].values()),symbolic_releases=len(robot.moved),remaining=remaining,close_calls=sum(e['method']=='gripper' and e['command']==0 for e in robot.events),all_symbolically_delivered=not remaining,events=robot.events)
  rows.append(row)
tree=ast.parse(source);calls=sorted({n.func.attr for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='robot'})
out=dict(state='completed',source_sha256=hashlib.sha256(source.encode()).hexdigest(),conditions=2,layouts=5,symbolic_cases=10,native_cases=0,api_calls=0,lab_gpu_used=False,robot_methods=calls,rows=rows,limitations=['Constructed complete perception and ideal attachment/delivery snapped to intended nearest basket center; no physics, collisions, action budget, native reward or full-success result. This removes placement errors intentionally to test coverage capacity only.','Only layouts 0 and 3 contain more than six objects (8 and 7); layouts 1,2,4 contain 5,3,6.','The six-cycle cap is a latent coverage limitation, not an explanation of earlier first-transport failures.','Candidate has no explicit final-home stage; real success additionally depends on native home and settled predicates.'])
(H/'current-symbolic-capacity.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps([dict(condition=r['condition'],layout=r['layout_id'],objects=r['objects'],delivered=r['symbolic_releases'],remaining=len(r['remaining'])) for r in rows]))
