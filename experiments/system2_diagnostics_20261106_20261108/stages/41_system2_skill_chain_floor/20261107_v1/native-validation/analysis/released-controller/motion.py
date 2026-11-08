"""Shihao cover control with official RGB initial geometry and proprioception."""
from physicalrsi_skill_library.stage_programs import execute as _execute_memory
import json, math, os, time
from pathlib import Path
import cv2
import numpy as np
from scipy.spatial.transform import Rotation
from XPolicyLab.model_template import ModelTemplate
from .curobo_planner import CuroboPlanner
ARMS = ('left', 'right')
BASE = {'left': [-0.3, -0.45, 0.765, 0.707, 0, 0, 0.707], 'right': [0.3, -0.45, 0.765, 0.707, 0, 0, 0.707]}
QUAT = {'left': [0.613, -0.3593, 0.6163, 0.3392], 'right': [0.3814, -0.6197, 0.3785, 0.572]}

class Motion(ModelTemplate):

    def __init__(self, model_cfg):
        super().__init__()
        self.planners = model_cfg.get('planners') or {a: CuroboPlanner(robot_origin_pose=[0, 0, 0, 1, 0, 0, 0], active_joints_name=[f'joint{i}' for i in range(1, 7)], all_joints=[f'joint{i}' for i in range(1, 7)], dt=0.004, yml_path=str(Path(__file__).parent / 'assets/x5/curobo.yml'), table_height=-0.025) for a in ARMS}
        self.reset()

    def reset(self):
        for w in getattr(self, 'writers', {}).values():
            w.release()
        if getattr(self, 'trace', None):
            self.trace.close()
        self.pending_rgb = None
        self.writers = {}
        self.trace = None
        self.state = None
        self.rgb = None
        self.program = None
        self.failure = None
        self.stage = 'initial'
        self.count = 0
        self.targets = None
        self.grip = {a: 1.0 for a in ARMS}

    def event(self, **data):
        if self.trace and getattr(self, '_saved_stage', None) != self.stage and (self.rgb is not None):
            self._saved_stage = self.stage
            for camera in ('cam_left_wrist', 'cam_right_wrist'):
                if camera in getattr(self, 'vision', {}):
                    cv2.imwrite(str(Path(self.trace.name).parent / f'{self.count:04d}_{self.stage}_{camera}.jpg'), cv2.cvtColor(self.vision[camera], cv2.COLOR_RGB2BGR))
            cv2.imwrite(str(Path(self.trace.name).parent / f'{self.count:04d}_{self.stage}.jpg'), cv2.cvtColor(self.rgb, cv2.COLOR_RGB2BGR))
        if self.trace:
            self.trace.write(json.dumps({'time_ns': time.time_ns(), 'action_index': self.count, 'stage': self.stage, **data}, default=lambda x: x.tolist()) + '\n')
            self.trace.flush()

    def _memory_update_obs_0(self, _frame, _context):
        if _frame.get('done'):
            return _frame
        self.operation_trace.append('classify_objects.observation.capture')
        if 'a' in _frame['locals']:
            a = _frame['locals']['a']
        if 'k' in _frame['locals']:
            k = _frame['locals']['k']
        if 'name' in _frame['locals']:
            name = _frame['locals']['name']
        if 'obs' in _frame['locals']:
            obs = _frame['locals']['obs']
        if 'p' in _frame['locals']:
            p = _frame['locals']['p']
        if 'trace_started' in _frame['locals']:
            trace_started = _frame['locals']['trace_started']
        if 'v' in _frame['locals']:
            v = _frame['locals']['v']
        if 'video_seconds' in _frame['locals']:
            video_seconds = _frame['locals']['video_seconds']
        if 'video_started' in _frame['locals']:
            video_started = _frame['locals']['video_started']
        if 'w' in _frame['locals']:
            w = _frame['locals']['w']
        self.state = {k: np.asarray(v).copy() for k, v in obs['state'].items() if k.endswith('_arm_joint_state') or k.endswith('_ee_joint_state') or k.endswith('_ee_pose')}
        self.instruction = obs.get('instruction', '')
        self.rgb = np.asarray(obs['vision']['cam_head']['color']).copy()
        self.vision = {k: np.asarray(v['color']).copy() for k, v in obs['vision'].items()}
        _values = locals()
        _frame['locals'].update({k: _values[k] for k in ['a', 'k', 'name', 'obs', 'p', 'trace_started', 'v', 'video_seconds', 'video_started', 'w'] if k in _values})
        return _frame

    def _memory_update_obs_1(self, _frame, _context):
        if _frame.get('done'):
            return _frame
        self.operation_trace.append('classify_objects.observation.record_and_initialize')
        if 'a' in _frame['locals']:
            a = _frame['locals']['a']
        if 'k' in _frame['locals']:
            k = _frame['locals']['k']
        if 'name' in _frame['locals']:
            name = _frame['locals']['name']
        if 'obs' in _frame['locals']:
            obs = _frame['locals']['obs']
        if 'p' in _frame['locals']:
            p = _frame['locals']['p']
        if 'trace_started' in _frame['locals']:
            trace_started = _frame['locals']['trace_started']
        if 'v' in _frame['locals']:
            v = _frame['locals']['v']
        if 'video_seconds' in _frame['locals']:
            video_seconds = _frame['locals']['video_seconds']
        if 'video_started' in _frame['locals']:
            video_started = _frame['locals']['video_started']
        if 'w' in _frame['locals']:
            w = _frame['locals']['w']
        if self.trace is None:
            p = Path(os.environ['CLASSIFY_TRACE_DIR']) / str(time.time_ns())
            p.mkdir(parents=True)
            self.trace = (p / 'trace.jsonl').open('w')
            os.environ['CLASSIFY_EPISODE_TRACE_DIR'] = str(p)
        video_started = time.monotonic()
        for name, w in self.writers.items():
            w.write(cv2.cvtColor(np.asarray(obs['vision'][name]['color']), cv2.COLOR_RGB2BGR))
        if self.targets is None:
            self.targets = {a: self.state[a + '_arm_joint_state'].astype('float32') for a in ARMS}
        video_seconds = time.monotonic() - video_started
        _values = locals()
        _frame['locals'].update({k: _values[k] for k in ['a', 'k', 'name', 'obs', 'p', 'trace_started', 'v', 'video_seconds', 'video_started', 'w'] if k in _values})
        return _frame

    def _memory_update_obs_2(self, _frame, _context):
        if _frame.get('done'):
            return _frame
        self.operation_trace.append('classify_objects.evidence.observation')
        if 'a' in _frame['locals']:
            a = _frame['locals']['a']
        if 'k' in _frame['locals']:
            k = _frame['locals']['k']
        if 'name' in _frame['locals']:
            name = _frame['locals']['name']
        if 'obs' in _frame['locals']:
            obs = _frame['locals']['obs']
        if 'p' in _frame['locals']:
            p = _frame['locals']['p']
        if 'trace_started' in _frame['locals']:
            trace_started = _frame['locals']['trace_started']
        if 'v' in _frame['locals']:
            v = _frame['locals']['v']
        if 'video_seconds' in _frame['locals']:
            video_seconds = _frame['locals']['video_seconds']
        if 'video_started' in _frame['locals']:
            video_started = _frame['locals']['video_started']
        if 'w' in _frame['locals']:
            w = _frame['locals']['w']
        trace_started = time.monotonic()
        self.event(state=self.state)
        self.event(video_write_seconds=video_seconds, trace_write_seconds=time.monotonic() - trace_started)
        _values = locals()
        _frame['locals'].update({k: _values[k] for k in ['a', 'k', 'name', 'obs', 'p', 'trace_started', 'v', 'video_seconds', 'video_started', 'w'] if k in _values})
        return _frame

    def update_obs(self, obs):
        return _execute_memory(self, __file__, 'Motion.update_obs', {'obs': obs})

    def action(self, arm=None, q=None):
        return joint_action(self.targets, self.grip, ARMS, arm, q)

    def hold_gripper(self, arm, value, repeats):
        yield from hold_gripper(self.grip, arm, value, repeats, self.action)

    def settle_capture(self, arm):
        self.grip[arm] = 0.0
        last = float(self.state[arm + '_ee_joint_state'][0])
        stable = 0
        for step in range(18):
            yield self.action()
            current = float(self.state[arm + '_ee_joint_state'][0])
            delta = abs(current - last)
            stable = stable + 1 if delta < 0.006 else 0
            self.event(capture_aperture=current, capture_aperture_delta=delta, capture_settle_action=step + 1, capture_stable_observations=stable)
            last = current
            if step >= 5 and stable >= 3:
                return
        self.event(capture_settle_limit=True)

    def qualify_grasp(self, arm, grasp, q):
        from .reach import qualify
        current = self.state[arm + '_arm_joint_state'].copy()
        planner = self.planners[arm]
        started = time.monotonic()

        def validate(candidate):
            last = current
            native = {}
            for stage, dz in [('approach', 0.07), ('contact', 0.0), ('capture_lift', 0.008), ('lift', 0.08)]:
                pose = [*grasp + [0, 0, dz], *candidate['q']]
                ik = planner.solve_ik_to_joint(candidate['joints'][stage], pose, BASE[arm])
                self.event(skill_choice_qualification_stage=stage, skill_choice_arm=arm, skill_choice_native_ik=ik['status'])
                if ik['status'] != 'Success':
                    return False
                path = planner.plan_joint(last, ik['joint_value'])
                self.event(skill_choice_qualification_stage=stage, skill_choice_arm=arm, skill_choice_native_path=path['status'])
                if path['status'] != 'Success':
                    return False
                native[stage] = np.asarray(ik['joint_value']).copy()
                last = native[stage]
            candidate['joints'] = native
            candidate['native_qualified'] = True
            return True
        candidate = qualify(arm, grasp, q, current, validator=validate)
        self.event(skill_choice_qualified=candidate is not None, skill_choice_arm=arm, skill_choice_seconds=time.monotonic() - started)
        return candidate

    def move(self, arm, pose=None, max_waypoints=8):
        started = time.monotonic()
        current = self.state[arm + '_arm_joint_state']
        planner = self.planners[arm]
        if self.stage in ('observe_retract', 'contact_recovery_view') and arm in getattr(self, 'look_joints', {}):
            pose = None
            result = planner.plan_joint(current, self.look_joints[arm])
        elif self.stage in ('approach', 'contact') and getattr(self, 'grasp_plan', None) is not None:
            joint = self.grasp_plan['joints'][self.stage]
            self.event(native_grasp_endpoint_status='prequalified', native_qualified_arm=arm)
            result = planner.plan_joint(current, joint)
        elif self.stage in ('transport', 'basket_lower'):
            from .axis_ik import axis_ik
            candidate = axis_ik(arm, pose, current)
            self.event(cone_ik=candidate)
            if candidate['status'] != 'Success':
                raise RuntimeError('approach cone IK rejected')
            pose = candidate['target_pose']
            ik = planner.solve_ik_to_joint(candidate['joint_value'], pose, BASE[arm])
            self.event(native_endpoint_ik_status=ik['status'])
            if ik['status'] != 'Success':
                raise RuntimeError('native endpoint IK rejected')
            result = planner.plan_joint(current, ik['joint_value'])
        else:
            result = planner.plan_joint(current, np.zeros_like(current)) if pose is None else planner.plan_path(curr_joint_pos=current, target_ee_pose=list(map(float, pose)), real_robot_pose=BASE[arm])
        if result.get('status') != 'Success':
            raise RuntimeError(f'CuRobo failed {arm} {pose}')
        from .waypoints import thin_native_path
        path = np.asarray(result['position'], np.float32)
        indices, diagnostic = thin_native_path(path, current)
        self.event(arm=arm, target_pose=pose, path_length=len(path), sampled=len(indices), waypoint_geometry=diagnostic, planning_seconds=time.monotonic() - started)
        yield from follow_waypoints(path, indices, arm, self.action)
        if self.stage == 'contact':
            for _ in range(3):
                yield self.action(arm, path[-1])
            self.event(contact_transaction=True, contact_actual_pose=self.state[arm + '_ee_pose'], contact_target_pose=pose)
            return
        for wait in range(41):
            joint_error = float(np.max(np.abs(self.state[arm + '_arm_joint_state'] - path[-1])))
            position_error = 0.0
            rotation_error = 0.0
            if pose is not None:
                actual = self.state[arm + '_ee_pose']
                target = np.asarray(pose)
                position_error = float(np.linalg.norm(actual[:3] - target[:3]))
                rotation_error = float((Rotation.from_quat(actual[[4, 5, 6, 3]]).inv() * Rotation.from_quat(target[[4, 5, 6, 3]])).magnitude())
            self.event(endpoint_wait=wait, arm=arm, joint_error_rad=joint_error, position_error_m=position_error, rotation_error_rad=rotation_error)
            if pose is None and joint_error <= 0.02 or (pose is not None and position_error <= 0.01 and (rotation_error <= 0.1)):
                return
            if wait == 40:
                raise RuntimeError('motion endpoint did not converge before next stage')
            yield self.action(arm, path[-1])

    def _memory_get_action_0(self, _frame, _context):
        if _frame.get('done'):
            return _frame
        self.operation_trace.append('classify_objects.motion.prepare_generator')
        if 'a' in _frame['locals']:
            a = _frame['locals']['a']
        if 'action' in _frame['locals']:
            action = _frame['locals']['action']
        if 'detections' in _frame['locals']:
            detections = _frame['locals']['detections']
        if self.count >= 1080 and self.failure is None:
            self.failure = 'budget_terminal_release'
            self.stage = 'failure_hold'
            self.targets = {a: self.state[a + '_arm_joint_state'].astype('float32') for a in ARMS}
            self.grip = {a: 1.0 for a in ARMS}
            self.event(physical_release=True)
        if self.program is None and self.failure is None:
            self.program = self.run()
        _values = locals()
        _frame['locals'].update({k: _values[k] for k in ['a', 'action', 'detections'] if k in _values})
        return _frame

    def _memory_get_action_1(self, _frame, _context):
        if _frame.get('done'):
            return _frame
        self.operation_trace.append('classify_objects.motion.advance_generator')
        if 'a' in _frame['locals']:
            a = _frame['locals']['a']
        if 'action' in _frame['locals']:
            action = _frame['locals']['action']
        if 'detections' in _frame['locals']:
            detections = _frame['locals']['detections']
        try:
            if self.failure is not None:
                action = self.action()
            elif self.pending_rgb is not None:
                detections = self.pending_rgb
                self.pending_rgb = None
                action = self.program.send(detections)
            else:
                action = next(self.program)
            if isinstance(action, dict) and action.get('_rgb_request'):
                _result = action
                _frame['result'] = _result
                _frame['done'] = True
                return _frame
        except StopIteration:
            action = self.action()
        except RuntimeError as exc:
            self.failure = repr(exc)
            self.stage = 'failure_hold'
            self.targets = {a: self.state[a + '_arm_joint_state'].astype('float32') for a in ARMS}
            self.grip = {a: 1.0 for a in ARMS}
            self.event(failure=self.failure, physical_release=True)
            action = self.action()
        _values = locals()
        _frame['locals'].update({k: _values[k] for k in ['a', 'action', 'detections'] if k in _values})
        return _frame

    def _memory_get_action_2(self, _frame, _context):
        if _frame.get('done'):
            return _frame
        self.operation_trace.append('classify_objects.action.count_and_emit')
        if 'a' in _frame['locals']:
            a = _frame['locals']['a']
        if 'action' in _frame['locals']:
            action = _frame['locals']['action']
        if 'detections' in _frame['locals']:
            detections = _frame['locals']['detections']
        self.count += 1
        self.event(action=action)
        _result = [action]
        _frame['result'] = _result
        _frame['done'] = True
        return _frame
        _values = locals()
        _frame['locals'].update({k: _values[k] for k in ['a', 'action', 'detections'] if k in _values})
        return _frame

    def get_action(self):
        return _execute_memory(self, __file__, 'Motion.get_action', {})

from physicalrsi_skill_library.joint_skills import joint_action, hold_gripper, follow_waypoints
