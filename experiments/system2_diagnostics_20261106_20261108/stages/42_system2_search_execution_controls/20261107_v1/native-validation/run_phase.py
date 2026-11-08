"""One native phase, validation and analysis; fail closed on deployment errors."""
import datetime,fcntl,json,os,subprocess,sys,traceback
from pathlib import Path
R=Path(__file__).resolve().parent
PY='/mnt/data/physical-RSI/models/skill-assets/implementations/openpi/.venv/bin/python'
phase=sys.argv[1]
assert phase in ['parent','sampling','repair','rebind','round2','heldout']
lock=(R/(phase+'.lock')).open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
def status(state,**kw):
 p=R/(phase+'-status.json');p.write_text(json.dumps(dict(state=state,phase=phase,pid=os.getpid(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**kw),indent=2)+'\n')
try:
 assert not (R/phase).exists(),'Existing phase requires reconciliation, never blind rerun'
 compute=subprocess.run(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],capture_output=True,text=True,check=True).stdout.strip()
 assert not compute,'GPU in use; do not start competing native jobs'
 jobs=[('prepare',R/'prepare_phase.py',[phase]),('execute',R/phase/'run_native.py',[]),('analyze',R/phase/'analyze_native.py',[]),('validate',R/phase/'validate_native.py',[])]
 for kind,script,args in jobs:
  status(kind,script=str(script))
  with (R/(phase+'-'+kind+'.stdout.log')).open('w') as out,(R/(phase+'-'+kind+'.stderr.log')).open('w') as err:
   p=subprocess.Popen([PY,'-B',str(script)]+args,stdout=out,stderr=err,stdin=subprocess.PIPE,cwd=R)
   status(kind,script=str(script),child_pid=p.pid)
   rc=p.wait();p.stdin.close()
  if rc:raise RuntimeError(kind+' exit '+str(rc))
 status('completed',validation=str(R/phase/'analysis/independent-validation.json'))
except BaseException as e:
 status('stopped_for_diagnosis',error=str(e),traceback=traceback.format_exc(),policy_zero_score=False)
 raise
