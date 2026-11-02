"""Register the remaining paired validation without replaying development/HTTP."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,os,sys,subprocess
R=Path('/mnt/data/physical-RSI');P=R/'result/29_system2_api_20261030T101800Z';O=Path(sys.argv[1]).resolve()
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):Path(p).write_text(json.dumps(v,sort_keys=True,ensure_ascii=False,indent=2)+'\n')
assert os.geteuid()==0 and O.parent==R/'result' and not O.exists()
assert not Path('/proc/105668').exists() and not Path('/proc/105796').exists()
assert not Path('/proc/138921').exists() and not Path('/proc/138929').exists()
assert not subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True,timeout=15).strip()
old=read(P/'protocol.json')
for f,h in old['sources'].items():assert sha(f)==h
freeze=read(R/'result/23_protocol_freeze_20261029T132917Z/source-freeze.json')
for row in freeze['deployment_files']:assert sha(row['path'])==row['sha256']
for f,h in freeze['recorded_protocol_and_framework_hashes'].items():assert sha(f)==h
assert read(P/'native-budget.json')['requested']==read(P/'native-budget.json')['completed']==20
failure=read(P/'iteration-failed.json');assert failure['round_index']==1 and failure['message']=='CPU scene contract gate rejected candidate: named'
parent=P/'workspace/rounds/round-000000/commit.json';selected=read(parent)
assert selected['decision']['decision']=='retain_parent'
O.mkdir();S=O/'procedure-sources';S.mkdir()
names=['step5_final_register.py','step5_final_run.py','step5_scene_api_v4.py','step5_feedback.py','step5_final_audit.py','step5_final_finish.py','step5_observe.py']
for n in names:(S/n).write_bytes((R/'result'/n).read_bytes())
cfg=read(P/'runtime.json');cfg['policy_spec']['configuration']['output']=str(O/'primitive-services');write(O/'runtime.json',cfg)
write(O/'workflow-configuration.json',read(P/'workflow-configuration.json'))
w=P/'workspace/rounds/round-000001'
reuse_files=[P/'runtime.json',P/'protocol.json',P/'native-budget.json',P/'iteration-failed.json',parent,w/'parent.json',w/'development-cases.json',w/'development-results.json']
model_files=[P/n for n in ['proposal-api/call-0001/request.json','proposal-api/call-0001/response.json','proposal-api/call-0001/completed.json','workspace/rounds/round-000001/proposals/classify_objects/request.json','workspace/rounds/round-000001/proposals/classify_objects/response.json']]
excluded=read(P/'observed-layout-hashes.json')
write(O/'historical-exclusions.json',dict(hashes=excluded,source=str(P/'observed-layout-hashes.json'),source_sha256=sha(P/'observed-layout-hashes.json')))
protocol=dict(old)
protocol.update(schema='physicalrsi.system2-final-validation-continuation/v1',registered_utc=datetime.now(timezone.utc).isoformat(),
 maximum_rounds=1,logical_round_index=1,previous_complete_round=str(P/'round-00-result.json'),registered_zero_dispatch_attempt=str(R/'result/30_system2_final_validation_20261030T120500Z'),
 maximum_native_evaluations=10,expected_native_evaluations='Only the remaining second-round 5 parent + 5 candidate validation episodes',proposal_http_attempts_maximum=0,
 selected_parent_commit=str(parent),selected_parent_commit_sha256=sha(parent),selected_parent_freeze_sha256=selected['freeze_sha256'],
 reuse_development=dict(directory=str(P),round_index=1,episodes=10,new_native_episodes=0,files={str(f):sha(f) for f in reuse_files}),
 completed_proposal=dict(directory=str(P),round_index=1,new_http_attempts=0,files={str(f):sha(f) for f in model_files}),
 sources={str(f):sha(f) for f in S.glob('*.py')},configuration_sha256=sha(O/'runtime.json'),workflow_configuration_sha256=sha(O/'workflow-configuration.json'),historical_exclusions_sha256=sha(O/'historical-exclusions.json'),
 prior_attempt=str(R/'result/26_system2_iterations_20261030T074100Z'),
 amendments_before_dispatch=[
 'Static CPU fixtures inspect a bounded valid RPC prefix; exhausting the static fixture is inconclusive for policy completion. Also verify completed no-path rejection handling. No synthetic motion/reward success is invented.',
 'Native isolation max_calls remains 100, physics/control/reward/checkpoints/model output unchanged. Native evaluation alone determines physical outcome.',
 'Explicit new policy bootstrap preserving selected skill/memory/control/weights; rebind only assets/prompts/dependencies to the current execution closure, with external bridge to the first committed round. This is a registered policy-boundary continuation, not an unchanged-policy hash chain.',
 'Reuse ten completed second-round development episodes and exact completed Qwen source/memory/response. No new HTTP, no native development replay.',
 'Only five new paired validation layouts, generated after comparison freeze and excluding all prior layouts; official selector/commit used without changing scores.'
 ])
write(O/'protocol.json',protocol)
write(O/'policy-bridge-registration.json',dict(previous_commit=str(parent),previous_revision=selected['revision'],harness_freeze_sha256=selected['freeze_sha256'],native_call_budget_unchanged=100,requires_new_bootstrap_policy=True,only_rebound_components=['assets','prompts','dependencies'],no_source_or_memory_rewrite=True,new_http_attempts=0))
write(O/'controller-status.json',dict(stage='registered_final_validation',pid=None,complete=False,utc=protocol['registered_utc']))
write(O/'audit-registration.json',dict(audit_sha256=sha(S/'step5_final_audit.py'),finisher_sha256=sha(S/'step5_final_finish.py')))
plan=read(R/'result/CURRENT_REPRODUCTION_PLAN.json');plan.update(updated_utc=protocol['registered_utc'],active_directory=str(O),active_attempt_directory=str(O),active_protocol=str(O/'protocol.json'),active_controller_pid=None,current_controller_running=False,active_tmux_session=None,next_step=5,step5_complete=False,next_action='Complete final second-round paired validation and combined two-round audit; preserve original native call limit')
plan['steps'][4]['state']='first round complete; second-round development/proposal complete; final paired validation pending with explicit inspection-policy bridge'
write(R/'result/CURRENT_REPRODUCTION_PLAN.json',plan);write(R/'result/CURRENT_STEP5.json',dict(directory=str(O),stage='registered_final_validation',pid=None,complete=False,utc=protocol['registered_utc']))
print(json.dumps(dict(registered=True,directory=str(O),new_native_cap=10,new_http_attempts=0)))
