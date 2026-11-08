"""Descriptive, candidate-visible commanded-closed motions near RGB basket estimates."""
import csv,datetime,hashlib,json,math,sys
from pathlib import Path
O=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
tag=sys.argv[1];assert tag.replace('_','').isalnum()
D=O/'target-audits'/tag;D.mkdir(parents=True,exist_ok=False)
rows=[];sources=[]
for phase in ['parent','sampling']:
 P=O/phase
 for completed in sorted((P/'native-campaign/runs').glob('*/completed.json')):
  condition=completed.parent.name;run=Path(read(completed)['output'])
  for p in sorted((run/'model/expert').glob('*/0/policy/processes/isolated/process.json')):
   proc=read(p);closed={'left':False,'right':False};baskets=[]
   sources.append(dict(path=str(p.relative_to(O)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
   for call in sorted(proc['calls'],key=lambda x:x['request']['id']):
    req=call['request'];kw=req.get('kwargs',{});value=call.get('response',{}).get('value',{})
    if req['method']=='scene' and isinstance(value,dict):
     found=[obj for name,obj in value.get('objects',{}).items() if name.rsplit('_',1)[0]=='basket']
     if found:baskets=found
    if req['method']=='gripper' and kw.get('arm') in closed:closed[kw['arm']]=kw['command']==0
    if req['method']!='approach' or not closed.get(kw.get('arm')) or not baskets:continue
    target=kw['position_m'];basket=min(baskets,key=lambda b:math.dist(target[:2],b['pose'][:2]));dist=math.dist(target[:2],basket['pose'][:2])
    if dist>.18 or target[2]<.98:continue
    status='incomplete' if 'response' not in call else 'exception' if 'error' in call['response'] else value.get('primitive_error','returned')
    rows.append(dict(phase=phase,condition=condition,actor=p.parents[4].name,call_id=req['id'],arm=kw['arm'],target_x=target[0],target_y=target[1],target_z=target[2],basket_estimate_x=basket['pose'][0],basket_estimate_y=basket['pose'][1],offset_x=target[0]-basket['pose'][0],offset_y=target[1]-basket['pose'][1],center_distance_xy=dist,result=status,process=str(p.relative_to(O))))
with (D/'motions.csv').open('w',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=list(rows[0]) if rows else ['condition']);writer.writeheader();writer.writerows(rows)
summary={}
for condition in sorted({x['condition'] for x in rows}):
 group=[x for x in rows if x['condition']==condition]
 summary[condition]=dict(motions=len(group),returned=sum(x['result']=='returned' for x in group),rejected=sum(x['result']=='no_collision_free_path' for x in group),center_motions=sum(x['center_distance_xy']<.01 for x in group))
out=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),summary=summary,sources=sources,scope='Completed cohorts only. Candidate-visible RGB basket estimate, commanded-closed motions within0.18mXY andz>=0.98. No claim that an object was held. Starting joints, arm, height, object and code differ; endpoint association is observational and cannot establish a target-offset treatment effect.')
(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out['summary']))
