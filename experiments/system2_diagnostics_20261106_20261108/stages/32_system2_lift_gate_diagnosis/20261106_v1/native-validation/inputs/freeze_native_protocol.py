"""Freeze the adaptive native experiment on the lab server before execution."""
import datetime
import hashlib
import json
from pathlib import Path
R=Path('/mnt/data/joey_tr/physical-RSI/result/32_system2_lift_gate_diagnosis/20261106_v1')
S=Path('/mnt/data/joey_tr/physical-RSI/result/31_system2_rgb_validation/20261105_v1')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
summary=json.loads((R/'summary.json').read_text())
assert not summary['z_only_branch_changes']
assert summary['totals']['bypass_lift_guard']['next_call_requests']==5
old=json.loads((S/'native-campaign/campaign.json').read_text())
conditions=[dict(name=n,candidate_sha256=sha(R/'candidates'/n/'candidate.py')) for n in ['original','bypass_lift_guard']]
protocol=dict(schema='physicalrsi.lift-gate-native-ablation/v1',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    title='Lift verification guard enabled versus diagnostic bypass',
    question='Does the post-lift guard prevent later actions, and does bypassing it improve native outcome or only continue a failed grasp?',
    protocol_type='Exploratory adaptive mechanism experiment, frozen before new native execution',
    adaptation=dict(prior_plan='Original versus remove_z_only',reason='Exact CPU replay showed zero branch changes across all five saved observations.',
        decision='Do not spend a native matrix on Z-only removal. Compare original against one-line bypass of the whole return guard.',
        evidence_sha256=sha(R/'summary.json'),offline_replays=25,existing_native_cases_reused=5),
    conditions=conditions,execution_order=['original','bypass_lift_guard'],cases_per_condition=5,planned_native_cases=10,
    task='classify_objects',robot='ARX X5',native_step_limit=1100,
    runtime_sha256=old['runtime_sha256'],layout_sha256=[x['layout_sha256'] for x in old['cases']],
    fixed=['All code except one post-lift conditional','Same five historical layouts','Original scoring and step budget',
           'Perception, primitives, planning configuration and runtime','Simulator seed from frozen runtime'],
    metrics=['Valid native receipts and full success','Score on 0-100 scale','First post-lift basket approach requested/completed',
             'Planner rejection and step-limit termination','Primitive action steps','Three-camera video evidence','Full cohort wall time'],
    physical_evidence='Use original scoring and videos. Physical lift/grasp remains unknown where video does not establish it; no hidden GT is fed to actor.',
    limitations=['Manual diagnostic bypass is not an autonomous System 2 improvement or reliable grasp verifier.',
                 'Historical layouts already exposed; no generalization claim.',
                 'Same-layout pairing does not ensure identical rendered pixels or stochastic execution.',
                 'No new policy selection; pi05 stays retained.','Whole guard intervention does not isolate Z alone.'],
    paid_api_calls_planned=0,lab_gpu_used=False,transport='Lab to cloud through local SSH relay; results returned to project-only lab path.',
    archive_destination=str(R/'native-validation'),stop_policy='Stop and preserve any deployment failure before retry; task failures remain valid outcomes.')
p=R/'protocol/native-protocol.json';p.parent.mkdir(exist_ok=True);assert not p.exists();p.write_text(json.dumps(protocol,ensure_ascii=False,indent=2)+'\n')
status=json.loads((R/'status.json').read_text());status.update(stage='native_protocol_frozen',pending=['transfer_to_execution_host','10_native_cases','analysis_and_lab_archive'],
    native_protocol_sha256=sha(p),active_pid=None,cloud_result_root='/mnt/data/physical-RSI/result/32_lift_gate_validation_20261106')
(R/'status.json').write_text(json.dumps(status,indent=2)+'\n')
print(json.dumps({'state':'frozen','native_cases':10,'protocol_sha256':sha(p),'no_z_only_native_matrix':True}))
