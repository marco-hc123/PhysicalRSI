"""Bounded fixed-start target test after native reference releases its GPU."""
import os,sys,json,time,datetime,subprocess,traceback,hashlib
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[1];P=O.parent/'38_candidate_capacity_20261107'
def read(p):return json.loads(p.read_text())
def write(name,x):
 p=O/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def smi(args):return subprocess.check_output(['nvidia-smi',*args],text=True,timeout=15).strip()
def idle():
 procs=smi(['--query-compute-apps=pid','--format=csv,noheader']);mem,util=[int(x.strip()) for x in smi(['--query-gpu=memory.used,utilization.gpu','--format=csv,noheader,nounits']).split(',')]
 assert not procs and mem<100 and util==0,'GPU occupied';return dict(processes=procs,memory_mib=mem,utilization=util)
def worker():
 write('gpu-before.json',idle());assert os.environ['CUDA_VISIBLE_DEVICES']=='0'
 import numpy as np,torch
 assert torch.cuda.device_count()==1
 from rdj_v1_classify_objects.curobo_planner import CuroboPlanner
 import inspect
 cfg=read(P/'inherited-runtime.json')['policy_spec']['configuration'];planners={};rows=[]
 write('runtime.json',dict(torch=torch.__version__,planner=inspect.getfile(CuroboPlanner),planner_sha256=hashlib.sha256(Path(inspect.getfile(CuroboPlanner)).read_bytes()).hexdigest(),robot_yaml=cfg['robot_yml'],robot_yaml_sha256=hashlib.sha256(Path(cfg['robot_yml']).read_bytes()).hexdigest(),api_calls=0,new_native_cases=0))
 try:
  for arm in ('left','right'):
   planners[arm]=CuroboPlanner(robot_origin_pose=[0,0,0,1,0,0,0],active_joints_name=['joint'+str(i) for i in range(1,7)],all_joints=['joint'+str(i) for i in range(1,7)],dt=.004,yml_path=cfg['robot_yml'],table_height=-.025)
  for job in read(O/'protocol.json')['jobs']:
   np.random.seed(job['seed']);torch.manual_seed(job['seed']);torch.cuda.manual_seed_all(job['seed'])
   target=[v+d for v,d in zip(job['position_m'],job['offset_xyz_m'])];t=time.monotonic()
   result=planners[job['arm']].plan_path(curr_joint_pos=job['start'],target_ee_pose=[*target,*job['quaternion_wxyz']],real_robot_pose=cfg['arm_bases'][job['arm']]);torch.cuda.synchronize()
   row=dict(job,requested_position=target,planner_status=result.get('status'),trajectory_returned='position' in result,seconds=time.monotonic()-t)
   if 'position' in result:
    path=np.asarray(result['position']);assert np.isfinite(path).all();(O/'trajectories').mkdir(exist_ok=True);np.save(O/f'trajectories/job{job["job_id"]:03}.npy',path);row['shape']=list(path.shape)
   rows.append(row);write('results.json',rows)
 finally:
  for p in planners.values():p.__del__()
 groups=[]
 for i in sorted(set(r['source_layout_id'] for r in rows)):
  for c in ['recorded_arm','candidate_fallback_arm']:
   rr=[r for r in rows if r['source_layout_id']==i and r['condition']==c];groups.append(dict(source_layout_id=i,condition=c,calls=len(rr),trajectories=sum(x['trajectory_returned'] for x in rr)))
 assert len(rows)==12;write('summary.json',dict(state='completed',solver_calls=12,new_native_cases=0,api_calls=0,lab_gpu_used=False,groups=groups));print(json.dumps(groups),flush=True)
def main():
 assert not (O/'status.json').exists();write('status.json',dict(state='waiting_for_idle_gpu',pid=os.getpid()))
 deadline=time.monotonic()+600
 while True:
  try:idle();break
  except AssertionError:
   if time.monotonic()>deadline:raise
   time.sleep(5)
 cfg=read(P/'environment.json');env=dict(os.environ,**cfg['policy_environment']);env['PYTHONPATH']=':'.join(p for p in env['PYTHONPATH'].split(':') if not any(t in p for t in ['37_gripper_command_contract','36_postgrasp_diagnosis','35_trajectory_contract']));env['PYTHONDONTWRITEBYTECODE']='1'
 with (O/'worker.log').open('w') as f:
  p=subprocess.Popen([cfg['policy_python'],'-B',str(O/'destination_probe.py'),'worker'],env=env,stdout=f,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True);write('status.json',dict(state='running',pid=os.getpid(),worker_pid=p.pid));code=p.wait(timeout=900)
 assert code==0,'Worker failed; no native zeros assigned';assert read(O/'summary.json')['solver_calls']==12
 write('gpu-after.json',dict(processes=smi(['--query-compute-apps=pid','--format=csv,noheader']),gpu=smi(['--query-gpu=memory.used,utilization.gpu','--format=csv,noheader'])))
 write('status.json',dict(state='completed',pid=os.getpid(),solver_calls=12,native_cases=0,api_calls=0,utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
if __name__=='__main__':
 try:worker() if len(sys.argv)>1 else main()
 except BaseException as e:write('failure.json',dict(error=repr(e),traceback=traceback.format_exc()));raise
