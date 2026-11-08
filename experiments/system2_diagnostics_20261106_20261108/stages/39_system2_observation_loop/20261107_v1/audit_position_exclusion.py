"""Exploratory CPU fixture: does one attempted position suppress another object?

Idealized attachment and delivery deliberately remove physical failures. This
tests selection coverage only; it is not an RGB episode or native task score.
"""
from pathlib import Path
import copy,hashlib,json,math
H=Path(__file__).resolve().parent
source=(H/'candidates/fixed_six_turns/candidate.py').read_text()
class IdealRobot:
    def __init__(self,separation):
        self.objects={f'basket_{i+1}':dict(pose=[x,.05,.8036,1,0,0,0],dims=[.22,.16,.08]) for i,x in enumerate([-.28,0,.28])}
        self.objects.update({f'toy_car_{i+1}':dict(pose=[-.1+i*separation,-.20,.78,1,0,0,0],dims=[.02,.02,.02]) for i in range(2)})
        self.held={};self.positions={};self.delivered=set();self.events=[]
    def scene(self):return dict(objects=copy.deepcopy(self.objects))
    def approach(self,*,arm,position_m,quaternion_wxyz):
        self.positions[arm]=position_m
        if arm in self.held:self.objects[self.held[arm]]['pose'][:3]=position_m
        self.events.append(dict(method='approach',arm=arm,position=position_m));return {}
    def gripper(self,*,arm,command):
        self.events.append(dict(method='gripper',arm=arm,command=command))
        if command==0:
            choices=[(math.dist(self.positions[arm][:2],v['pose'][:2]),k) for k,v in self.objects.items() if k.startswith('toy_car') and k not in self.delivered]
            if choices and min(choices)[0]<.01:self.held[arm]=min(choices)[1]
        elif arm in self.held:
            label=self.held.pop(arm);obj=self.objects[label];basket=min((v for k,v in self.objects.items() if k.startswith('basket')),key=lambda b:math.dist(b['pose'][:2],obj['pose'][:2]))
            # Abstract successful delivery is assumed, not a claim about physics.
            obj['pose'][:3]=basket['pose'][:3];self.delivered.add(label)
        return {}
rows=[]
for separation in [.03,.08]:
    robot=IdealRobot(separation);namespace={};exec(compile(source,'<saved-candidate-selection-fixture>','exec'),namespace);namespace['policy'](robot,{})
    rows.append(dict(separation_m=separation,objects=2,distinct_ideal_deliveries=len(robot.delivered),remaining_objects=sorted(k for k in robot.objects if k.startswith('toy_car') and k not in robot.delivered),close_commands=sum(x['method']=='gripper' and x['command']==0 for x in robot.events),events=robot.events))
assert [r['distinct_ideal_deliveries'] for r in rows]==[1,2]
out=dict(state='completed',exploratory_symbolic_cases=2,new_native_cases=0,new_api_calls=0,gpu_used=False,source_sha256=hashlib.sha256(source.encode()).hexdigest(),rows=rows,interpretation='With ideal grasp/delivery and complete perception, the category+4cm attempted-position rule can suppress an unhandled nearby object. Loop6 correction alone does not fix this behavior.',limits=['Constructed CPU fixture, not an observed failure rate or native performance.','The second fixture changes only separation, with all solver/perception/grasp effects idealized.','A stable object tracker would require its own validation; raw detector suffixes are not guaranteed persistent identities.'])
(H/'position-exclusion-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps([{k:v for k,v in r.items() if k!='events'} for r in rows]))
