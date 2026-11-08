"""Freeze two explicit runtime variants after the previous matrix is archived."""
import copy, datetime, json, shutil, sys
from pathlib import Path
R = Path('/mnt/data/physical-RSI')
O = R / 'result/35_trajectory_contract_20261106'
P = R / 'result/34_capability_feedback_20261106'
I = R / 'result/25_system2_integration_20261030T050100Z/integration-sources'
sys.path[:0] = [str(I), str(I / 'framework-validation-v3')]
from PhysicalRSI_core.infra.storage import atomic_json, file_digest, read_json
from PhysicalRSI_core.self_harness.artifacts import verify_harness
from PhysicalRSI_baselines.robodojo.native_runtime import NativeRuntime
from PhysicalRSI_baselines.robodojo.evidence import verify_case
from PhysicalRSI_baselines.robodojo.workflow import manifest

assert read_json(P / 'migration/LAB_ARCHIVE_VERIFIED.json')['state'] == 'verified'
assert read_json(P / 'analysis/independent-validation.json')['state'] == 'passed'
assert read_json(O / 'inputs/offline-contract/summary.json')['state'] == 'passed'
protocol = read_json(O / 'inputs/protocol.json')
prior = read_json(P / 'native-campaign/campaign.json')
parent = next(e for e in prior['entries'] if e['name'] == 'capability_feedback_2')
assert verify_harness(parent['harness']) == parent['harness_sha256']
base = read_json(prior['runtime'])
assert file_digest(Path(prior['runtime'])) == prior['runtime_sha256']
assert prior['runtime_sha256'] == '264b13eea4bc17a7505df43b868711eaba04f4f085117eade195e1e3eb341067'
cases = prior['cases']
for case in cases:
    verify_case(case, prior['layout_root'])
C = O / 'native-campaign'
C.mkdir(exist_ok=True)
assert not (C / 'campaign.json').exists()
new_files = {str(p): file_digest(p) for p in (O / 'code').glob('*.py')}
assert set(Path(p).name for p in new_files) == {'trajectory_contract.py', 'released_waypoints.py'}
entries, audits = [], []
for mode in ['dense', 'released_waypoint_thinning']:
    config = copy.deepcopy(base)
    for key in ['files', 'policy_files']:
        config[key].update(new_files)
    config['policy_spec']['files'].update(new_files)
    config['policy_spec']['entrypoint'] = 'trajectory_contract:assemble'
    config['policy_spec']['configuration']['trajectory_mode'] = mode
    config['policy_spec']['configuration']['output'] = str(O / 'backend-traces' / mode)
    config['policy_environment']['PYTHONPATH'] = str(O / 'code') + ':' + config['policy_environment']['PYTHONPATH']
    rp = O / 'runtimes' / (mode + '.json')
    rp.parent.mkdir(exist_ok=True)
    atomic_json(rp, config)
    runtime = NativeRuntime(config)
    identity = runtime.identity()
    target = C / 'harnesses' / mode
    shutil.copytree(Path(parent['harness']['root']), target, symlinks=False)
    atomic_json(target / 'assets.json', identity)
    assert file_digest(target / 'code/classify_objects.py') == parent['expert']['revision']
    harness = manifest(target, 'trajectory_' + mode)
    revision = verify_harness(harness)
    admission = runtime.admit(harness, O / 'native-preparation/admission' / mode)
    check = runtime.check()
    assert admission['accepted'] and check['ready'], (admission, check)
    audits.append(dict(condition=mode, runtime=str(rp), runtime_sha256=file_digest(rp), check=check))
    entries.append(dict(name=mode, expert=parent['expert'], harness=harness, harness_sha256=revision,
                        runtime=str(rp), runtime_sha256=file_digest(rp),
                        origin=dict(candidate='capability_feedback_2', source_sha256=parent['expert']['revision'],
                                    proposed_memory_unchanged=True, policy_code_unchanged=True)))
atomic_json(O / 'native-preparation/runtime-preflights.json', audits)
atomic_json(C / 'campaign.json', dict(schema='physicalrsi.rgb-campaign/v1',
    utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    protocol=str(O / 'inputs/protocol.json'), protocol_sha256=file_digest(O / 'inputs/protocol.json'),
    runtime=entries[0]['runtime'], runtime_sha256=entries[0]['runtime_sha256'],
    per_entry_runtime=True, layout_root=prior['layout_root'], cases=cases, entries=entries,
    planned_cases=10, api_calls=0, selection='Manual execution-contract diagnosis; no policy promotion',
    raw_task_budget_unchanged=1100))
print(json.dumps(dict(state='prepared',conditions=2,planned_cases=10,api_calls=0)))
