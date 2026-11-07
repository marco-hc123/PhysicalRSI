"""Resume only the uncompleted sparse inference acceptance, preserving old attempts."""
import importlib.util,json,os,shutil,subprocess,sys,time,signal,hashlib
from pathlib import Path
R=Path('/mnt/data/joey_tr/physical-RSI')
P=R/'result/28_h100_offline_acceptance/20261104_v5'
O=P.parent/'20261104_v6_sparse'
spec=importlib.util.spec_from_file_location('gpu_acceptance',P/'run_gpu_batch.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.O=O
if len(sys.argv)>1 and sys.argv[1]=='worker':
 m.worker('sparse');sys.exit(0)
if (O/'status.json').exists():raise RuntimeError('Attempt exists; inspect before resume')
O.mkdir(parents=True,exist_ok=True);m.configure();m.write('gpu-before.json',m.check_idle())
tok=P/'cache/openpi/big_vision/paligemma_tokenizer.model'
if tok.exists():
 dst=O/'cache/openpi/big_vision/paligemma_tokenizer.model';dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(tok,dst)
 m.write('tokenizer-provenance.json',{'source':str(tok),'sha256':m.sha(tok),'copied_sha256':m.sha(dst)})
m.write('protocol.json',{'created_utc':m.now(),'mode':'sparse-only','gpu_uuid':m.GPU,'visible_gpu_limit':1,'worker_source':str(P/'run_gpu_batch.py'),'worker_sha256':m.sha(P/'run_gpu_batch.py'),'new_api_calls':0,'new_native_episodes':0,'training':False,'input_scope':'Deterministic synthetic RGB/state; 3 inference calls, nonempty history and reset checks; not task scores','previous_completed':['CUDA basic','24 planning calls','pi05 3 calls','6 API candidate generations']})
with (O/'sparse.log').open('x') as log:
 p=subprocess.Popen([str(R/'envs/policy/bin/python'),'-B',str(O/'resume_sparse.py'),'worker'],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 m.write('status.json',{'state':'running','phase':'sparse','controller_pid':os.getpid(),'child_pid':p.pid,'started_utc':m.now()})
 t=time.monotonic()
 while p.poll() is None:
  with (O/'gpu_samples.jsonl').open('a') as f:f.write(json.dumps({'at':m.now(),'gpus':m.smi(['--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader'])})+'\n')
  if time.monotonic()-t>900:
   os.killpg(p.pid,signal.SIGTERM)
   try:p.wait(15)
   except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
   m.write('timeout.json',{'seconds':900});break
  time.sleep(5)
 m.write('status.json',{'state':'complete' if p.returncode==0 else 'failed','controller_pid':None,'child_pid':None,'exit_code':p.returncode,'elapsed_seconds':time.monotonic()-t,'finished_utc':m.now()})
 m.write('gpu-after.json',{'at':m.now(),'gpus':m.smi(['--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader']),'processes':m.smi(['--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader'])})
