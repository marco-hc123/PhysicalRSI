"""Finish the complete pilot before freezing and running the prespecified target control."""
import datetime,json,time,traceback,os
from remote_ops import H,C,CLOUD,PYTHON,call
P=H/'sampling-followup-status.json'
def status(state,**extra):
 d=dict(state=state,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),pid=os.getpid(),**extra);P.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d),flush=True)
try:
 while True:
  d=json.loads(call(CLOUD,f"from pathlib import Path;p=Path({C!r})/'sampling-status.json';print(p.read_text())",True))
  if d['state']=='completed':break
  assert d['state']!='stopped_for_diagnosis',d
  status('waiting_for_complete_pilot',controller=d);time.sleep(55)
 status('validating_control_eligibility')
 code=f'''import datetime,hashlib,json,subprocess
from pathlib import Path
r=Path({C!r});read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for phase in ['parent','sampling']:assert read(r/phase/'analysis/independent-validation.json')['state']=='passed'
m=read(r/'sampling/analysis/matrix-analysis.json');assert m['complete'] and m['qualified_cases']==25
sample=[x for x in m['actors'] if x['condition']=='sample_01'];assert len(sample)==5
for a in sample:
 assert a['mapping_qualified'] and a['return_record_exists'] and a['rpc_calls']<100
 calls=read(r/'sampling'/a['process_record'])['calls']
 assert calls[-1]['response']['value']['primitive_error']=='no_collision_free_path'
 grips=[x['request']['kwargs']['command'] for x in calls if x['request']['method']=='gripper']
 assert grips==[1,0],grips
assert all(x['normalized_score']==0 and not x['success'] for x in m['episodes'] if x['condition']=='sample_01')
control=read(r/'manual-target-control/control-equivalence-replay.json');assert control['state']=='passed' and len(control['cases'])==5
for script,args,output in [('select_development.py',['sampling'],'sampling-selection.json'),('replay_stops.py',['sampling'],'sampling/analysis/source-stop-replay-v2.json')]:
 if not (r/output).exists():
  p=subprocess.run([{PYTHON!r},'-B',str(r/script)]+args,capture_output=True,text=True,cwd=r);assert p.returncode==0,p.stderr[-2000:]
  (r/('pilot-final-'+script+'.stdout.log')).write_text(p.stdout)
assert not (r/'repair').exists() and not (r/'repair-plan.json').exists()
plan=read(r/'manual-target-control/repair-plan-draft.json');design=read(r/'manual-target-control/design-draft.json')
design.update(state='frozen_before_native_execution',frozen_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),evidence=[dict(path=str(p.relative_to(r)),sha256=sha(p)) for p in [r/'sampling/analysis/matrix-analysis.json',r/'sampling/analysis/independent-validation.json',r/'sampling/analysis/source-stop-replay-v2.json',r/'target-audits/first2/audit.json',r/'manual-target-control/control-equivalence-replay.json']],reason='Five sample_01 runs stop at commanded-closed transport no-path with no release; sample_02 independently exhibits frequent near-basket no-path. Select the earliest repeatedly observed generated-candidate transport bottleneck. A spacing-only intervention would not test a zero-execution rejected target.',protocol_clarification='Stage2 uses one manual destinationXY control within one otherwise-fixed candidate source; execution API/runtime is not changed. Generated source/memory remain immutable in the original sampling pool. Manual results cannot be counted as System2-generated improvement.',heldout_manual_reference_rule='If target_offset strictly improves full-success count then mean native score over target_control, include one separately labeled manual reference within maximum20heldoutcases. No test-set selection.')
(r/'manual-target-control/design-final.json').write_text(json.dumps(design,indent=2)+'\\n')
(r/'repair-plan.json').write_text(json.dumps(plan,indent=2)+'\\n')
with (r/'repair-orchestrator.log').open('x') as out:
 p=subprocess.Popen(['python3','-B',str(r/'run_phase.py'),'repair'],stdin=subprocess.DEVNULL,stdout=out,stderr=out,start_new_session=True,cwd=r)
print(json.dumps(dict(state='repair_launched',pid=p.pid,control_cases=5,treatment_cases=5,scope='One categorical targetXY rule, all other execution conditions fixed')))
'''
 result=json.loads(call(CLOUD,code,True,timeout=180));status('repair_launched',remote=result)
except BaseException as e:
 status('stopped_for_diagnosis',error=str(e),traceback=traceback.format_exc());raise
