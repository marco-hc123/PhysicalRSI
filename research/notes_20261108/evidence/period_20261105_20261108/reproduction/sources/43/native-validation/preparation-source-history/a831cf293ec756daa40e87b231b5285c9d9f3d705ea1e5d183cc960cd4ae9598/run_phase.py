"""Sequential phase runner; no automatic retry of incomplete native episodes."""
import datetime,fcntl,json,os,subprocess,sys,traceback
from pathlib import Path
O=Path(__file__).resolve().parent
PY='/mnt/data/physical-RSI/models/skill-assets/implementations/openpi/.venv/bin/python'
phase=sys.argv[1]
assert phase.replace('-','').replace('_','').isalnum()
lock=(O/(phase+'.lock')).open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
def status(state,**kw):
    p=O/(phase+'-status.json');t=p.with_suffix('.tmp');t.write_text(json.dumps(dict(state=state,phase=phase,pid=os.getpid(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**kw),indent=2)+'\n');t.replace(p)
try:
    assert not (O/phase).exists(),'Existing phase needs reconciliation'
    compute=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip()
    assert not compute,'GPU busy; no competing native work'
    for kind,script,args in [('prepare',O/'prepare_phase.py',[phase]),('execute',O/phase/'run_native.py',[]),('analyze',O/phase/'analyze_native.py',[])]:
        with (O/(phase+'-'+kind+'.stdout.log')).open('w') as out,(O/(phase+'-'+kind+'.stderr.log')).open('w') as err:
            p=subprocess.Popen([PY,'-B',str(script)]+args,stdout=out,stderr=err,stdin=subprocess.PIPE,cwd=O)
            status(kind,child_pid=p.pid);rc=p.wait();p.stdin.close()
        if rc:raise RuntimeError(kind+' exit '+str(rc))
    status('completed')
except BaseException as e:
    status('stopped_for_diagnosis',error=str(e),traceback=traceback.format_exc(),policy_zero_score=False);raise
