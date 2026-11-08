"""One bounded sequential route, no API, training or lab GPU use."""
import datetime,fcntl,json,os,subprocess,sys,traceback
from pathlib import Path
O=Path(__file__).resolve().parent
def status(state,**x):
    v=dict(state=state,pid=os.getpid(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),api_calls=0,paid_cost_usd=0,lab_gpu_used=False,**x)
    tmp=O/'route-status.tmp';tmp.write_text(json.dumps(v,indent=2)+'\n');tmp.replace(O/'route-status.json');print(json.dumps(v),flush=True)
lock=(O/'route.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not (O/'route-completed.json').exists()
jobs=['cpu_single_cycle.py','reference/cpu_boundary.py','run_native.py','analyze_native.py','validate_native.py','analyze_sidecar.py','reference/run_reference.py','reference/validate_reference.py']
try:
    assert not subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip(),'GPU occupied; do not interfere'
    for name in jobs:
        status('running',step=name)
        with (O/(name.replace('/','_')+'.stdout.log')).open('w') as out,(O/(name.replace('/','_')+'.stderr.log')).open('w') as err:
            p=subprocess.Popen([sys.executable,'-B',str(O/name)],stdout=out,stderr=err,cwd=O)
            status('running',step=name,child_pid=p.pid)
            code=p.wait()
        if code:raise RuntimeError(name+' failed with '+str(code)+'; preserve partial evidence, no automatic replay')
    (O/'route-completed.json').write_text(json.dumps(dict(state='native_and_validation_completed',native_cases=10,api_calls=0,lab_gpu_used=False),indent=2)+'\n')
    status('native_and_validation_completed',native_cases=10,next='Analyze complete chain, verify videos, archive through local relay')
except BaseException as e:
    (O/'route-failure.json').write_text(json.dumps(dict(error=repr(e),traceback=traceback.format_exc()),indent=2)+'\n');status('requires_diagnosis',error=repr(e));raise
