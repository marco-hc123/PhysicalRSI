"""Register bounded fifth-step native iteration before any experiment or API call."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import sys

R = Path('/mnt/data/physical-RSI')
O = Path(sys.argv[1]).resolve()
P = R/'result/25_system2_integration_20261030T050100Z'
F = R/'result/23_protocol_freeze_20261029T132917Z'
assert O.parent == R/'result' and not O.exists()
O.mkdir()

def read(p):
    return json.loads(Path(p).read_text())

def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()

def write(p, value):
    p.write_text(json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2)+'\n')

utc = datetime.now(timezone.utc).isoformat()
assert read(P/'step4-completion.json')['complete'] is True
freeze = read(F/'source-freeze.json')
for row in freeze['deployment_files']:
    assert sha(row['path']) == row['sha256'], row['path']
for name, expected in freeze['recorded_protocol_and_framework_hashes'].items():
    assert sha(name) == expected, name
sources = O/'procedure-sources'
sources.mkdir()
for name in ['step5_register.py', 'step5_feedback.py', 'step5_run.py']:
    (sources/name).write_bytes((R/'result'/name).read_bytes())

cfg = read(P/'attempt-05-planning-contract/runtime.json')
cfg['policy_spec']['configuration']['output'] = str(O/'primitive-services')
cfg['skill_api']['scope'] = ('Study-specific bounded System2 iteration using step4-qualified calibrated RGB/CuRobo primitives; '
    'not stock paper performance or a full dynamic-object collision model')
write(O/'runtime.json', cfg)
workflow = read(P/'attempt-05-planning-contract/workflow-configuration.json')
workflow.update(development_episodes=5, validation_episodes=5)
write(O/'workflow-configuration.json', workflow)

# Exclusion uses metadata and copies of already observed layouts, never future
# final-test geometry. These bytes are not supplied to the trusted sampler/model.
splits = read(F/'data-splits.json')
excluded = set()
def collect(value):
    if isinstance(value, dict):
        for key, val in value.items():
            if key in {'layout_sha256', 'content_sha256'} and isinstance(val, str) and len(val)==64:
                excluded.add(val)
            else:
                collect(val)
    elif isinstance(value, list):
        for val in value:
            collect(val)
collect(splits)
metadata = {}
for path in sorted(P.rglob('*cases.json')):
    collect(read(path))
    metadata[str(path)] = sha(path)
for path in sorted(P.glob('**/initialization-layouts/manifest.json')):
    collect(read(path))
    metadata[str(path)] = sha(path)
# Reference task assets were materialized by step3. Hash only copies retained in
# that completed experiment, rather than opening the benchmark asset directory.
v3 = R/'result/24_steps23_20261030T013742Z_v3'
for path in sorted((v3/'task-assets').rglob('*.json')):
    data = read(path)
    collect(data)
    metadata[str(path)] = sha(path)
write(O/'historical-exclusions.json', dict(hashes=sorted(excluded), metadata_sources=metadata,
    source_splits=str(F/'data-splits.json'), source_splits_sha256=sha(F/'data-splits.json'),
    purpose='Reject any observed content hash; no layout geometry supplied to proposal or sampler'))

registration = dict(schema='physicalrsi.system2-bounded-iteration/v1', registered_utc=utc,
    step=5, prior_protocol=str(F/'protocol.json'), prior_protocol_sha256=sha(F/'protocol.json'),
    step4_completion=str(P/'step4-completion.json'), step4_completion_sha256=sha(P/'step4-completion.json'),
    scope='Selected-task core reproduction; development/proposal costs separate from System1 online comparison',
    task='classify_objects', scheme='hybrid', maximum_rounds=2, maximum_candidates_per_round=1,
    development_layouts_per_round=5, validation_layouts_per_round=5, maximum_native_evaluations=50,
    expected_native_evaluations='40 if initial VLA retained; 45 if first candidate survives and incumbent code assessed in round2',
    initial_parent='Official workflow initial pi05 seed; no integration candidate relabelled as initial parent',
    minimum_vla_score=.6, minimum_gain=0, maximum_regression=0, tie_tolerance=1e-10,
    rollout_batch_size=1, num_envs=1, simulator_seed=0, control_dt=.04, physics_dt=.004,
    collect_interval=10, step_limit=1100, proposal_http_attempts_maximum=2, automatic_http_retries=0,
    amendments_before_dispatch=[
        'Reuse immutable step4 F3 qualified runtime; retain explicit no-path contract repair and native deployment adapters.',
        'Model receives all native development metric fields, with each verbose artifact inventory replaced by its complete-row digest and count. Full inventories remain verified and retained. This representation is fixed for both rounds, not a Token-saving ablation.',
        'Reject layout hashes across historical/reference/development/prior validation cohorts; no silent resampling on collision.',
        'Use the stock workflow proposer/selector/lineage: second round inherits only selected parent. A rejected candidate is retained as evidence, not silently adopted or fed back as successful repair.'
    ],
    model_profile=dict(model='qwen3.7-plus', temperature=0, enable_thinking=True,
        response_format={'type':'json_object'}, automatic_retries=0, timeout_s=600,
        output_limit_override=False, maximum_prompt_characters=100000),
    sources={str(path):sha(path) for path in sources.glob('*.py')},
    reused_runtime=str(P/'attempt-05-planning-contract/runtime.json'),
    configuration_sha256=sha(O/'runtime.json'), workflow_configuration_sha256=sha(O/'workflow-configuration.json'),
    historical_exclusions_sha256=sha(O/'historical-exclusions.json'),
    stop_conditions=['Two committed rounds or native evaluation cap',
        'Any ambiguous interrupted native/model operation, admission error, malformed model response or contract failure blocks automatic retry; preserve all evidence and diagnose'],
    qualifications=['No improvement assumed; parent retention is a valid scientific result.',
        'Fresh validation informs selection, not the model proposal. Final step7 test remains ungenerated.',
        'Selected task and study-specific budgets, not full RoboDojo leaderboard or authors historical exact performance.',
        'No changes to original source, weights, reward, model/proxy/permission settings; no local raw backup'],
    raw_retention='cloud_only')
write(O/'protocol.json', registration)
write(O/'controller-status.json', dict(utc=utc, stage='registered_not_started', complete=False, directory=str(O)))
write(R/'result/CURRENT_STEP5.json', dict(utc=utc,stage='registered_not_started',directory=str(O),complete=False,pid=None))
plan = read(R/'result/CURRENT_REPRODUCTION_PLAN.json')
plan.update(updated_utc=utc,current_authorized_step=5,active_authorized_step=5,current_step=5,
    next_step=6,active_directory=str(O),active_protocol=str(O/'protocol.json'),
    active_controller_pid=None,current_controller_running=False,active_tmux_session=None,
    later_steps_started=False,next_action='Run offline preflight then two bounded formal System2 rounds')
plan['authorized_steps']=sorted(set(plan.get('authorized_steps',[])+[5]))
plan['steps'][4]['state']='registered; offline preflight required before native iteration'
write(R/'result/CURRENT_REPRODUCTION_PLAN.json', plan)
print(json.dumps(dict(registered=True,directory=str(O),historical_hashes=len(excluded),native_evaluation_cap=50)))
