"""Continue offline diagnostics once the native batch and base analysis finish."""
from pathlib import Path
import datetime,fcntl,json,os,shlex,subprocess,time,traceback
from remote_ops import H,L,LAB
lock=(H/'diagnostic-controller.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
def state(value,**extra):
    d=dict(state=value,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),pid=os.getpid(),**extra)
    (H/'diagnostic-status.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d),flush=True)
try:
    state('waiting_for_base_analysis');deadline=time.monotonic()+7200
    while True:
        d=json.loads((H/'completion-status.json').read_text())
        if d['stage']=='requires_diagnosis':raise RuntimeError('Base analysis needs review')
        if d['stage']=='native_archive_verified':break
        if time.monotonic()>deadline:raise TimeoutError('No experiment changed')
        time.sleep(20)
    for name in ['finalize_loop.py','replay_terminal_reason.py','audit_observation_coverage.py','audit_transport_tracking.py','audit_scoring_conditions.py','extract_tracking_frames.py']:
        state('running_cpu_diagnostic',script=name)
        env='simulator' if name=='audit_scoring_conditions.py' else 'analysis'
        command='CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 /mnt/data/joey_tr/physical-RSI/envs/'+env+'/bin/python -B '+shlex.quote(L+'/'+name)
        p=subprocess.run(LAB+[command],capture_output=True,text=True,timeout=240)
        (H/(name+'.stdout.log')).write_text(p.stdout);(H/(name+'.stderr.log')).write_text(p.stderr)
        if p.returncode:raise RuntimeError(name+': '+p.stderr[-1500:])
    state('diagnostics_ready_for_review',new_native_cases=0,new_api_calls=0,lab_gpu_used=False)
except BaseException as e:
    state('requires_diagnosis',error=repr(e),traceback=traceback.format_exc(),experiment_unchanged=True)
    raise
