"""Single-variable waypoint selection diagnostic; all existing action guards stay."""
import hashlib
import json
from pathlib import Path
import time

import numpy as np
from step4_native_primitives_v3 import Backend, ContractPrimitives, ObservedObstacles
from released_waypoints import thin_native_path


def write(path, record):
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(record, indent=2, allow_nan=False) + '\n')
    tmp.replace(path)


def select_path(dense, start, mode):
    path = np.asarray(dense, dtype=np.float64)
    initial = np.asarray(start, dtype=np.float64)
    if path.ndim != 2 or path.shape[1] != 6 or not 1 <= len(path) <= 500 or not np.isfinite(path).all():
        raise ValueError('Invalid bounded native path')
    if mode == 'dense':
        indices = list(range(len(path)))
        diagnostic = {'selection': 'all native samples'}
    elif mode == 'released_waypoint_thinning':
        indices, diagnostic = thin_native_path(path, initial, max_joint_step=.12, chord_tolerance=.01)
        if diagnostic['native_adjacent_over_bound'] or diagnostic['max_selected_joint_delta_rad'] > .1200001:
            raise ValueError('Released selection exceeds its .12rad bound')
        if diagnostic['max_chord_deviation_rad'] > .0100001:
            raise ValueError('Released selection exceeds its .01rad chord tolerance')
    else:
        raise ValueError('Unknown frozen trajectory mode')
    assert indices and indices == sorted(set(indices)) and indices[-1] == len(path) - 1
    selected = path[indices]
    assert np.array_equal(selected[-1], path[-1])
    if np.abs(np.diff(np.vstack([initial, selected]), axis=0)).max() > .25:
        raise ValueError('Selected path exceeds unchanged primitive .25rad guard')
    return selected.tolist(), dict(indices=indices, dense_waypoints=len(path), executed_waypoints=len(indices),
                                  endpoint_preserved=True, selection_diagnostic=diagnostic)


class DiagnosticBackend(Backend):
    def __init__(self, configuration, output):
        super().__init__(configuration, output)
        self.mode = configuration['trajectory_mode']
        assert self.mode in ['dense', 'released_waypoint_thinning']
        self.counter = 0
        self.last_record = None

    def plan(self, **kwargs):
        self.counter += 1
        path = self.output / ('trajectory-%04d.json' % self.counter)
        record = dict(index=self.counter, mode=self.mode,
                      inputs={k: v for k, v in kwargs.items() if k != 'deadline'},
                      scope='Native planned samples; static geometry only, not a full scene collision certificate.')
        began = time.monotonic()
        try:
            dense = super().plan(**kwargs)
            selected, diagnostic = select_path(dense, kwargs['start'], self.mode)
            record.update(state='plan_returned', dense_path=dense, selected_path=selected, **diagnostic)
            record['dense_path_sha256'] = hashlib.sha256(json.dumps(dense, separators=(',', ':')).encode()).hexdigest()
        except BaseException as exc:
            record.update(state='planning_or_selection_rejected', error_type=type(exc).__name__, error=str(exc))
            raise
        finally:
            record['planning_and_selection_seconds'] = time.monotonic() - began
            write(path, record)
            self.last_record = (path, record)
        return selected


class DiagnosticPrimitives(ContractPrimitives):
    def __init__(self, diagnostic_backend, **kwargs):
        super().__init__(**kwargs)
        self.diagnostic_backend = diagnostic_backend

    def approach(self, *, arm, position_m, quaternion_wxyz):
        kwargs = dict(arm=arm, position_m=position_m, quaternion_wxyz=quaternion_wxyz)
        result = None
        caught = None
        previous_counter = self.diagnostic_backend.counter
        try:
            result = super().approach(**kwargs)
            return result
        except BaseException as exc:
            caught = dict(type=type(exc).__name__, message=str(exc))
            raise
        finally:
            backend = self.diagnostic_backend
            if backend.counter > previous_counter and backend.last_record:
                path, record = backend.last_record
                if result is not None:
                    record['primitive_return'] = result
                    if record.get('selected_path'):
                        key = kwargs['arm'] + '_arm_joint_state'
                        record['final_observed_joint_error_rad'] = float(np.max(np.abs(
                            np.asarray(result['state'][key]) - np.asarray(record['selected_path'][-1]))))
                if caught is not None:
                    record['execution_exception'] = caught
                write(path, record)


def assemble(channel, *, configuration, identity, own, pool=None):
    backend = own(DiagnosticBackend(configuration, Path(configuration['output']) / identity['episode'] / identity['actor']))
    perception = ObservedObstacles(channel=channel, estimate=backend.estimate, max_age_s=180)
    return DiagnosticPrimitives(diagnostic_backend=backend, observe=channel.observe, plan=backend.plan,
                                step=channel.step, perceive=perception.observe,
                                dimensions=configuration['dimensions'], joint_limits=configuration['joint_limits'],
                                max_joint_step=.25, timeout_s=180, max_waypoints=500, gripper_steps=6)
