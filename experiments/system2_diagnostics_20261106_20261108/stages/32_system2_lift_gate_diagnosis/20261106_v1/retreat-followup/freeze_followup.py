"""Freeze native retreat comparison only after successful actual-state solver probes."""
import ast,datetime,difflib,hashlib,json,shutil
from pathlib import Path
L=Path('/mnt/data/joey_tr/physical-RSI/result/32_system2_lift_gate_diagnosis/20261106_v1')
O=L/'retreat-followup'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
assert read(L/'planning-return/status.json')['state']=='completed'
s=read(L/'planning-return/summary.json')
assert s['solver_calls']==18
assert all(g['returned_trajectory']==3 for g in s['groups'] if g['goal_variant']=='previous_clearance')
assert all(g['returned_trajectory']==0 for g in s['groups'] if g['goal_variant']=='original_retreat')
O.mkdir(exist_ok=True)
assert not (O/'protocol/native-protocol.json').exists()
base=L/'candidates/bypass_lift_guard/candidate.py';code=base.read_text()
old='            move(arm, bx, by, 1.07)';new='            move(arm, x, y, clearance_z)'
assert code.count(old)==1
candidate=code.replace(old,new);ast.parse(candidate)
conditions=[]
for name,source in [('bypass_lift_guard',code),('return_to_clearance',candidate)]:
    p=O/'candidates'/name/'candidate.py';p.parent.mkdir(parents=True);p.write_text(source)
    conditions.append(dict(name=name,candidate_sha256=sha(p)))
(O/'candidates/return_to_clearance/change.diff').write_text(''.join(difflib.unified_diff(code.splitlines(True),candidate.splitlines(True),fromfile='bypass_lift_guard.py',tofile='return_to_clearance.py')))
prior=read(L/'protocol/native-protocol.json');inputs=O/'inputs';inputs.mkdir()
for sub in ['planning-return','planning-recovery']:
    for name in ['protocol.json','summary.json','runtime.json','status.json']:
        p=inputs/sub/name;p.parent.mkdir(exist_ok=True);shutil.copy2(L/sub/name,p)
protocol=dict(schema='physicalrsi.retreat-native-ablation/v1',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    question='Does retreating to the previously achieved clearance position remove the post-release planner stop, and does this change score or reveal another stop?',
    conditions=conditions,execution_order=[x['name'] for x in conditions],cases_per_condition=5,planned_native_cases=10,
    task='classify_objects',robot='ARX X5',native_step_limit=1100,runtime_sha256=prior['runtime_sha256'],layout_sha256=prior['layout_sha256'],
    primary_variable='Single post-release retreat destination: basket XY/Z1.07 versus previous object XY/clearance_z. Quaternion and arm unchanged.',
    fixed=['All other candidate code including diagnostic lift guard bypass','Same frozen runtime, planner, perception, geometry, layout identities, task scoring and 1100-step budget'],
    justification=dict(actual_prior_native_cases=10,failed_retreat_layouts=[1,3,4],transport_failure_control_layouts=[0,2],offline_return_probes=18,offline_height_probes=45,return_probe_summary_sha256=sha(L/'planning-return/summary.json')),
    metrics=['Strict native outcome and 0-100 score','Retreat request completion','Next scene or second object attempt','New planner rejection or step limit','Raw three-camera videos','Full cohort wall time'],
    limitations=['Manual diagnostic intervention; both conditions bypass unsupported grasp guard. No autonomous System2 success or valid grasp-verifier claim.','All layouts previously exposed; no independent generalization.','Fresh repeated control reduces chronology mismatch but does not guarantee identical observations.','Planning acceptance is not physical task success.','No new selector; pi05 retained.'],
    api_calls=0,archive_destination=str(O/'native-validation'))
p=O/'protocol/native-protocol.json';p.parent.mkdir();p.write_text(json.dumps(protocol,ensure_ascii=False,indent=2)+'\n')
(O/'status.json').write_text(json.dumps(dict(state='protocol_frozen',native_protocol_sha256=sha(p),planned_native_cases=10,api_calls=0),indent=2)+'\n')
print(json.dumps(dict(state='frozen',protocol_sha256=sha(p),conditions=conditions)))
