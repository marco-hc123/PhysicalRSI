"""Recreate the saved environment package set, without a dependency upgrade."""
from pathlib import Path
import subprocess, os, json, datetime, hashlib, fcntl, sys

R=Path('/mnt/data/physical-RSI')
O=R/'result/31_rgb_supplement_20261105/environment'
O.mkdir(parents=True,exist_ok=True)
lock=(O/'bootstrap.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
F=R/'reference/result/14_protocol_freeze/23_protocol_freeze_20261029T132917Z'
UV=R/'envs/tools/uv'
PY=R/'envs/python/cpython-3.11.17-linux-x86_64-gnu/bin/python3.11'
env=os.environ.copy()
env.update(UV_CACHE_DIR=str(R/'cache/uv'),UV_PYTHON_INSTALL_DIR=str(R/'envs/python'),
           UV_HTTP_TIMEOUT='120',UV_CONCURRENT_DOWNLOADS='4',PIP_CACHE_DIR=str(R/'cache/pip'),
           TMPDIR=str(R/'cache/tmp'),XDG_CACHE_HOME=str(R/'cache/xdg'),PYTHONNOUSERSITE='1',PIP_USER='0')
for d in ['cache/tmp','cache/xdg','cache/uv','cache/pip']: (R/d).mkdir(parents=True,exist_ok=True)
def state(stage,**kw):
    d=dict(stage=stage,pid=os.getpid(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),api_calls=0)
    d.update(kw);p=O/'status.json';t=p.with_suffix('.tmp');t.write_text(json.dumps(d,indent=2));t.replace(p)
    print(json.dumps(d),flush=True)
def run(name,cmd):
    done=O/(name+'.done.json')
    if done.exists():return
    state(name)
    with (O/(name+'.log')).open('a') as f:
        p=subprocess.run([str(c) for c in cmd],env=env,stdout=f,stderr=subprocess.STDOUT)
    (O/(name+'.command.json')).write_text(json.dumps({'argv':[str(c) for c in cmd],'returncode':p.returncode},indent=2))
    if p.returncode:raise RuntimeError(name+' failed; inspect log')
    done.write_text(json.dumps({'exit_code':0,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}))

try:
    # Local editable/source-owned packages are bound only after their sources arrive.
    local={'nvidia-curobo','openpi','openpi-client','physicalrsi-runtime','xpolicylab'}
    for name,dest in [('simulator',R/'envs/simulator'),('policy',R/'models/skill-assets/implementations/openpi/.venv')]:
        if name=='policy':
            # Model/source transfer must complete before creating this environment.
            if not (R/'models/skill-assets/implementations/openpi/pyproject.toml').is_file():
                state('simulator_packages_complete_waiting_policy_source');sys.exit(0)
        if not (dest/'bin/python').exists():run(name+'-venv',[UV,'venv','--python',PY,dest])
        lines=[x.strip() for x in (F/(name+'-packages.txt')).read_text().splitlines() if x.strip() and not x.startswith('#')]
        groups={'general':[],'isaac':[],'torch':[]}
        for line in lines:
            pkg=line.split('==')[0].lower().replace('_','-')
            if pkg in local:continue
            groups['isaac' if pkg.startswith('isaacsim') else 'torch' if '+cu128' in line else 'general'].append(line)
        for group,requirements in groups.items():
            if not requirements:continue
            req=O/(name+'-'+group+'.txt');req.write_text('\n'.join(requirements)+'\n')
            index={'general':'https://mirrors.aliyun.com/pypi/simple','isaac':'https://pypi.nvidia.com','torch':'https://download.pytorch.org/whl/cu128'}[group]
            run(name+'-'+group,[UV,'pip','install','--python',dest/'bin/python','--no-deps','--index-url',index,'-r',req])
    state('package_install_complete_pending_local_source_bindings')
except BaseException as e:
    if isinstance(e,SystemExit):raise
    state('needs_review',error_type=type(e).__name__,error=str(e));raise
