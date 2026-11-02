"""Run one registered stage with an exclusive lock and no automatic attempt replay."""
from pathlib import Path
from datetime import datetime,timezone
import json,sys,os,subprocess,fcntl,hashlib
O=Path(sys.argv[1]);stage=sys.argv[2];S=O/'analysis-sources'
def write(p,v):
 t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');t.replace(p)
lock=(O/'controller.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
state=dict(stage=stage,pid=os.getpid(),complete=False,jobs=[],started_utc=datetime.now(timezone.utc).isoformat())
def save(**kw):
 state.update(kw,utc=datetime.now(timezone.utc).isoformat());write(O/(stage+'-controller-status.json'),state);write(O.parent/'CURRENT_STEP7.json',dict(directory=str(O),**state));print(json.dumps(state),flush=True)
try:
 protocol=json.loads((O/'protocol.json').read_text())
 for name,h in json.loads((O/'procedure-registration.json').read_text()).items():assert hashlib.sha256((S/name).read_bytes()).hexdigest()==h,name
 save(current='assets')
 if stage=='smoke':
  with (O/'assets.log').open('x') as log:subprocess.run(['python3',str(S/'step7_assets.py'),str(O)],stdout=log,stderr=subprocess.STDOUT,check=True)
 elif stage=='formal':assert json.loads((O/'formal-freeze.json').read_text())['approved_after_smoke']
 else:raise ValueError(stage)
 for job in [j for j in protocol['jobs'] if j['stage']==stage]:
  save(current=job['name'])
  assert not (O/job['name']).exists(),'Existing attempt: reconcile before resume'
  with (O/(job['name']+'.launch.log')).open('x') as log:subprocess.run(['python3',str(S/'cloud_comparison_run.py'),'--suite',str(O),'--job',job['name']],stdout=log,stderr=subprocess.STDOUT,check=True)
  result=json.loads((O/job['name']/'status.json').read_text());assert result['complete'];state['jobs'].append(dict(name=job['name'],successes=result['successes'],native_completed=result['native_completed'],counted_errors=result['counted_episode_errors']));save()
 save(complete=True,current=None,stage=stage+'_complete')
except BaseException as e:
 save(stage='needs_review',error_type=type(e).__name__,error=str(e));raise
