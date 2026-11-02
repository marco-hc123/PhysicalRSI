"""Explicit receipt-aware recovery after the user-reported ECS arrears shutdown.

Use the framework's resume_evaluation port. Preserve the incomplete physical
attempt; only a fresh reset of that layout and unstarted cases are dispatched.
No candidate generation, manual policy edit or scoring change is permitted.
"""
from datetime import datetime, timezone
import fcntl
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import traceback
import types

O=Path('/mnt/data/physical-RSI/result/38_system2_gpt61sol_20261102')
REC=O/'recovery-01'
original=O/'procedure-sources/system2_sol_run.py'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(v,indent=2)+'\n');tmp.replace(p)
def stamp():return datetime.now(timezone.utc).isoformat()
assert not (O/'completion.json').exists()
assert not REC.exists(),'Reconcile this recovery before trying again'
assert not subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip()
old_pid=read(O/'launch.json')['pid']
cmdline=Path('/proc/'+str(old_pid)+'/cmdline')
assert not cmdline.exists() or str(original).encode() not in cmdline.read_bytes(),'Original controller still alive'
REC.mkdir()
lock=(O/'controller.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
protocol=read(O/'protocol.json')
for p,h in protocol['sources'].items():assert sha(p)==h,p
sys.argv=[str(original),str(O)]
namespace={'__file__':str(original),'__name__':'registered_system2_resume'}
source=original.read_text().split("lock=(O/'controller.lock').open('a')",1)[0]
exec(compile(source,str(original),'exec'),namespace)
task=namespace['task'];ns_read=namespace['read_json'];file_digest=namespace['file_digest']
from PhysicalRSI_baselines.robodojo import evidence
from PhysicalRSI_baselines.robodojo.workflow import Evaluation
from PhysicalRSI_core.self_harness.artifacts import verify_harness

def no_model_requests(*args,**kwargs):raise RuntimeError('Recovery forbids new model requests')
task.code_proposer.model.transport=no_model_requests
namespace['ROUND']=0
w=O/'workspace/rounds/round-000000'
for name in ['develop','propose','freeze','validation']:
    assert read(w/(name+'.json'))['state']=='completed',name
budget=read(O/'native-budget.json')
write(REC/'native-budget-before.json',budget)
write(REC/'phase-before.json',read(w/'evaluate_initial.json'))
completed=[b for b in budget['batches'] if b['state']=='completed']
interrupted=[b for b in budget['batches'] if b['state']=='started']
assert len(completed)==4 and len(interrupted)==1 and budget['completed']==4
for b in completed:
    leaf=Path(b['output']);v=read(leaf/'episodes/0.json')
    evidence.episode_receipt(leaf/'episodes/0.json',directory=leaf,task=v['task'],split=v['split'],
        layout_sha256=v['layout_sha256'],expert={'name':v['expert'],'revision':v['revision']},harness_sha256=v['harness_sha256'])
cases=read(w/'validation-cases.json')
pending=interrupted[0]
assert pending['harness_id']=='initial' and pending['index']==4
assert not (Path(pending['output'])/'episodes/0.json').exists(),'A possibly completed episode requires explicit reconciliation'
pending.update(state='interrupted_power_loss',interruption_recorded_utc=stamp(),
    reason='User confirmed ECS arrears shutdown; instance rebooted; partial native attempt retained without score',
    layout_sha256=cases[4]['layout_sha256'],score=None,success=None)
budget['maximum']=11
budget['recovery_amendment']=str(REC/'protocol.json')
plan=dict(utc=stamp(),authorization='User: continue experiment; arrears shutdown, account recharged',
    original_protocol_sha256=sha(O/'protocol.json'),original_driver_sha256=sha(original),
    recovery_source_sha256=sha(__file__),completed_receipts_reused=4,interrupted_physical_attempts=1,
    additional_complete_rollouts_planned=6,maximum_total_native_starts=11,planned_complete_native_episodes=10,
    model_requests_allowed=0,candidate_source_sha256=sha(w/'candidate/code/classify_objects.py'),
    recovery_interface='SelfHarness evaluator.resume_evaluation with durable per-batch receipt reconciliation',
    native_policy_source_changes=False,feedback_changes=False,scoring_changes=False,
    interrupted_attempt_counts_as='Infrastructure interruption, unknown score, not task inability')
write(REC/'protocol.json',plan);write(O/'native-budget.json',budget)

original_execute=task.execute_batch
def resumed_execute(self,harness,cases,cohort_root,output,*,expert=None):
    ledger=read(O/'native-budget.json')
    previous=next((b for b in ledger['batches'] if b['output']==str(output)),None)
    if previous and previous['state']=='completed':
        leaf=Path(previous['output']);v=read(leaf/'episodes/0.json')
        assert len(cases)==1 and cases[0]['layout_sha256']==v['layout_sha256']
        assert verify_harness(harness)==v['harness_sha256']
        return [evidence.episode_receipt(leaf/'episodes/0.json',directory=leaf,task=v['task'],split=v['split'],
            layout_sha256=v['layout_sha256'],expert={'name':v['expert'],'revision':v['revision']},harness_sha256=v['harness_sha256'])]
    if previous:
        assert previous['state']=='interrupted_power_loss'
        output=Path(output).with_name('recovery-01-'+Path(output).name)
        assert not output.exists()
    result=original_execute(harness,cases,cohort_root,output,expert=expert)
    if previous:
        ledger=read(O/'native-budget.json')
        ledger['batches'][-1]['recovery_of_batch_index']=previous['index']
        write(O/'native-budget.json',ledger)
    return result
task.execute_batch=types.MethodType(resumed_execute,task)

def resume_evaluation(self,candidate,comparison,cohort,output):
    return self.evaluate(candidate,comparison,cohort,output)
Evaluation.resume_evaluation=resume_evaluation
write(REC/'launch.json',dict(pid=__import__('os').getpid(),utc=stamp(),original_launch=read(O/'launch.json')))
namespace['status']('recovering_after_confirmed_power_loss',completed_receipts_reused=4,model_requests=0)
began=time.monotonic()
try:
    result=task.evolve()
    row=dict(index=0,finished_utc=stamp(),elapsed_s=time.monotonic()-began,result=result,task_status=task.status(),
             recovered_after_power_loss=True,recovery_protocol=str(REC/'protocol.json'))
    write(O/'round-00-result.json',row)
    write(O/'iteration-result.json',dict(utc=stamp(),logical_round_index=0,rounds=[row],
        recovery_elapsed_s=row['elapsed_s'],task_status=task.status(),native_budget=read(O/'native-budget.json'),
        qualification='One GPT model-swap pilot with explicit infrastructure recovery; interrupted attempt retained'))
    write(O/'completion.json',dict(complete=True,utc=stamp(),system2_rounds=1,new_proposals=1,
        native_budget=read(O/'native-budget.json'),recovered_after_power_loss=True))
    namespace['status']('complete',rounds_finished=1,recovered_after_power_loss=True)
except BaseException as error:
    write(O/'iteration-failed.json',dict(utc=stamp(),round_index=0,type=type(error).__name__,message=str(error),
        traceback=traceback.format_exc(),automatic_retry=False,recovery_protocol=str(REC/'protocol.json')))
    namespace['status']('recovery_failed',error_type=type(error).__name__,error=str(error))
    raise
