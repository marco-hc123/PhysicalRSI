"""Register continuation with explicit scene API and verified prior development."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import sys

R = Path('/mnt/data/physical-RSI')
PRIOR = R/'result/26_system2_iterations_20261030T074100Z'
O = Path(sys.argv[1]).resolve()


def read(p):
    return json.loads(Path(p).read_text())


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def write(p, value):
    Path(p).write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)+'\n')


assert os.geteuid() == 0 and O.parent == R/'result' and not O.exists()
assert not Path('/proc/104166').exists(), 'Previous controller still exists'
freeze = read(R/'result/23_protocol_freeze_20261029T132917Z/source-freeze.json')
for row in freeze['deployment_files']:
    assert sha(row['path']) == row['sha256'], row['path']
for p, h in freeze['recorded_protocol_and_framework_hashes'].items():
    assert sha(p) == h, p
O.mkdir()
sources = O/'procedure-sources'
sources.mkdir()
names = ['step5_api_register.py', 'step5_api_run.py', 'step5_scene_api_v3.py',
         'step5_feedback.py', 'step5_api_audit.py', 'step5_api_finish.py', 'step5_observe.py']
for name in names:
    (sources/name).write_bytes((R/'result'/name).read_bytes())
sys.path[:0] = [str(sources), str(R/'result/25_system2_integration_20261030T050100Z/integration-sources/framework-validation-v3')]
from step5_scene_api_v3 import clarified_api
cfg = read(PRIOR/'runtime.json')
cfg['policy_spec']['configuration']['output'] = str(O/'primitive-services')
cfg['skill_api'] = clarified_api(cfg['skill_api'])
cfg['skill_api']['methods']['scene'] = (
    'robot.scene() -> {objects: {"<category>_<positive_instance_index>": '
    '{pose:[x,y,z,w,x,y,z],dims:[x,y,z]}}, observation}; keys are strings. '
    'Examples: basket_1, watch_2, toy_car_1. Split at the last underscore; '
    'category is a string, only the final instance suffix is an integer. '
    'RGB estimates, world-frame metres; no hidden layouts or success signal.')
write(O/'runtime.json', cfg)
write(O/'workflow-configuration.json', read(PRIOR/'workflow-configuration.json'))
old_w = PRIOR/'workspace/rounds/round-000000'
paths = [PRIOR/'runtime.json', PRIOR/'protocol.json', PRIOR/'step5-stopped-results.json',
         PRIOR/'interruption-audit/verification.json', old_w/'parent.json',
         old_w/'development-cases.json', old_w/'development-results.json']
reuse = dict(directory=str(PRIOR), episodes=10, layouts=5,
    files={str(p):sha(p) for p in paths},
    reason='Completed paired VLA development remains applicable: only API documentation and primitive output directory change; native sources/configuration/weights unchanged',
    receipt_identity='Original native harness identities retained; evidence paths ported without changing bytes',
    new_native_episodes=0)
excluded = sorted(set(read(PRIOR/'observed-layout-hashes.json')))
write(O/'historical-exclusions.json', dict(hashes=excluded, source=str(PRIOR/'observed-layout-hashes.json'),
    source_sha256=sha(PRIOR/'observed-layout-hashes.json'), reused_development_layouts=[c['layout_sha256'] for c in read(old_w/'development-cases.json')]))
protocol = read(PRIOR/'protocol.json')
utc = datetime.now(timezone.utc).isoformat()
protocol.update(schema='physicalrsi.system2-interface-continuation/v2', registered_utc=utc,
    completed_proposal=dict(directory=str(R/'result/28_system2_interface_20261030T102000Z'), files={str(p):sha(p) for p in [R/'result/28_system2_interface_20261030T102000Z'/name for name in ['proposal-api/call-0001/request.json','proposal-api/call-0001/response.json','proposal-api/call-0001/completed.json','workspace/rounds/round-000000/proposals/classify_objects/request.json','workspace/rounds/round-000000/proposals/classify_objects/response.json']]}),
    maximum_native_evaluations=35, expected_native_evaluations='30 new evaluations, or 35 if selected code needs round2 development; 10 prior VLA development evaluations reused',
    reuse_development=reuse, prior_attempt=str(PRIOR), prior_attempt_protocol_sha256=sha(PRIOR/'protocol.json'),
    sources={str(p):sha(p) for p in sources.glob('*.py')},
    configuration_sha256=sha(O/'runtime.json'), workflow_configuration_sha256=sha(O/'workflow-configuration.json'),
    historical_exclusions_sha256=sha(O/'historical-exclusions.json'),
    amendments_before_dispatch=[
        'Align CPU quaternion tolerance with the unchanged native primitive squared-norm tolerance 1e-4; reuse the completed actual model response without source/memory rewriting or new first-round HTTP.',
        'Explicit public scene-object string key format with examples and last-underscore parsing; task, rewards, controls and checkpoints unchanged.',
        'CPU synthetic scene/RPC contract gate after actual model generation, before native evaluation; no generated source rewriting, no automatic regeneration.',
        'Reuse verified first-round five-layout/two-VLA development evidence, retaining original native identities; do not replay those completed evaluations.',
        'New paired validation cohort generated only after new candidate comparison freeze, excluding every previously observed layout.',
        'Second round uses fresh development and validation; incumbent selection, lineage and source/memory inheritance use official workflow.',
        'Keep actual failed prior proposal and incurred costs separate and in cumulative totals. No change to model/thinking/permission/proxy configuration.'
    ])
write(O/'protocol.json', protocol)
write(O/'controller-status.json', dict(utc=utc,stage='registered_interface_continuation',pid=None,complete=False))
write(O/'audit-registration.json', dict(audit_sha256=sha(sources/'step5_api_audit.py'),
    finisher_sha256=sha(sources/'step5_api_finish.py'), no_model_or_native_dispatch=True))
write(R/'result/CURRENT_STEP5.json', dict(utc=utc,stage='registered_interface_continuation',directory=str(O),pid=None,complete=False))
plan = read(R/'result/CURRENT_REPRODUCTION_PLAN.json')
plan.pop('latest_scene_contract_repair', None)
plan['formal_candidate_policy'] = dict(
    task='classify_objects',candidate_source='Actual model output without source rewriting',
    interface='Explicit scene-name API and bounded CPU contract checks',
    inputs='Development evidence and public API only',
    evaluation='Fresh paired native validation, official selection and lineage',
    accounting='All proposal, failed attempt, development and evaluation costs retained')
plan.update(updated_utc=utc,active_directory=str(O),active_attempt_directory=str(O),
    active_protocol=str(O/'protocol.json'),active_controller_pid=None,current_controller_running=False,
    active_tmux_session=None,next_step=5,step5_complete=False,
    next_action='Complete model-generated candidate validation and two bounded System2 rounds with explicit scene API',
    qualification='Interface clarified; completed development evidence reused after verification; native candidate validation and two-round selection remain to finish')
plan['step5_progress'] = dict(stage='registered_interface_continuation',reused_development_episodes=10,
    new_native_completed=0,committed_rounds=0,prior_attempt=str(PRIOR),raw_retention='cloud_only')
plan['steps'][4]['state'] = 'continuing with explicit scene API; first-round development evidence reused'
write(R/'result/CURRENT_REPRODUCTION_PLAN.json', plan)
print(json.dumps(dict(registered=True,directory=str(O),reused_development=10,new_native_cap=35)))
