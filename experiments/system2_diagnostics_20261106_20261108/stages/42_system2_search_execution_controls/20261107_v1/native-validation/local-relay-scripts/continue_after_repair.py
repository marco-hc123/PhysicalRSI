"""Bounded continuation after the explicitly frozen repair; never rerun a phase."""
import datetime,json,subprocess,sys,time,traceback
from remote_ops import H,C,L,LAB,CLOUD,PYTHON,call
S=H/'followup-coordinator-status.json'
def status(state,**extra):
 d=dict(state=state,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**extra);S.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d),flush=True)
def remote_json(host,path,sudo=False):
 return json.loads(call(host,f"from pathlib import Path;import json;p=Path({path!r});print(p.read_text() if p.exists() else 'null')",sudo))
def exists(path):return bool(json.loads(call(CLOUD,f"from pathlib import Path;import json;print(json.dumps(Path({path!r}).exists()))",True)))
def wait_phase(phase):
 while True:
  d=remote_json(CLOUD,C+'/'+phase+'-status.json',True)
  if d and d['state']=='completed':status(phase+'_verified');return
  if d and d['state']=='stopped_for_diagnosis':raise RuntimeError(d)
  status('waiting_native',phase=phase,controller=d)
  time.sleep(55)
def run_script(name,args,expected,tag):
 if exists(C+'/'+expected):status('existing_artifact_preserved',artifact=expected);return
 code=f'''import subprocess,json
from pathlib import Path
r=Path({C!r});assert not (r/{expected!r}).exists()
with (r/({tag!r}+'.stdout.log')).open('x') as out,(r/({tag!r}+'.stderr.log')).open('x') as err:
 p=subprocess.Popen([{PYTHON!r},'-B',str(r/{name!r})]+{args!r},stdin=subprocess.PIPE,stdout=out,stderr=err,cwd=r)
 (r/({tag!r}+'-process.json')).write_text(json.dumps(dict(pid=p.pid,script={name!r},args={args!r})))
 rc=p.wait();p.stdin.close()
assert rc==0,dict(script={name!r},returncode=rc,stderr=(r/({tag!r}+'.stderr.log')).read_text()[-1500:])
assert (r/{expected!r}).exists()
print(json.dumps(dict(script={name!r},state='completed')))
'''
 status('running_preparation',script=name,args=args);print(call(CLOUD,code,True,timeout=2400),flush=True)
def launch(phase):
 d=remote_json(CLOUD,C+'/'+phase+'-status.json',True)
 if d:
  if d['state']=='stopped_for_diagnosis':raise RuntimeError(d)
  if d['state']!='completed':
   assert json.loads(call(CLOUD,f"from pathlib import Path;import json;p=Path('/proc/{d['pid']}/cmdline');print(json.dumps(p.exists() and {C!r}.encode() in p.read_bytes()))",True)), 'Recorded controller absent; manual reconciliation required'
  status('existing_phase_preserved',phase=phase,controller=d);return
 print(call(CLOUD,f'''import subprocess,json
from pathlib import Path
r=Path({C!r});assert not (r/{phase!r}).exists()
with (r/({phase!r}+'-orchestrator.log')).open('x') as out:
 p=subprocess.Popen(['python3','-B',str(r/'run_phase.py'),{phase!r}],stdin=subprocess.DEVNULL,stdout=out,stderr=out,start_new_session=True,cwd=r)
print(json.dumps(dict(phase={phase!r},pid=p.pid)))
''',True),flush=True)
 time.sleep(3)
def local_script(name,*args):
 p=subprocess.run([sys.executable,'-B',str(H/name),*args],capture_output=True,text=True,timeout=300)
 print(p.stdout,flush=True);assert p.returncode==0,p.stderr[-2000:]
try:
 status('started',pid=__import__('os').getpid())
 wait_phase('repair')
 for phase in ['parent','sampling','repair']:
  run_script('replay_stops.py',[phase],phase+'/analysis/source-stop-replay-v2.json','post-repair-replay-'+phase)
 run_script('build_round2_requests.py',[],'execution-final.json','freeze-round2')
 if not remote_json(LAB,L+'/round2-generation.json'):
  local_script('publish_round2_inputs.py')
 while not remote_json(LAB,L+'/round2-generation-complete.json'):
  d=remote_json(LAB,L+'/generation-status.json')
  if d['state'] in ['stopped_api_failure','finished_without_next_batch','model_access_failed']:raise RuntimeError(d)
  status('waiting_round2_generation',api_status=d);time.sleep(55)
 if not exists(C+'/round2-generation-complete.json'):local_script('relay_generation.py','round2')
 launch('round2');wait_phase('round2')
 run_script('replay_stops.py',['round2'],'round2/analysis/source-stop-replay-v2.json','replay-round2')
 run_script('freeze_final_selection.py',[],'selection-final.json','freeze-final-selection')
 run_script('prepare_heldout.py',[],'heldout-eligibility.json','prepare-heldout')
 assert remote_json(CLOUD,C+'/heldout-eligibility.json',True)['state']=='passed'
 launch('heldout');wait_phase('heldout')
 run_script('replay_stops.py',['heldout'],'heldout/analysis/source-stop-replay-v2.json','replay-heldout')
 status('native_sequence_completed_awaiting_final_analysis_and_archive',next='Read all phase results, write report/accounting, seal evidence and relay archive to lab')
except BaseException as e:
 status('stopped_for_diagnosis',error=str(e),traceback=traceback.format_exc(),no_automatic_native_retry=True)
 raise
