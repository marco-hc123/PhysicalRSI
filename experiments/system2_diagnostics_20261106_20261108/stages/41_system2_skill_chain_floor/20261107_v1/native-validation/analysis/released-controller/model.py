"""RGB category completion with source-local retries and tabletop handoff."""
import itertools
import numpy as np
import cv2
from scipy.spatial.transform import Rotation
from .motion import Motion,ARMS
from .perception import Reader,HEIGHT

def look_pose(arm):return [-.42 if arm=='left' else .42,-.32,1.12,.5,-.5,.5,.5]

class Episode(Motion):
 def __init__(self,cfg):
  super().__init__(cfg);self.reader=cfg['reader'];self.initial_detections=None;self.look_joints={};self.grasp_plan=None
 def observe(self,recovery=False,temporal_source=None):
  d=yield {'_rgb_request': True, '_recovery_front': recovery, '_temporal_source':temporal_source}
  self.event(rgb_detections=d);return d
 def settled_handoff(self,category,source):
  from .temporal_source import stable_pair
  previous=yield from self.observe(recovery=True,temporal_source=source)
  for attempt in range(3):
   self.stage='handoff_settle'
   for _ in range(6):yield self.action()
   current=yield from self.observe(recovery=True,temporal_source=source)
   stable=stable_pair(previous,current,category)
   self.event(handoff_stability_attempt=attempt+1,stable_candidates=stable)
   if stable:return stable
   previous=current
  self.event(handoff_stability_unknown=True,category=category)
  return []
 def record_grasp_source(self,obj):
  from pathlib import Path
  filename=f'{self.count:04d}_selected_source.png'
  if self.trace:
   cv2.imwrite(str(Path(self.trace.name).parent/filename),cv2.cvtColor(self.rgb,cv2.COLOR_RGB2BGR))
  self.event(selected_source=obj,selected_source_rgb=filename)
 def transfer(self,obj,arm,dest,tag,qualified_plan=None):
  from .source_veto import SourceAppearance
  source_appearance=SourceAppearance(self.rgb,obj['box'])
  from .grasp_shape import grasp as infer_grasp
  self.record_grasp_source(obj)
  cat=obj['category'];contact,q,shape=infer_grasp(self.rgb,obj);grasp=contact+[0,0,.125];grasp[2]=max(grasp[2],.920);self.event(rgb_grasp_shape=shape)
  self.event(category=cat,transfer=tag,arm=arm,contact=contact,destination=dest)
  self.grasp_plan=qualified_plan if qualified_plan is not None else self.qualify_grasp(arm,grasp,q)
  if self.grasp_plan is None:
   self.event(rgb_category_incomplete=cat,reason='exact reach preflight rejected before contact');return False
  q=self.grasp_plan['q']
  for attempt in range(2):
   self.stage='open';yield from self.hold_gripper(arm,1.,3)
   try:
    self.stage='approach';yield from self.move(arm,[*(grasp+[0,0,.07]),*q],16)
    self.stage='contact';yield from self.move(arm,[*grasp,*q],12)
    break
   except RuntimeError as exc:
    self.event(contact_recovery_attempt=attempt+1,contact_failure=str(exc))
    self.targets[arm]=self.state[arm+'_arm_joint_state'].astype('float32').copy()
    self.grip[arm]=1.
    actual=self.state[arm+'_ee_pose'].copy();actual[2]+=.06
    self.stage='contact_recovery_lift';yield from self.move(arm,actual,12)
    self.stage='contact_recovery_view';yield from self.move(arm,look_pose(arm),18)
    if attempt==1:
     self.event(rgb_category_incomplete=cat,reason='two contact failures after orthogonal regrasp')
     return False
    live=[x for x in (yield from self.observe()) if x['category']==cat]
    if not live:
     self.event(rgb_category_incomplete=cat,reason='source absent after contact recovery');return False
    fresh=min(live,key=lambda o:np.linalg.norm(o['xyz'][:2]-obj['xyz'][:2]))
    if np.linalg.norm(fresh['xyz'][:2]-obj['xyz'][:2])>.07:
     self.event(rgb_category_incomplete=cat,reason='source displaced beyond70mm during contact recovery');return False
    source_appearance=SourceAppearance(self.rgb,fresh['box'])
    self.record_grasp_source(fresh)
    contact,new_q,shape=infer_grasp(self.rgb,fresh)
    q=(Rotation.from_rotvec([0,0,np.pi/2])*Rotation.from_quat(q[[1,2,3,0]])).as_quat()[[3,0,1,2]]
    grasp=contact+[0,0,.125];grasp[2]=max(grasp[2],.920)
    self.grasp_plan=self.qualify_grasp(arm,grasp,q)
    if self.grasp_plan is None:
     self.event(rgb_category_incomplete=cat,reason='recovery reach preflight rejected');return False
    q=self.grasp_plan['q']
    self.event(contact_reacquired=fresh,rgb_grasp_shape=shape,retry_quaternion=q)
  self.stage='close';yield from self.hold_gripper(arm,0.,12)
  pickup=self.state[arm+'_ee_pose'].copy();q=pickup[3:].copy()
  self.stage='capture_lift';yield from self.move(arm,[*(pickup[:3]+[0,0,.008]),*q],8)
  self.stage='capture_settle';yield from self.settle_capture(arm)
  self.stage='lift';yield from self.move(arm,[*(pickup[:3]+[0,0,.08]),*q],16)
  target=np.asarray(dest).copy();transit_z=target[2]
  self.stage='transport';yield from self.move(arm,[*target,*q],22)
  q=self.state[arm+'_ee_pose'][3:].copy();target[2]-=.020 if tag=='basket' else .055
  self.stage='basket_lower' if tag=='basket' else 'lower';yield from self.move(arm,[*target,*q],10)
  q=self.state[arm+'_ee_pose'][3:].copy()
  self.stage='release';yield from self.hold_gripper(arm,1.,12)
  target[2]=transit_z;self.stage='retreat';yield from self.move(arm,[*target,*q],12)
  self.stage='observe_retract';yield from self.move(arm,look_pose(arm),18)
  observed=(yield from self.observe(recovery=True))
  source_confirmed=any(x['category']==cat and np.linalg.norm(x['xyz'][:2]-obj['xyz'][:2])<.022 for x in observed)
  verdict=source_appearance.check(self.rgb,source_confirmed=source_confirmed)
  self.event(post_transfer_rgb_detections=observed,post_transfer_source=verdict,completed_transfer=tag)
  if verdict['stationary']:
   self.event(rgb_category_incomplete=cat,reason='source visually stationary after complete transfer; retry source')
   return False
  return True
 def run(self):
  self.event(initial_home_detections=self.initial_detections)
  for arm in ARMS:
   self.stage='clear_view';yield from self.hold_gripper(arm,1.,2);yield from self.move(arm,look_pose(arm),16)
   self.look_joints[arm]=self.state[arm+'_arm_joint_state'].copy()
  detections=(yield from self.observe());self.event(rgb_detections=detections,instruction=self.instruction)
  cv2.imwrite(str(__import__('pathlib').Path(self.trace.name).parent/'initial.jpg'),cv2.cvtColor(self.rgb,cv2.COLOR_RGB2BGR))
  baskets=sorted([x for x in detections if x['category']=='basket'],key=lambda x:x['xyz'][0])
  if len(baskets)!=3:raise RuntimeError(f'RGB expected3 baskets, found{len(baskets)}')
  objects=[x for x in detections if x['category']!='basket']
  groups={c:[x for x in objects if x['category']==c] for c in sorted(set(x['category'] for x in objects))}
  groups=dict(sorted(groups.items(),key=lambda kv:-sum(x['score'] for x in kv[1]))[:3])
  if not groups:raise RuntimeError('RGB no object category')
  def cross(obj,bi):return bi!=1 and ((obj['xyz'][0]<0)!=(bi==0))
  difficulty={'camera':1.,'toy_car':1.,'garage':1.5,'watch':2.,'pen':2.5}
  choices=[]
  for assignment in itertools.permutations(range(3),len(groups)):
   cost=sum(difficulty[cat]*(len(groups[cat])+sum(cross(o,bi) for o in groups[cat]))+.05*sum(np.linalg.norm(o['xyz'][:2]-baskets[bi]['xyz'][:2]) for o in groups[cat]) for cat,bi in zip(groups,assignment))
   choices.append((cost,assignment))
  _,assignment=min(choices,key=lambda x:x[0]);assigned=dict(zip(groups,assignment))
  cats=sorted(groups,key=lambda cat:(assigned[cat]==1,difficulty[cat]*(len(groups[cat])+sum(cross(o,assigned[cat]) for o in groups[cat]))))
  self.event(category_assignment=assigned,category_order=cats)
  for cat in cats:
   bi=assigned[cat];attempted=[];index=0;recover_source=None;recovery=False
   def source_record(obj):
    near=[a for a in attempted if np.linalg.norm(a['xy']-obj['xyz'][:2])<.04]
    return min(near,key=lambda a:np.linalg.norm(a['xy']-obj['xyz'][:2])) if near else None
   while True:
    live=[x for x in (yield from self.observe(recovery=recovery,temporal_source=recover_source)) if x['category']==cat]
    if not live:
     self.stage='residual_settle'
     for _ in range(3):yield self.action()
     live=[x for x in (yield from self.observe()) if x['category']==cat]
     if not live:
      live=[x for x in (yield from self.observe(recovery=True)) if x['category']==cat]
      self.event(rgb_front_recovery_category=cat,candidates=len(live))
      if not live:
       self.event(rgb_category_absent=cat,transfers=index,episode_score=None);break
    available=[o for o in live if source_record(o) is None or source_record(o)['count']<2]
    if not available:
     self.event(rgb_category_incomplete=cat,reason='all current RGB sources used both attempts',source_attempts=attempted);break
    obj=min(available,key=lambda o:((source_record(o) or {}).get('count',0),cross(o,bi),float(np.linalg.norm(o['xyz'][:2]-baskets[bi]['xyz'][:2]))))
    record=source_record(obj)
    if record is None:
     record=dict(xy=obj['xyz'][:2].copy(),count=0);attempted.append(record)
    record['count']+=1
    self.event(source_attempt=record['count'],source_candidates=len(available),source_category=cat,source_xy=obj['xyz'][:2])
    arm='left' if obj['xyz'][0]<0 else 'right'
    direct=False;direct_plan=None
    if cross(obj,bi):
     from .grasp_shape import grasp as infer_grasp
     contact,q,shape=infer_grasp(self.rgb,obj);g=contact+[0,0,.125];g[2]=max(g[2],.920)
     destination_arm='left' if bi==0 else 'right'
     direct_plan=self.qualify_grasp(destination_arm,g,q)
     direct=direct_plan is not None
     self.event(direct_transfer_preflight=direct,category=cat,destination_arm=destination_arm)
     if direct:arm=destination_arm
    if cross(obj,bi) and not direct:
     staging=np.array([0.,-.20,.99])
     from .temporal_source import TemporalSource
     handoff_source=TemporalSource(self.rgb,obj['box'],cat)
     transferred=yield from self.transfer(obj,arm,staging,'handoff_source')
     if not transferred:
      recovery=True;recover_source=handoff_source
      self.event(source_local_continuation=True,category=cat,failed_phase='handoff_source');continue
     recover_source=handoff_source;recovery=True
     live=yield from self.settled_handoff(cat,handoff_source)
     arm='left' if bi==0 else 'right';direct_plan=None
     from .grasp_shape import grasp as infer_grasp
     for candidate in sorted(live,key=lambda x:np.linalg.norm(x['xyz'][:2]-staging[:2])):
      contact,q,shape=infer_grasp(self.rgb,candidate);g=contact+[0,0,.125];g[2]=max(g[2],.920)
      direct_plan=self.qualify_grasp(arm,g,q)
      distance=float(np.linalg.norm(candidate['xyz'][:2]-staging[:2]))
      self.event(handoff_rgb_candidate=candidate,staging_distance_m=distance,native_destination_reachable=direct_plan is not None)
      if direct_plan is not None:
       obj=candidate;self.event(handoff_rgb_reacquired=obj,staging_distance_m=distance);break
     if direct_plan is None:
      self.event(source_local_continuation=True,category=cat,failed_phase='handoff_reacquire',reason='no current same-category RGB source with native destination-arm skill_choice after handoff');continue
    target=baskets[bi]['xyz'].copy()
    if bi==1:target[0]+=-.065 if arm=='left' else .065;target[1]-=.055;target[2]=.99
    else:target[0]+=(index%2-.5)*.035;target[1]-=.035;target[2]=1.01
    transferred=yield from self.transfer(obj,arm,target,'basket',qualified_plan=direct_plan)
    if not transferred:
     recovery=True
     self.event(source_local_continuation=True,category=cat,failed_phase='basket_source');continue
    index+=1
    recover_source=None
  for arm in ARMS:
   self.stage='final_home';yield from self.move(arm,max_waypoints=18)
  self.stage='complete_hold'

class Model:
 def __init__(self,cfg):
  import torch,time,random
  random.seed(0);np.random.seed(0);torch.manual_seed(0);cv2.setRNGSeed(0)
  load_started=time.monotonic()
  cv2.setNumThreads(1);torch.set_num_threads(1)
  self.reader=Reader();perception_loaded=time.monotonic();owner=Motion({});self.planners=owner.planners;self.models={};self.indices=[];self.perception_batch_id=0
  from .motion import BASE
  from pathlib import Path
  import os,json
  qualification={a:self.planners[a].plan_path(np.zeros(6),look_pose(a),BASE[a])['status'] for a in ARMS}
  (Path(os.environ['CLASSIFY_RESULTS'])/'load_timing.json').write_text(json.dumps(dict(perception_load_seconds=perception_loaded-load_started,planner_load_and_warmup_seconds=time.monotonic()-perception_loaded,total_load_seconds=time.monotonic()-load_started)))
  (Path(os.environ['CLASSIFY_RESULTS'])/'observation_pose_qualification.json').write_text(json.dumps(qualification))
  if any(v!='Success' for v in qualification.values()):raise RuntimeError('observation pose native qualification failed before episodes')
 def reset(self):
  for m in self.models.values():m.reset()
  self.models={};self.indices=[]
 def update_obs_batch(self,obs_list):
  self.indices=[];fresh=[]
  for obs in obs_list:
   i=int(obs['env_idx'])
   if i not in self.models:self.models[i]=Episode({'reader':self.reader,'planners':self.planners});fresh.append(i)
   self.models[i].update_obs(obs);self.indices.append(i)
   if i in fresh:self.models[i].event(policy_env_idx=i)
  if fresh:
   ds=self.reader.read_batch([self.models[i].rgb for i in fresh],[self.models[i].state for i in fresh])
   for i,d in zip(fresh,ds):self.models[i].initial_detections=d
 def update_obs(self,obs):self.update_obs_batch([dict(obs,env_idx=0)])
 def get_action_batch(self,env_idx_list=None):
  ids=self.indices if env_idx_list is None else env_idx_list
  # Resolve all current RGB requests together before one action per environment.
  actions=[None for _ in ids];pending=list(range(len(ids)))
  while pending:
   requested=[];recovery_flags=[];temporal_sources=[]
   for j in pending:
    result=self.models[int(ids[j])].get_action()
    if isinstance(result,dict) and result.get('_rgb_request'):
     requested.append(j);recovery_flags.append(bool(result.get('_recovery_front',False)));temporal_sources.append(result.get('_temporal_source'))
    else:actions[j]=result
   if not requested:break
   import time
   started=time.monotonic()
   detections=self.reader.read_batch([self.models[int(ids[j])].rgb for j in requested],[self.models[int(ids[j])].state for j in requested],recovery_flags=recovery_flags,temporal_sources=temporal_sources)
   elapsed=time.monotonic()-started
   self.perception_batch_id+=1
   for batch_index,(j,d) in enumerate(zip(requested,detections)):
    m=self.models[int(ids[j])];m.pending_rgb=d
    m.event(rgb_basket_source_rejections=self.reader.last_basket_exclusions[batch_index])
    m.event(rgb_robot_source_rejections=self.reader.last_robot_exclusions[batch_index])
    m.event(perception_batch_id=self.perception_batch_id,perception_batch_size=len(requested),perception_batch_seconds=elapsed)
   pending=requested
  if all(self.models[int(i)].failure is not None or self.models[int(i)].stage=='complete_hold' for i in ids):
   return [[dict(a[0]) for _ in range(16)] for a in actions]
  return actions
 def get_action(self):return self.get_action_batch([0])[0]
