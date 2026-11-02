"""Finish code-program preparation and a dual-VLA check after background downloads."""
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path('/mnt/data/physical-RSI')
OUT=Path(sys.argv[1]);OUT.mkdir(parents=True,exist_ok=True)
status={'api_calls':0,'agent_enabled':False,'programs_prepared':False}


def save(stage,**data):
    status.update(stage=stage,utc=datetime.now(timezone.utc).isoformat(),**data)
    temp=OUT/'status.json.tmp';temp.write_text(json.dumps(status,indent=2)+'\n');temp.replace(OUT/'status.json')


def pointer(name):
    return Path(json.loads((ROOT/'result'/name).read_text())['directory'])


def wait_until(test,seconds=7200):
    end=time.monotonic()+seconds
    while not test():
        if time.monotonic()>end:raise TimeoutError('Offline setup dependency wait timed out')
        time.sleep(20)


try:
    save('waiting_for_assets')
    installer=pointer('CURRENT_ASSET_INSTALL.json')
    def installed():
        state=json.loads((installer/'status.json').read_text())['state']
        if state=='failed':raise RuntimeError('Asset installer failed; inspect its log')
        return state=='assets_installed'
    wait_until(installed)
    repo=ROOT/'code/RoboDojo';runtime=repo/'XPolicyLab/policy/physicalRSI/runtime'
    python=ROOT/'models/skill-assets/implementations/openpi/.venv/bin/python'
    env=os.environ.copy();env.update(PYTHONPATH=':'.join(map(str,[runtime,repo,repo/'XPolicyLab'])),
        XLA_PYTHON_CLIENT_PREALLOCATE='false',OPENPI_DATA_HOME=str(ROOT/'cache/openpi'),
        XDG_CACHE_HOME=str(ROOT/'cache/xdg'),HF_HOME=str(ROOT/'cache/huggingface'),TMPDIR=str(ROOT/'cache/tmp'))
    programs=ROOT/'models/skill-assets/implementations/code-skills'
    save('preparing_code_programs')
    if not (programs/'programs.json').exists():
        with (OUT/'prepare-programs.log').open('w') as log:
            subprocess.run([str(python),'-m','PhysicalRSI_baselines.robodojo.prepare_code_programs',str(programs)],
                           cwd=repo,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=1200)
    package=json.loads((programs/'programs.json').read_text())
    save('waiting_for_fixed_episode',programs_prepared=True,
         program_names=[entry['name'] for entry in package['programs']])
    fixed=pointer('CURRENT_FIXED_EPISODE.json')
    wait_until(lambda:json.loads((fixed/'status.json').read_text())['stage'] in ['complete','failed'])
    sparse=pointer('CURRENT_FIXED_SPARSE_EPISODE.json')
    wait_until(lambda:json.loads((sparse/'status.json').read_text())['stage'] in ['complete','failed'])
    observation=fixed/'first_observation.npz'
    if not observation.exists():
        raise RuntimeError('Fixed policy test produced no native observation; dual inference check awaits its repair')
    save('checking_both_vla_routes')
    with (OUT/'dual-vla.log').open('w') as log:
        subprocess.run(['timeout','--kill-after=30','1800',str(python),str(ROOT/'result/cloud_dual_vla_check.py'),
                        '--output',str(OUT/'dual-vla'),'--observation',str(observation)],
                       cwd=repo,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    result=json.loads((OUT/'dual-vla/result.json').read_text())
    if not result['passed']:raise RuntimeError('Dual VLA validation failed')
    save('offline_setup_complete',dual_vla_passed=True,
         agent_status='Requires fresh private credentials and explicit model/endpoint configuration')
except Exception as exc:
    save('failed',error={'type':type(exc).__name__,'message':str(exc)})
    raise
