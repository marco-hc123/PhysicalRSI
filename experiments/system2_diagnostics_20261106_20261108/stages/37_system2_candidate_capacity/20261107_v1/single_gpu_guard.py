"""Single approved H100: historical planning and pretrained inference acceptance."""
import ctypes, datetime, hashlib, json, os, resource, subprocess, sys, time, traceback
from pathlib import Path
R=Path('/mnt/data/joey_tr/physical-RSI')
O=R/'result/28_h100_offline_acceptance/20261104_v5'
GPU='GPU-16ecfd7e-5125-c528-1ab7-625967fc01d1'
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
 devices=['/dev/null','/dev/nvidiactl','/dev/nvidia-uvm','/dev/nvidia-uvm-tools','/dev/nvidia0']
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
