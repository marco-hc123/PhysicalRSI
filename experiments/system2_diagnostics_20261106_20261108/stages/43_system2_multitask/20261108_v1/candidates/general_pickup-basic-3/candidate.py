def policy(robot, memory):
    quats = {'left': [0.613, -0.3593, 0.6163, 0.3392], 'right': [0.3814, -0.6197, 0.3785, 0.572]}
    for arm in quats:
        norm = sum(v * v for v in quats[arm]) ** 0.5
        quats[arm] = [v / norm for v in quats[arm]]

    def move(arm, position):
        value = robot.approach(arm=arm, position_m=position, quaternion_wxyz=quats[arm])
        error = value.get('primitive_error')
        if error == 'no_collision_free_path':
            return 'rejected'
        if error:
            return 'uncertain'
        return 'returned'

    objects = robot.scene()['objects']
    if 'target_1' not in objects:
        return {'stop': 'target_not_detected', 'physical_success': 'unknown'}
    x, y, z = objects['target_1']['pose'][:3]
    preferred = 'left' if x <= 0 else 'right'
    for arm in [preferred, 'right' if preferred == 'left' else 'left']:
        status = move(arm, [x, y, 1.02])
        if status == 'rejected':
            continue
        if status == 'uncertain':
            return {'stop': 'approach_execution_uncertain', 'physical_success': 'unknown'}
        robot.gripper(arm=arm, command=1)
        status = move(arm, [x, y, 0.93])
        if status != 'returned':
            return {'stop': 'contact_' + status, 'physical_success': 'unknown'}
        robot.gripper(arm=arm, command=0)
        for lift_z in [1.10, 1.06]:
            status = move(arm, [x, y, lift_z])
            if status == 'rejected':
                continue
            if status == 'uncertain':
                return {'stop': 'lift_execution_uncertain', 'physical_success': 'unknown'}
            return {'stop': 'program_complete', 'physical_success': 'unknown', 'requested_lift_tool_z': lift_z}
        return {'stop': 'lift_plans_rejected', 'physical_success': 'unknown'}
    return {'stop': 'approach_plans_rejected', 'physical_success': 'unknown'}
