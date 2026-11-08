def policy(robot, memory):
    quats = {'left': [0.613, -0.3593, 0.6163, 0.3392], 'right': [0.3814, -0.6197, 0.3785, 0.572]}
    for arm in quats:
        norm = sum(v * v for v in quats[arm]) ** 0.5
        quats[arm] = [v / norm for v in quats[arm]]

    def move(arm, position):
        value = robot.approach(arm=arm, position_m=position, quaternion_wxyz=quats[arm])
        return value.get('primitive_error')

    objects = robot.scene()['objects']
    if 'target_1' not in objects:
        return {'stop': 'target_not_detected', 'physical_success': 'unknown'}
    x, y, z = objects['target_1']['pose'][:3]
    preferred = 'left' if x <= 0 else 'right'
    other = 'right' if preferred == 'left' else 'left'
    for arm in [preferred, other]:
        error = move(arm, [x, y, 1.02])
        if error == 'no_collision_free_path':
            continue
        if error is not None:
            return {'stop': 'approach_uncertain', 'primitive_error': error, 'physical_success': 'unknown'}
        robot.gripper(arm=arm, command=1)
        error = move(arm, [x, y, 0.93])
        if error is not None:
            return {'stop': 'contact_motion_error', 'primitive_error': error, 'physical_success': 'unknown'}
        robot.gripper(arm=arm, command=0)
        for height in [0.98, 1.06]:
            error = move(arm, [x, y, height])
            if error is not None:
                return {'stop': 'lift_motion_error', 'primitive_error': error, 'requested_tool_z': height, 'physical_success': 'unknown'}
        return {'stop': 'program_complete', 'physical_success': 'unknown'}
    return {'stop': 'approach_plans_rejected', 'physical_success': 'unknown'}
