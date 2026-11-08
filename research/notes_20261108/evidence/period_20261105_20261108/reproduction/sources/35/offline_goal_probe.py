"""One idle GPU, fixed recorded starts: bounded target-height/yaw diagnostic."""
import ctypes,datetime,hashlib,json,math,os,re,subprocess,sys,time,traceback
from pathlib import Path
L=Path(__file__).resolve().parent;R=Path('/mnt/data/joey_tr/physical-RSI');O=L/'goal-probes'
import single_gpu_guard as guard
guard.O=O

def read(p):return json.loads(Path(p).read_text())
def write(name,x):
 p=O/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def quat_yaw(q,degrees):
 w,x,y,z=q;a=math.radians(degrees)/2;c,s=math.cos(a),math.sin(a)
 return [c*w-s*z,c*x-s*y,c*y+s*x,c*z+s*w]
def worker():
 guard.configure();write('gpu-idle-before-worker.json',guard.check_idle());write('write-isolation.json',guard.guard());assert ctypes.CDLL('libcuda.so.1').cuInit(0)==0
 cfg=read(O/'input-runtime.json');pc=cfg['policy_spec']['configuration'];source=guard.mapped(pc['robot_yml']);code=source.parents[3]
 sys.path[:0]=[str(code),str(R/'repos/lab-runtime/curobo')]
 import numpy as np,torch,warp
 warp.config.kernel_cache_dir=str(O/'cache/warp')
 import curobo._src.runtime as cruntime
 cruntime.cache_dir=str(O/'cache/curobo');assert torch.cuda.device_count()==1
 y=source.read_text();replacements={}
 for s in set(re.findall(r'/mnt/data/physical-RSI/[^\s\"\']+',y)):replacements[s]=str(guard.mapped(s));y=y.replace(s,replacements[s])
 target=O/'config/robot-paths-only.yml';target.parent.mkdir(exist_ok=True);target.write_text(y)
 for asset in source.parent.iterdir():
  if asset.name!='curobo.yml':(target.parent/asset.name).symlink_to(asset)
 from rdj_v1_classify_objects.curobo_planner import CuroboPlanner
 import inspect
 write('runtime.json',dict(planner_source=inspect.getfile(CuroboPlanner),planner_sha256=sha(inspect.getfile(CuroboPlanner)),yaml_sha256=sha(source),path_substitutions=replacements,visible_devices=1,gpu_uuid=guard.GPU,torch=torch.__version__,scope='Offline solver feasibility; no RGB or robot steps'))
 jobs=read(O/'protocol.json')['jobs'];planners={};results=[];ik_events=[]
 def wrap_ik(planner):
  original=planner.motion_planner.ik_solver.solve_pose
  def solve(*args,**kwargs):
   res=original(*args,**kwargs);row=dict(success_count=int(res.success.sum().item()),success_shape=list(res.success.shape))
   for key in ['position_error','rotation_error','feasible']:
    v=getattr(res,key,None)
    if hasattr(v,'detach'):
     ar=v.detach().cpu().numpy();row[key]=dict(shape=list(ar.shape),minimum=float(ar.min()),maximum=float(ar.max()),true_count=int(ar.sum()) if ar.dtype==bool else None)
   ik_events.append(row);return res
  planner.motion_planner.ik_solver.solve_pose=solve
 try:
  for arm in sorted(set(j['arm'] for j in jobs)):
   planners[arm]=CuroboPlanner(robot_origin_pose=[0,0,0,1,0,0,0],active_joints_name=['joint'+str(i) for i in range(1,7)],all_joints=['joint'+str(i) for i in range(1,7)],dt=.004,yml_path=str(target),table_height=-.025);wrap_ik(planners[arm])
  for job in jobs:
   np.random.seed(job['seed']);torch.manual_seed(job['seed']);torch.cuda.manual_seed_all(job['seed']);ik_events.clear();t=time.monotonic()
   target=list(job['position_m']);target[2]+=job['delta_z_m'];q=quat_yaw(job['quaternion_wxyz'],job['yaw_degrees'])
   res=planners[job['arm']].plan_path(curr_joint_pos=job['start'],target_ee_pose=[*target,*q],real_robot_pose=pc['arm_bases'][job['arm']]);torch.cuda.synchronize()
   row=dict(job,requested_pose=[*target,*q],planner_status=res.get('status'),trajectory_returned='position' in res,ik_calls=list(ik_events),seconds=time.monotonic()-t)
   if 'position' in res:
    traj=np.asarray(res['position']);assert np.isfinite(traj).all();np.save(O/f'trajectories/job{job["job_id"]:03}.npy',traj);row['trajectory_shape']=list(traj.shape)
   results.append(row);write(f'probes/job{job["job_id"]:03}.json',row);write('results.json',results);print(json.dumps({k:row[k] for k in ['job_id','source_layout_id','delta_z_m','yaw_degrees','planner_status']}),flush=True)
 finally:
  for p in planners.values():p.__del__()
 groups=[]
 for sid in sorted(set(x['source_layout_id'] for x in results)):
  for dz,yaw in read(O/'protocol.json')['settings']:
   rs=[x for x in results if x['source_layout_id']==sid and x['delta_z_m']==dz and x['yaw_degrees']==yaw];groups.append(dict(source_layout_id=sid,delta_z_m=dz,yaw_degrees=yaw,calls=len(rs),trajectories=sum(x['trajectory_returned'] for x in rs)))
 write('summary.json',dict(state='completed',solver_calls=len(results),new_native_cases=0,api_calls=0,groups=groups))
def main():
 assert not (O/'status.json').exists();O.mkdir(exist_ok=True);guard.configure();write('gpu-before.json',guard.check_idle())
 with (O/'worker.log').open('x') as f:
  p=subprocess.Popen([str(R/'envs/simulator/bin/python'),'-B',str(L/'offline_goal_probe.py'),'worker'],stdout=f,stderr=subprocess.STDOUT,start_new_session=True);write('status.json',dict(state='running',worker_pid=p.pid,controller_pid=os.getpid()));start=time.monotonic()
  while p.poll() is None:
   with (O/'gpu-samples.jsonl').open('a') as out:out.write(json.dumps(dict(utc=guard.now(),gpu=guard.smi(['-i',guard.GPU,'--query-gpu=memory.used,utilization.gpu','--format=csv,noheader'])))+'\n')
   if time.monotonic()-start>1200:
    import signal;os.killpg(p.pid,signal.SIGTERM);p.wait(20);break
   time.sleep(5)
 write('status.json',dict(state='completed' if p.returncode==0 else 'failed',exit_code=p.returncode,worker_pid=None,controller_pid=None,elapsed_s=time.monotonic()-start,utc=guard.now()))
 write('gpu-after.json',dict(devices=guard.smi(['--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader']),compute=guard.smi(['--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader'])))
if __name__=='__main__':
 try:worker() if len(sys.argv)>1 else main()
 except BaseException as e:write('failure.json',dict(error=repr(e),traceback=traceback.format_exc()));raise
