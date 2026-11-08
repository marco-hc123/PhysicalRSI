def policy(robot, memory):
    quats = {'left': [0.613, -0.3593, 0.6163, 0.3392], 'right': [0.3814, -0.6197, 0.3785, 0.572]}
    for arm in quats:
        norm = sum(v * v for v in quats[arm]) ** 0.5
        quats[arm] = [v / norm for v in quats[arm]]

    def move(arm, position):
        result = robot.approach(arm=arm, position_m=position, quaternion_wxyz=quats[arm])
        return result.get('primitive_error')

    objects = robot.scene()['objects']
    if 'target_1' not in objects:
        return {'stop': 'target_not_detected', 'physical_success': 'unknown'}
    x, y, z = objects['target_1']['pose'][:3]
    preferred = 'left' if x <= 0 else 'right'
    for arm in [preferred, 'right' if preferred == 'left' else 'left']:
        error = move(arm, [x, y, 1.02])
        if error == 'no_collision_free_path':
            continue
        if error:
            return {'stop': 'primitive_error_uncertain', 'stage': 'approach', 'physical_success': 'unknown'}

        result = robot.gripper(arm=arm, command=1)
        if result.get('primitive_error'):
            return {'stop': 'primitive_error_uncertain', 'stage': 'open', 'physical_success': 'unknown'}
        error = move(arm, [x, y, 0.93])
        if error:
            reason = 'contact_plan_rejected' if error == 'no_collision_free_path' else 'primitive_error_uncertain'
            return {'stop': reason, 'stage': 'contact', 'physical_success': 'unknown'}
        result = robot.gripper(arm=arm, command=0)
        if result.get('primitive_error'):
            return {'stop': 'primitive_error_uncertain', 'stage': 'close', 'physical_success': 'unknown'}

        for stage, height in [('lift_clearance', 0.995), ('lift_final', 1.06)]:
            error = move(arm, [x, y, height])
            if error == 'no_collision_free_path':
                if stage == 'lift_clearance':
                    continue
                return {'stop': 'lift_plan_rejected', 'stage': stage, 'physical_success': 'unknown'}
            if error:
                return {'stop': 'primitive_error_uncertain', 'stage': stage, 'physical_success': 'unknown'}
        return {'stop': 'motion_sequence_returned', 'physical_success': 'unknown'}
    return {'stop': 'approach_plans_rejected', 'physical_success': 'unknown'}
