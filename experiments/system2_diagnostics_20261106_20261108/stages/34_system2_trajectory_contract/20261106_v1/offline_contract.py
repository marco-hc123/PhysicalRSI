"""CPU checks of saved trajectories and released waypoint selection; no new plans."""
import datetime
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

L = Path('/mnt/data/joey_tr/physical-RSI/result/34_system2_trajectory_contract/20261106_v1')
P = Path('/mnt/data/joey_tr/physical-RSI/result/32_system2_lift_gate_diagnosis/20261106_v1')
I = Path('/mnt/data/joey_tr/physical-RSI/result/16_system2_integration/25_system2_integration_20261030T050100Z/integration-sources')
sys.path[:0] = [str(L / 'code'), str(I), str(I / 'framework-validation-v3')]
from trajectory_contract import select_path


def read(p):
    return json.loads(p.read_text())


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


O = L / 'offline-contract'
assert not O.exists(), 'Do not overwrite completed checks'
O.mkdir()
rows = []
cfg = read(P / 'native-validation/analysis/frozen-runtime.json')['policy_spec']['configuration']
for study in ['planning-recovery', 'planning-return']:
    for r in read(P / study / 'results.json'):
        if not r['trajectory_returned']:
            continue
        path = P / study / 'trajectories' / ('job%02d.npy' % r['job_id'])
        dense = np.load(path, allow_pickle=False)
        original, control = select_path(dense, r['start'], 'dense')
        sampled, treatment = select_path(dense, r['start'], 'released_waypoint_thinning')
        assert np.array_equal(original, dense)
        assert np.array_equal(sampled, dense[treatment['indices']])
        assert len(sampled) <= len(dense)
        limits = cfg['joint_limits'][r['action']['arm']]
        assert np.all(dense >= np.asarray(limits['low'])) and np.all(dense <= np.asarray(limits['high']))
        rows.append(dict(study=study, job_id=r['job_id'], layout=r['layout'], seed=r['seed'],
                         source=str(path), source_sha256=sha(path), start=r['start'],
                         control=control, treatment=treatment, passed=True))
assert len(rows) == 24
invalid = []
for name, dense, start in [
    ('empty', [], [0.] * 6),
    ('nonfinite', [[float('nan')] * 6], [0.] * 6),
    ('dimension', [[0.] * 5], [0.] * 6),
    ('over_native_bound', [[0.] * 6] * 501, [0.] * 6),
    ('adjacent_over_released_step_bound', [[.2] * 6], [0.] * 6),
]:
    try:
        select_path(dense, start, 'released_waypoint_thinning')
    except (ValueError, RuntimeError, AssertionError) as exc:
        invalid.append(dict(name=name, rejected=True, exception_type=type(exc).__name__))
    else:
        raise AssertionError('Invalid fixture accepted: ' + name)
result = dict(state='passed', utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              saved_trajectories=24, selection_checks=48, invalid_fixture_checks=len(invalid),
              dense_waypoints=sum(r['control']['executed_waypoints'] for r in rows),
              selected_waypoints=sum(r['treatment']['executed_waypoints'] for r in rows),
              rows=rows, invalid_fixtures=invalid, script_sha256=sha(Path(__file__)),
              api_calls=0, gpu_used=False, new_native_cases=0, new_solver_calls=0,
              limitations=['Saved trajectories from prior stage, not new independent native episodes.',
                           'Geometric bounds and unchanged endpoints are not full collision certificates.',
                           'No observed-state tracking, gripper success or task completion is established by CPU checks.'])
(O / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k not in ['rows', 'invalid_fixtures']}))
