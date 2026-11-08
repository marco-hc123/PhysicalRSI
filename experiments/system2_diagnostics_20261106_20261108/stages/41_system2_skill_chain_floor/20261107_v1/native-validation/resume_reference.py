"""Resume only the never-executed reference after a reviewed launcher repair."""
import datetime,json,os,subprocess,sys,traceback
from pathlib import Path
O=Path(__file__).resolve().parent
def status(state,**x):
    v=dict(state=state,pid=os.getpid(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),api_calls=0,paid_cost_usd=0,lab_gpu_used=False,**x)
    (O/'route-status.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v),flush=True)
assert json.loads((O/'analysis/independent-validation.json').read_text())['state']=='passed'
assert json.loads((O/'reference/deployment-repair.json').read_text())['native_cases_before_repair']==0
assert not (O/'reference/native').exists()
try:
    for name in ['reference/run_reference.py','reference/validate_reference.py']:
        status('running',step=name,resume='Reference startup only; five candidate episodes reused without rerun')
        with (O/(name.replace('/','_')+'.v2.stdout.log')).open('w') as out,(O/(name.replace('/','_')+'.v2.stderr.log')).open('w') as err:
            p=subprocess.Popen([sys.executable,'-B',str(O/name)],cwd=O,stdout=out,stderr=err)
            status('running',step=name,child_pid=p.pid)
            assert p.wait()==0,name+' failed; inspect preserved evidence'
    (O/'route-completed.json').write_text(json.dumps(dict(state='native_and_validation_completed',native_cases=10,api_calls=0,lab_gpu_used=False),indent=2)+'\n')
    status('native_and_validation_completed',native_cases=10,next='Chain analysis and verified lab archive')
except BaseException as e:
    (O/'route-failure.json').write_text(json.dumps(dict(error=repr(e),traceback=traceback.format_exc()),indent=2)+'\n');status('requires_diagnosis',error=repr(e));raise
