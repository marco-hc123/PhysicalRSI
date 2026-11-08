def policy(robot, memory):
    quats = {'left': [0.613, -0.3593, 0.6163, 0.3392], 'right': [0.3814, -0.6197, 0.3785, 0.572]}
    for arm in quats:
        norm = sum(v*v for v in quats[arm])**0.5
        quats[arm] = [v/norm for v in quats[arm]]

    def move(arm, position):
        value = robot.approach(arm=arm, position_m=position, quaternion_wxyz=quats[arm])
        return value.get('primitive_error')

    objects = robot.scene()['objects']
    if 'target_1' not in objects:
        return {'stop': 'target_not_detected', 'physical_success': 'unknown'}
    x, y = objects['target_1']['pose'][:2]
    preferred = 'left' if x <= 0 else 'right'
    alternate = 'right' if preferred == 'left' else 'left'
    for arm in [preferred, alternate]:
        error = move(arm, [x, y, 1.02])
        if error == 'no_collision_free_path':
            continue
        if error:
            return {'stop': 'approach_error', 'primitive_error': error, 'physical_success': 'unknown'}
        robot.gripper(arm=arm, command=1)
        error = move(arm, [x, y, 0.93])
        if error:
            return {'stop': 'contact_plan_rejected' if error == 'no_collision_free_path' else 'contact_error', 'physical_success': 'unknown'}
        robot.gripper(arm=arm, command=0)
        for lift_z in [0.97, 1.06]:
            error = move(arm, [x, y, lift_z])
            if error:
                return {'stop': 'lift_plan_rejected' if error == 'no_collision_free_path' else 'lift_error', 'requested_tool_z_m': lift_z, 'physical_success': 'unknown'}
        return {'stop': 'program_complete', 'physical_success': 'unknown'}
    return {'stop': 'approach_plans_rejected', 'physical_success': 'unknown'}
