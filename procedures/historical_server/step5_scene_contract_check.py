"""Cloud-only, zero-API/zero-native regression for the diagnosed scene-key error."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import difflib
import hashlib
import json
import os
import shutil
import subprocess
import sys
import traceback

R = Path('/mnt/data/physical-RSI')
PRIOR = R/'result/26_system2_iterations_20261030T074100Z'
BASE = R/'result/25_system2_integration_20261030T050100Z'
PROPOSAL = PRIOR/'workspace/rounds/round-000000/proposals/classify_objects/skill-proposal.json'


def read(p):
    return json.loads(Path(p).read_text())


def write(p, value):
    Path(p).write_text(json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2)+'\n')


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def pins():
    freeze = read(R/'result/23_protocol_freeze_20261029T132917Z/source-freeze.json')
    for row in freeze['deployment_files']:
        assert sha(row['path']) == row['sha256'], row['path']
    for path, expected in freeze['recorded_protocol_and_framework_hashes'].items():
        assert sha(path) == expected, path
    return dict(deployment=len(freeze['deployment_files']),
                framework=len(freeze['recorded_protocol_and_framework_hashes']))


assert os.geteuid() == 0
current = read(R/'result/CURRENT_STEP5.json')
assert current['stage'] == 'registered_stop_diagnosed_and_audited' and not current.get('pid')
gpu = subprocess.run(['nvidia-smi', '--query-compute-apps=pid', '--format=csv,noheader'],
                     capture_output=True, text=True, check=True).stdout.strip()
assert not gpu, 'Do not overlap an active GPU experiment'
for pid in [70246, 73032, 76657, 100629]:
    assert not Path(f'/proc/{pid}').exists(), f'Prior process unexpectedly present: {pid}'
stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
O = R/('result/27_scene_contract_repair_'+stamp)
O.mkdir()
sources = O/'procedure-sources'
sources.mkdir()
for name in ['step5_scene_contract_v1.py', 'step5_scene_contract_check.py']:
    shutil.copyfile(Path(__file__).parent/name, sources/name)
cfg = read(PRIOR/'runtime.json')
F = BASE/'integration-sources/framework-validation-v3'
sys.path[:0] = [str(sources), str(F)]
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
proposal_hash = sha(PROPOSAL)
watched = [PRIOR/'protocol.json', PRIOR/'parent-state-verification.json',
           PRIOR/'interruption-audit/verification.json', PRIOR/'step5-stopped-results.json',
           PRIOR/'workspace/state/current.json', PRIOR/'workspace/state/validation.json']
before = {str(p): sha(p) for p in watched}
registration = dict(schema='physicalrsi.scene-contract-repair-diagnostic/v1',
    registered_utc=datetime.now(timezone.utc).isoformat(), pid=os.getpid(),
    scope='Manual diagnostic correction plus synthetic CPU contract gate; NOT System2 improvement evidence',
    native_episode_budget=0, real_api_call_budget=0, physical_success_claim=False,
    source_proposal=str(PROPOSAL), source_proposal_sha256=proposal_hash,
    original_receipts=before, isolation_runtime=cfg['policy_spec']['runtime'],
    procedure_sha256={str(p): sha(p) for p in sources.glob('*.py')},
    fixture_origin='Artificial constants and public interface category strings; no validation scene read',
    action='Keep original proposal/active harness immutable; create separate manually patched diagnostic source',
    stop_on_check_failure=True, automatic_native_or_model_retry=False)
write(O/'registration.json', registration)
print(json.dumps(dict(directory=str(O), stage='registered_cpu_checks_only')), flush=True)

try:
    from PhysicalRSI_core.infra.storage import digest
    from step5_scene_contract_v1 import (CheckedCodeProposer, SCENE_KEY_CONTRACT,
        clarified_api, diagnostic_repair, fixtures, run_case)
    verified_pins = pins()
    original = read(PROPOSAL)
    source = original['source']
    assert digest(source) == original['source_sha256']
    fixed = diagnostic_repair(source)
    (O/'manually-repaired-policy.py').write_text(fixed)
    (O/'manual-repair.diff').write_text(''.join(difflib.unified_diff(
        source.splitlines(True), fixed.splitlines(True), fromfile='original-model-source',
        tofile='manually-repaired-diagnostic-source')))
    api = clarified_api(cfg['skill_api'])
    write(O/'clarified-skill-api.json', api)
    write(O/'manual-repair-provenance.json', dict(origin='manual_diagnostic_patch',
        model_generated=False, original_source_sha256=digest(source),
        repaired_source_sha256=digest(fixed), memory_changed=False,
        active_harness_changed=False, candidate_adopted=False, physical_qualification=False))

    class FakeConfig:
        def public(self):
            return dict(kind='offline_response_fixture', network=False)

    class ResponseFixture:
        config = FakeConfig()
        def __init__(self, text):
            self.text, self.calls = text, 0
        def complete(self, messages, tools):
            self.calls += 1
            assert not tools
            request = json.loads(messages[1]['content'])
            assert request['primitive_api']['scene_object_key_contract'] == SCENE_KEY_CONTRACT
            return json.dumps(dict(source=self.text, memory={}, rationale='CPU test fixture')), [], {}

    feedback = [dict(task='classify_objects', split='development', scope='synthetic adapter test only')]
    offline_models = []
    for label, text, should_pass in [('original', source, False), ('manual_repair', fixed, True)]:
        output = O/label
        output.mkdir()
        fake = ResponseFixture(text)
        checked = CheckedCodeProposer(fake, isolation_runtime=cfg['policy_spec']['runtime'])
        try:
            checked.propose(task='classify_objects', source='', memory={}, feedback=feedback,
                            skill_api=api, output=output)
            passed = True
        except ValueError:
            passed = False
        assert passed == should_pass, (label, passed)
        assert fake.calls == 1, 'No automatic regeneration is permitted'
        offline_models.append(dict(label=label, calls_to_offline_response_fixture=fake.calls,
                                   gate_passed=passed, real_api_calls=0))
    old = read(O/'original/cpu-contract-gate/gate-result.json')
    bad = old['cases']['named']
    assert not bad['completed'] and "invalid literal for int() with base 10: 'basket_1'" in bad['stderr_tail']
    assert [row['method'] for row in bad['calls']] == ['scene']
    passed = read(O/'manual_repair/cpu-contract-gate/gate-result.json')
    assert passed['passed'] and len(passed['cases']) == 3
    mixed = passed['cases']['underscore_and_repeated_category']['calls']
    counts = Counter(c['method'] for c in mixed)
    assert counts == {'scene': 1, 'approach': 12, 'gripper': 8, 'reobserve': 8}, counts
    approaches = [c['kwargs']['position_m'] for c in mixed if c['method'] == 'approach']
    # Item iteration is left-to-right: watch_1, toy_car_1, pen_1, watch_2.
    releases = approaches[2::3]
    assert releases[0] == releases[3], 'Repeated category must use the same basket'
    assert len({tuple(p) for p in releases[:3]}) == 3, 'Three classes must retain distinct baskets'

    extras = {}
    for mode in ['no_path', 'transport_timeout']:
        extras[mode] = run_case(fixed, {}, fixtures()['named'], runtime=cfg['policy_spec']['runtime'],
                                output=O/mode, mode=mode)
    assert extras['no_path']['completed']
    assert [c['method'] for c in extras['no_path']['calls']] == ['scene', 'approach']
    assert not extras['transport_timeout']['completed']
    assert extras['transport_timeout']['error'].startswith('TimeoutError:')
    for name in ['basket', 'basket_0']:
        extras['malformed_'+name] = run_case(fixed, {}, {name: fixtures()['named']['basket_1']},
            runtime=cfg['policy_spec']['runtime'], output=O/('malformed_'+name))
        assert not extras['malformed_'+name]['completed']
        assert 'Expected scene object key' in extras['malformed_'+name]['stderr_tail']
        assert [c['method'] for c in extras['malformed_'+name]['calls']] == ['scene']
    write(O/'extra-contract-cases.json', extras)
    assert sha(PROPOSAL) == proposal_hash
    assert {str(p): sha(p) for p in watched} == before
    assert pins() == verified_pins
    gpu_after = subprocess.run(['nvidia-smi', '--query-compute-apps=pid', '--format=csv,noheader'],
                              capture_output=True, text=True, check=True).stdout.strip()
    assert not gpu_after
    verification = dict(complete=True, verified_utc=datetime.now(timezone.utc).isoformat(),
        original_error_reproduced_before_motion=True, manual_correction_contract_passed=True,
        named_empty_underscore_repeated_category_cases=True, no_path_recoverable=True,
        transport_failure_still_fatal=True, malformed_keys_rejected_before_motion=True,
        gate_wrapper_offline_checks=offline_models, real_api_calls=0, native_episodes=0,
        original_proposal_and_receipts_unchanged=True, original_pins=verified_pins,
        active_harness_unchanged=True, physical_qualification=False, candidate_adopted=False,
        source=str(O/'manually-repaired-policy.py'), api=str(O/'clarified-skill-api.json'),
        next='Register a fresh formal continuation using the explicit API and checked proposer; CPU gate is not native success or model self-improvement evidence')
    write(O/'verification.json', verification)
    print(json.dumps(dict(directory=str(O), verification=verification), ensure_ascii=False), flush=True)
except BaseException as error:
    write(O/'diagnostic-failed.json', dict(error=type(error).__name__+': '+str(error),
        traceback=traceback.format_exc(), native_episodes=0, real_api_calls=0))
    raise
