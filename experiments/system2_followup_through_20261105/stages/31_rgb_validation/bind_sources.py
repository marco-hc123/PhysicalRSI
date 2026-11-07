from pathlib import Path
import os,subprocess,json,datetime,hashlib,shutil,fcntl
R=Path('/mnt/data/physical-RSI');O=R/'result/31_rgb_supplement_20261105/environment'
lock=(O/'bindings.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
env=os.environ.copy();env.update(UV_CACHE_DIR=str(R/'cache/uv'),TMPDIR=str(R/'cache/tmp'),XDG_CACHE_HOME=str(R/'cache/xdg'),UV_INDEX_URL='https://mirrors.aliyun.com/pypi/simple',CUDA_HOME='/usr/local/cuda-12.8',SETUPTOOLS_SCM_PRETEND_VERSION='0.0.post1.dev1',PYTHONNOUSERSITE='1')
U=R/'envs/tools/uv';S=R/'envs/simulator/bin/python';P=R/'models/skill-assets/implementations/openpi/.venv/bin/python'
def run(name,args):
 out=O/(name+'.done.json')
 if out.exists():return
 with (O/(name+'.log')).open('a') as f:r=subprocess.run([str(x) for x in args],env=env,stdout=f,stderr=subprocess.STDOUT)
 if r.returncode:raise RuntimeError(name+' failed')
 out.write_text(json.dumps({'argv':[str(x) for x in args],'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'returncode':0},indent=2))
try:
 run('simulator-curobo',[U,'pip','install','--python',S,'--no-deps','--no-build-isolation','-e',R/'code/RoboDojo/third_party/curobo'])
 for name,path in [('openpi',R/'models/skill-assets/implementations/openpi'),('openpi-client',R/'models/skill-assets/implementations/openpi/packages/openpi-client'),('xpolicylab',R/'code/RoboDojo/XPolicyLab'),('runtime',R/'code/RoboDojo/XPolicyLab/policy/physicalRSI/runtime')]:
  run('policy-'+name,[U,'pip','install','--python',P,'--no-deps','-e',path])
 # Restore the released OpenPI Transformers compatibility files, as in the recorded setup.
 site=Path(subprocess.check_output([str(P),'-c','import sysconfig;print(sysconfig.get_path("purelib"))'],text=True).strip())
 source=R/'models/skill-assets/implementations/openpi/src/openpi/models_pytorch/transformers_replace'
 receipt=[]
 for rel in ['models/gemma/configuration_gemma.py','models/gemma/modeling_gemma.py','models/paligemma/modeling_paligemma.py','models/siglip/modeling_siglip.py']:
  src=source/rel;dst=site/'transformers'/rel
  before=hashlib.sha256(dst.read_bytes()).hexdigest();after=hashlib.sha256(src.read_bytes()).hexdigest()
  bak=O/'transformers-original'/rel
  if not bak.exists():bak.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(dst,bak)
  if before!=after:shutil.copy2(src,dst)
  receipt.append({'relative_path':rel,'before_sha256':before,'source_sha256':after,'installed_sha256':hashlib.sha256(dst.read_bytes()).hexdigest()})
 (O/'transformers-compatibility.json').write_text(json.dumps(receipt,indent=2))
 frozen=json.loads((R/'reference/result/14_protocol_freeze/23_protocol_freeze_20261029T132917Z/environment-packages.json').read_text())
 checks={}
 for name,py in [('simulator',S),('policy',P)]:
  actual=json.loads(subprocess.check_output([str(py),'-c','import importlib.metadata as m,json,sys;print(json.dumps({"python":sys.version,"packages":{d.metadata["Name"].lower().replace("_","-"):d.version for d in m.distributions()}}))'],text=True))
  expected={x['name'].lower().replace('_','-'):x['version'] for x in frozen[name]['packages']}
  differences=[{'package':k,'expected':v,'actual':actual['packages'].get(k)} for k,v in expected.items() if actual['packages'].get(k)!=v]
  extra={k:v for k,v in actual['packages'].items() if k not in expected}
  checks[name]={'python':actual['python'],'differences':differences,'extra':extra,'expected_packages':len(expected),'actual_packages':len(actual['packages'])}
  (O/(name+'-installed-packages.json')).write_text(json.dumps(actual,indent=2))
  with (O/(name+'-pip-check.txt')).open('w') as f:
   result=subprocess.run([str(U),'pip','check','--python',str(py)],stdout=f,stderr=subprocess.STDOUT,env=env)
  checks[name]['pip_check_exit']=result.returncode
 (O/'version-comparison.json').write_text(json.dumps(checks,indent=2))
 (O/'bindings-status.json').write_text(json.dumps({'state':'source_bindings_complete','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'version_differences':sum(len(v['differences']) for v in checks.values()),'api_calls':0},indent=2))
 print(json.dumps(checks,indent=2))
except BaseException as e:
 (O/'bindings-status.json').write_text(json.dumps({'state':'needs_review','error_type':type(e).__name__,'error':str(e)},indent=2));raise
