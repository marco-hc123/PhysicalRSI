"""Single approved H100: historical planning and pretrained inference acceptance."""
import ctypes, datetime, hashlib, json, os, resource, subprocess, sys, time, traceback
from pathlib import Path
R=Path('/mnt/data/joey_tr/physical-RSI')
O=R/'result/28_h100_offline_acceptance/20261104_v3'
GPU='GPU-a84ba1a7-488b-54cf-eb02-6ded6cf3f94f'
D=R/'result/21_system2_failure_mechanisms/36_system2_mechanism_20261031T010000Z_v3'
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def read(p):return json.loads(Path(p).read_text())
def write(p,v):
 p=O/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,default=str,allow_nan=False)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def guard():
 lib=ctypes.CDLL(None,use_errno=True);abi=lib.syscall(444,0,0,1)
 if abi<3:raise RuntimeError('Landlock ABI >=3 required')
 class Rules(ctypes.Structure):_fields_=[('rights',ctypes.c_uint64)]
 class Beneath(ctypes.Structure):
  _pack_=1;_fields_=[('rights',ctypes.c_uint64),('fd',ctypes.c_int32)]
 rights=(1<<1)|sum(1<<n for n in range(4,15));r=Rules(rights)
 fd=lib.syscall(444,ctypes.byref(r),ctypes.sizeof(r),0)
 if fd<0:raise OSError(ctypes.get_errno(),'create Landlock')
 devices=['/dev/null','/dev/nvidiactl','/dev/nvidia-uvm','/dev/nvidia-uvm-tools','/dev/nvidia1']
 allow=[(O,rights),(Path('/proc/self/task'),(1<<1)|(1<<14))]+[(Path(p),(1<<1)|(1<<14)) for p in devices if Path(p).exists()]
 for p,access in allow:
  pfd=os.open(p,os.O_PATH|os.O_CLOEXEC);b=Beneath(access,pfd)
  if lib.syscall(445,fd,1,ctypes.byref(b),0)<0:raise OSError(ctypes.get_errno(),'Landlock rule')
  os.close(pfd)
 if lib.prctl(38,1,0,0,0)!=0 or lib.syscall(446,fd,0)!=0:raise OSError(ctypes.get_errno(),'enforce Landlock')
 os.close(fd)
 return {'abi':abi,'disk_write_root':str(O),'device_io':[str(p) for p,a in allow[1:]],'gpu_uuid':GPU}
def configure():
 os.umask(0o077);resource.setrlimit(resource.RLIMIT_CORE,(0,0))
 for k,v in {'CUDA_VISIBLE_DEVICES':GPU,'PYTHONDONTWRITEBYTECODE':'1','XLA_PYTHON_CLIENT_PREALLOCATE':'false','OMP_NUM_THREADS':'4','OPENBLAS_NUM_THREADS':'4','MKL_NUM_THREADS':'4','CUDA_HOME':'/usr/local/cuda-12.8'}.items():os.environ[k]=v
 for k,v in {'TMPDIR':'tmp','XDG_CACHE_HOME':'cache/xdg','XDG_CONFIG_HOME':'cache/config','XDG_DATA_HOME':'cache/data','CUDA_CACHE_PATH':'cache/cuda','TORCH_EXTENSIONS_DIR':'cache/torch_extensions','TRITON_CACHE_DIR':'cache/triton','HF_HOME':'cache/huggingface','JAX_COMPILATION_CACHE_DIR':'cache/jax','MPLCONFIGDIR':'cache/matplotlib','NUMBA_CACHE_DIR':'cache/numba','OPENPI_DATA_HOME':'cache/openpi','WARP_CACHE_PATH':'cache/warp','CUROBO_CACHE_DIR':'cache/curobo'}.items():
  p=O/v;p.mkdir(parents=True,exist_ok=True);os.environ[k]=str(p)
 os.environ['PATH']='/usr/local/cuda-12.8/bin:'+os.environ['PATH']
 os.environ['LD_LIBRARY_PATH']='/usr/local/cuda-12.8/lib64:'+os.environ.get('LD_LIBRARY_PATH','')
 os.chdir(O)
def mapped(p):
 s=str(p).removeprefix('/mnt/data/physical-RSI/');m=read(R/'configs/organization/path-mapping.json')['mapping']
 for k in sorted(m,key=len,reverse=True):
  if s==k or s.startswith(k+'/'):return R/(m[k]+s[len(k):])
 raise ValueError('Unmapped '+s)
def smi(args):return subprocess.check_output(['nvidia-smi',*args],text=True,timeout=15).strip()
def check_idle():
 rows=smi(['--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader'])
 if GPU in rows:raise RuntimeError('Selected GPU already has compute processes: '+rows)
 line=smi(['-i',GPU,'--query-gpu=memory.used,utilization.gpu','--format=csv,noheader,nounits'])
 mem,util=[int(x.strip()) for x in line.split(',')]
 if mem>100 or util>0:raise RuntimeError('Selected GPU not idle: '+line)
 return {'compute_processes':rows,'selected_gpu_memory_mib':mem,'utilization_percent':util,'at':now()}
def basic():
 import numpy as np,torch
 assert torch.cuda.is_available() and torch.cuda.device_count()==1
 a=torch.ones((64,64),device='cuda');b=a@a;torch.cuda.synchronize();np.testing.assert_allclose(b.cpu(),64)
 result={'torch_version':torch.__version__,'torch_cuda':torch.version.cuda,'gpu':torch.cuda.get_device_name(0),'visible_devices':1,'torch_passed':True}
 del a,b;torch.cuda.empty_cache()
 import jax,jax.numpy as jnp
 assert len(jax.devices('gpu'))==1
 x=jax.jit(lambda x:x@x)(jnp.ones((64,64)));x.block_until_ready();np.testing.assert_allclose(np.asarray(x),64)
 result.update(jax_version=jax.__version__,jax_passed=True,jax_devices=[str(x) for x in jax.devices()]);return result
def planning():
 proto=read(D/'reachability-protocol.json');assert len(proto['jobs'])==24
 fingerprints=[]
 for p,h in proto['inputs'].items():
  mp=mapped(p);assert sha(mp)==h;fingerprints.append({'original':p,'path':str(mp),'sha256':h})
 cfg=read(R/'result/17_system2_iterations/31_system2_final_validation_20261030T121000Z/runtime.json');pc=cfg['policy_spec']['configuration']
 source=mapped(pc['robot_yml']);code=source.parents[3]
 sys.path.insert(0,str(code));sys.path.insert(0,str(R/'repos/lab-runtime/curobo'))
 import numpy as np,torch,yaml,warp
 warp.config.kernel_cache_dir=str(O/'cache/warp')
 import curobo._src.runtime as cruntime
 cruntime.cache_dir=str(O/'cache/curobo')
 assert torch.cuda.device_count()==1
 y=source.read_text();replacements={}
 # Only migrate old absolute paths in a copied YAML; preserve geometry and solver configuration.
 for s in set(__import__('re').findall(r'/mnt/data/physical-RSI/[^\s\"\']+',y)):
  replacements[s]=str(mapped(s));y=y.replace(s,replacements[s])
 local_yml=O/'planning/robot-paths-only.yml';local_yml.parent.mkdir(exist_ok=True);local_yml.write_text(y)
 write('planning/protocol.json',{'historical_protocol':str(D/'reachability-protocol.json'),'sha256':sha(D/'reachability-protocol.json'),'input_hashes':fingerprints,'jobs':proto['jobs'],'yaml_path_substitutions':replacements,'qualifications':['24 offline solver calls; not physical execution','Other-arm contrast also changes quaternion','Three seeds do not prove geometric impossibility','Only absolute asset paths migrated; no collision/solver edits']})
 from rdj_v1_classify_objects.curobo_planner import CuroboPlanner
 planners={};results=[]
 try:
  for arm in ('left','right'):
   planners[arm]=CuroboPlanner(robot_origin_pose=[0,0,0,1,0,0,0],active_joints_name=['joint'+str(i) for i in range(1,7)],all_joints=['joint'+str(i) for i in range(1,7)],dt=.004,yml_path=str(local_yml),table_height=-.025)
  for i,job in enumerate(proto['jobs']):
   np.random.seed(job['seed']);torch.manual_seed(job['seed']);torch.cuda.manual_seed_all(job['seed']);a=job['action'];t=time.monotonic()
   res=planners[a['arm']].plan_path(curr_joint_pos=job['start'],target_ee_pose=[*a['position_m'],*a['quaternion_wxyz']],real_robot_pose=pc['arm_bases'][a['arm']]);torch.cuda.synchronize()
   row=dict(job,planner_status=res.get('status'),seconds=time.monotonic()-t)
   if 'position' in res:
    traj=np.asarray(res['position']);np.save(O/f'planning/trajectory_{i:02}.npy',traj);row.update(trajectory_shape=list(traj.shape),finite=bool(np.isfinite(traj).all()))
   results.append(row);write(f'planning/probe_{i:02}.json',row);write('planning/results.json',results);print('PROBE',i,row['planner_status'],flush=True)
 finally:
  for p in planners.values():p.__del__()
 return {'calls':len(results),'results':results,'new_native_episodes':0}
def policy(which):
 import numpy as np,jax
 assert len(jax.devices('gpu'))==1
 from PhysicalRSI_baselines.robodojo.skills.pi05 import Model as Pi
 from PhysicalRSI_baselines.robodojo.skills.sparse import Model as Sparse
 ck=R/'models/recorded_policy_assets/skill-assets/checkpoints'/('pi05' if which=='pi05' else 'pi05-sparse-memory')
 cfg={'task_name':'classify_objects','action_type':'joint','env_cfg_type':'arx_x5','model_path':str(ck),'repo_id':'arx_x5_sim' if which=='pi05' else 'robodojo_arx_x5_all35','train_config_name':'pi05_base_aloha_full_sim_arx-x5_seed_0' if which=='pi05' else 'pi05_sparse_mem_robodojo_all35_80k','require_gpu':True,'seed':0}
 out=O/which;out.mkdir(exist_ok=True);write(which+'/config.json',cfg)
 t=time.monotonic();model=(Pi if which=='pi05' else Sparse)(cfg);load_seconds=time.monotonic()-t
 # Deterministic synthetic input is hardware/contract acceptance, never task evidence.
 rng=np.random.default_rng(0);images={k:{'color':rng.integers(0,256,(224,224,3),dtype=np.uint8)} for k in ['cam_head','cam_left_wrist','cam_right_wrist']}
 obs={'env_idx':0,'instruction':'Sort objects of the same category into the same basket.','state':{'left_arm_joint_state':np.zeros(6,np.float32),'right_arm_joint_state':np.zeros(6,np.float32),'left_ee_joint_state':np.array([.04],np.float32),'right_ee_joint_state':np.array([.04],np.float32)},'vision':images}
 np.savez_compressed(out/'synthetic-input.npz',**{k:v['color'] for k,v in images.items()},**obs['state'])
 outputs=[]
 for i in range(3):
  # 26 updates make the stride-25 sparse history nonempty before the second inference.
  updates=26 if i==1 else 1
  for _ in range(updates):model.update_obs_batch([obs])
  masks=None
  if which=='sparse':masks={k:np.asarray(v).tolist() for k,v in model.observation_window['history_image_masks'].items()}
  tick=time.monotonic();actions=model.get_action_batch(env_idx_list=[0])[0];elapsed=time.monotonic()-tick
  arrays={k:np.asarray(v) for k,v in actions.items()} if isinstance(actions,dict) else {'actions':np.asarray(actions)}
  assert all(np.isfinite(a).all() for a in arrays.values())
  np.savez_compressed(out/f'actions_{i}.npz',**arrays)
  outputs.append({'call':i,'seconds':elapsed,'shape':{k:list(a.shape) for k,a in arrays.items()},'all_finite':True,'sparse_masks':masks});write(which+'/inference.json',outputs);print('INFERENCE',which,i,elapsed,flush=True)
 model.reset();reset_ok=model.observation_window is None
 if which=='sparse':reset_ok=reset_ok and not model._visual_history.session_ids
 assert reset_ok
 return {'loaded_existing_checkpoint':True,'load_seconds':load_seconds,'calls':outputs,'reset_verified':reset_ok,'input':'synthetic seed 0 RGB/state; not task observation','native_episodes':0,'api_calls':0}
def worker(mode):
 configure();isolation=guard();write(mode+'/write-isolation.json',isolation);start=time.monotonic()
 try:
  driver=ctypes.CDLL('libcuda.so.1');code=driver.cuInit(0)
  write(mode+'/driver-init.json',{'cuInit_return':code,'adaptation':'Explicit driver init inside confinement, before torch/JAX import; no system configuration changes'})
  if code:raise RuntimeError('cuInit failed '+str(code))
  result=basic() if mode=='basic' else planning() if mode=='planning' else policy(mode)
  write(mode+'/completion.json',{'state':'passed','started_seconds':start,'elapsed_seconds':time.monotonic()-start,'result':result,'pid':os.getpid(),'finished_utc':now()})
 except BaseException as e:
  write(mode+'/completion.json',{'state':'failed','error':type(e).__name__+': '+str(e),'traceback':traceback.format_exc(),'elapsed_seconds':time.monotonic()-start,'finished_utc':now()});traceback.print_exc();sys.exit(1)
def main():
 if (O/'status.json').exists():raise RuntimeError('Batch exists; inspect before resume')
 O.mkdir(parents=True,exist_ok=True);configure();write('write-isolation.json',guard());write('gpu-before.json',check_idle())
 write('protocol.json',{'created_utc':now(),'gpu_uuid':GPU,'physical_gpu':1,'maximum_visible_gpus':1,'training':False,'rgb_simulation':False,'api_calls':0,'source_change_policy':'No existing environment/source edits; new outputs and copied path-only config in this batch','phases':['basic','planning','pi05','sparse'],'policy_input_scope':'Synthetic hardware inference acceptance; not task-success evaluation','planner_scope':'Exact archived 24-job reachability protocol; do not count as episodes'})
 results=[]
 for mode in ['basic','planning','pi05','sparse']:
  write(mode+'/gpu-idle-before.json',check_idle())
  py=R/'envs'/('simulator' if mode=='planning' else 'policy')/'bin/python'
  with (O/(mode+'.log')).open('x') as log:
   p=subprocess.Popen([str(py),'-B',str(O/'run_gpu_batch.py'),'worker',mode],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
   write('status.json',{'state':'running','phase':mode,'controller_pid':os.getpid(),'child_pid':p.pid,'gpu_uuid':GPU,'started_utc':now(),'completed':results});t=time.monotonic()
   while p.poll() is None:
    with (O/'gpu_samples.jsonl').open('a') as f:f.write(json.dumps({'at':now(),'phase':mode,'query':smi(['--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader'])})+'\n')
    if time.monotonic()-t>1800:
     import signal
     os.killpg(p.pid,signal.SIGTERM)
     try:p.wait(15)
     except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
     write(mode+'/timeout.json',{'timeout_seconds':1800});break
    time.sleep(5)
   results.append({'phase':mode,'exit_code':p.returncode,'elapsed_seconds':time.monotonic()-t})
  print('PHASE',mode,results[-1],flush=True)
  if mode=='basic' and p.returncode:break
 write('status.json',{'state':'complete' if all(x['exit_code']==0 for x in results) else 'complete_with_failures','controller_pid':None,'child_pid':None,'results':results,'finished_utc':now(),'native_episodes':0,'api_calls':0})
 write('gpu-after.json',{'at':now(),'gpus':smi(['--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader']),'processes':smi(['--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader'])})
if __name__=='__main__':
 if len(sys.argv)>1:worker(sys.argv[2])
 else:main()
