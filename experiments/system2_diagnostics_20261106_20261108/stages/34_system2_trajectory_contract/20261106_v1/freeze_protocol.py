"""Freeze the preselected execution comparison after stage33 completion."""
import datetime, hashlib, json, shutil
from pathlib import Path
L=Path('/mnt/data/joey_tr/physical-RSI/result/34_system2_trajectory_contract/20261106_v1')
P=Path('/mnt/data/joey_tr/physical-RSI/result/33_system2_capability_feedback/20261106_v1')
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert read(P/'EVIDENCE_INDEX.json')['state']=='sealed'
assert read(P/'FINAL_SUMMARY.json')['accounting']['new_native_cases']==30
assert read(L/'offline-contract/summary.json')['state']=='passed'
assert not (L/'protocol.json').exists()
design=read(L/'DESIGN.json');candidate=P/'candidates'/design['candidate']
inputs=L/'inputs';inputs.mkdir()
shutil.copy2(candidate/'candidate.py',inputs/'candidate.py')
shutil.copy2(candidate/'proposal.json',inputs/'proposal.json')
(inputs/'offline-contract').mkdir();shutil.copy2(L/'offline-contract/summary.json',inputs/'offline-contract/summary.json')
shutil.copy2(L/'DESIGN.json',inputs/'DESIGN.json')
protocol=dict(schema='physicalrsi.trajectory-contract-diagnostic/v1',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
 question='Does replacing dense waypoint execution with released bounded waypoint selection relieve budget blockage with exactly the same saved candidate?',
 selection=dict(candidate=design['candidate'],reason=design['selection_reason'],design_preparation_utc=design['utc'],source_sha256=sha(inputs/'candidate.py'),proposal_sha256=sha(inputs/'proposal.json')),
 previous_stage_index_sha256=sha(P/'EVIDENCE_INDEX.json'),previous_stage_summary_sha256=sha(P/'FINAL_SUMMARY.json'),
 conditions=['dense','released_waypoint_thinning'],planned_native_cases=10,layouts=[0,1,2,3,4],unique_layouts=5,
 layout_role='Previously exposed development/diagnostic layouts; no independent generalization',
 treatment=dict(selector='Exact released thin_native_path function',max_joint_step_rad=.12,chord_tolerance_rad=.01,
  original_native_samples_only=True,endpoints_preserved=True,invalid_selection='Reject and record; no silent dense fallback',
  unchanged_primitive_guard_rad=.25),
 unchanged=design['unchanged'],new_api_calls=0,new_api_budget_usd=0,new_training_steps=0,
 new_native_control=True,historical_cases_recounted=0,automatic_policy_promotion=False,
 primary_metrics=['native_score_100','native_success','active_execution_budget_cancellation','completed_approach_count','stop_reason'],
 secondary_metrics=['dense_and_selected_planned_waypoints','completed_primitive_steps','final_observed_joint_tracking_error','full_cohort_wall_seconds'],
 limitations=design['limits']+['Thinning changes execution timing and interpolation; fixed endpoints do not imply identical continuous motion.',
  'Projected planner rejection does not distinguish IK from collision failure.',
  'Static geometry is not full collision certification; preserve original robot/table scope and observed-state guards.',
  'Primitive completed-step totals omit partial cancelled calls; all1100native actions can include post-return holds.',
  'One preselected candidate, fixed condition order and five reused layouts limit statistical and timing attribution.'],
 code_files={str(p.relative_to(L)):sha(p) for p in sorted((L/'code').glob('*.py'))},
 reference_manifest_sha256=sha(L/'reference-manifest.json'),offline_contract_sha256=sha(L/'offline-contract/summary.json'))
(L/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');shutil.copy2(L/'protocol.json',inputs/'protocol.json')
files=[]
for folder in ['inputs','code']:
 for p in sorted((L/folder).rglob('*')):
  if p.is_file() and '__pycache__' not in p.parts:files.append(dict(path=str(p.relative_to(L)),bytes=p.stat().st_size,sha256=sha(p)))
(L/'input-manifest.json').write_text(json.dumps(dict(files=files),indent=2)+'\n')
print(json.dumps(dict(state='protocol_frozen',files=len(files),planned_native_cases=10,new_api_calls=0)))
