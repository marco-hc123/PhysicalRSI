"""Wait for the existing controller, verify results and return them to lab.

This script never starts or retries a native experiment. Network/deployment
errors are preserved for explicit diagnosis instead of being scored as zero.
"""
import datetime
import json
from pathlib import Path
import shlex
import subprocess
import sys
import time
import traceback
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'rgb_supplement_20261105'))
from remote import CLOUD
HERE=Path(__file__).resolve().parent
C='/mnt/data/physical-RSI/result/33_retreat_recovery_20261106'
PY='/mnt/data/physical-RSI/models/skill-assets/implementations/openpi/.venv/bin/python'
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def state(stage,**kwargs):
    d=dict(stage=stage,updated_utc=utc(),local_watcher_pid=__import__('os').getpid(),cloud_root=C,**kwargs)
    (HERE/'completion-status.json').write_text(json.dumps(d,indent=2)+'\n')
    print(json.dumps(d),flush=True)
def remote(script,python='python3',timeout=120):
    p=subprocess.run(CLOUD+['sudo -n env PYTHONDONTWRITEBYTECODE=1 '+shlex.quote(python)+' -B '+shlex.quote(C+'/'+script)],capture_output=True,text=True,timeout=timeout)
    (HERE/(script+'.stdout.log')).write_text(p.stdout)
    (HERE/(script+'.stderr.log')).write_text(p.stderr)
    if p.returncode:raise RuntimeError(script+': '+p.stderr[-1500:])
    return p.stdout
try:
    state('watching_existing_controller')
    last=None;deadline=time.monotonic()+10800
    while True:
        cmd='sudo -n cat '+shlex.quote(C+'/native-campaign/status.json')
        p=subprocess.run(CLOUD+[cmd],capture_output=True,text=True,timeout=35)
        if p.returncode:raise RuntimeError('Controller status read failed: '+p.stderr[-1000:])
        d=json.loads(p.stdout);marker=(d['state'],d.get('condition'),d.get('completed_cases'))
        if marker!=last:state('native_status',native=d);last=marker
        if d['state']=='stopped_for_diagnosis':raise RuntimeError('Native controller requires diagnosis: '+d.get('error','unknown'))
        if d['state']=='diagnostic_matrix_completed':
            assert d['completed_cases']==10
            break
        if time.monotonic()>deadline:raise TimeoutError('Watcher deadline; native job left unchanged')
        time.sleep(20)
    time.sleep(3)
    state('native_complete_analyzing',native=d)
    remote('analyze_native.py',timeout=240)
    state('independent_validation')
    remote('validate_native.py',python=PY,timeout=360)
    state('packaging_immutable_evidence')
    remote('package_native.py',timeout=300)
    state('returning_to_lab')
    p=subprocess.run([sys.executable,str(HERE/'return_archive.py')],capture_output=True,text=True,timeout=3600)
    (HERE/'return-archive.stdout.log').write_text(p.stdout);(HERE/'return-archive.stderr.log').write_text(p.stderr)
    if p.returncode:raise RuntimeError('Return archive failed: '+p.stderr[-1500:])
    receipt=json.loads((HERE/'return-status.json').read_text())
    state('native_archive_verified',archive=receipt)
except BaseException as exc:
    state('requires_diagnosis',error=type(exc).__name__+': '+str(exc),traceback=traceback.format_exc(),native_job_interrupted=False)
    raise
