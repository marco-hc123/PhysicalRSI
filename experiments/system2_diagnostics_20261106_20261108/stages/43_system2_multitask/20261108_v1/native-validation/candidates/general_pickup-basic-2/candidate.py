def policy(robot, memory):
    quats = {'left': [0.613, -0.3593, 0.6163, 0.3392], 'right': [0.3814, -0.6197, 0.3785, 0.572]}
    for arm in quats:
        norm = sum(v * v for v in quats[arm]) ** 0.5
        quats[arm] = [v / norm for v in quats[arm]]
    def move(arm, position):
        value = robot.approach(arm=arm, position_m=position, quaternion_wxyz=quats[arm])
        if 'primitive_error' not in value:
            return 'issued'
        if value['primitive_error'] == 'no_collision_free_path':
            return 'rejected'
        return 'uncertain'
    objects = robot.scene()['objects']
    if 'target_1' not in objects:
        return {'stop': 'target_not_detected', 'physical_success': 'unknown'}
    x, y = objects['target_1']['pose'][:2]
    preferred = 'left' if x <= 0 else 'right'
    alternate = 'right' if preferred == 'left' else 'left'
    for arm in [preferred, alternate]:
        status = move(arm, [x, y, 1.02])
        if status == 'rejected':
            continue
        if status == 'uncertain':
            return {'stop': 'approach_execution_uncertain', 'physical_success': 'unknown'}
        robot.gripper(arm=arm, command=1)
        status = move(arm, [x, y, 0.93])
        if status != 'issued':
            return {'stop': 'contact_' + status, 'physical_success': 'unknown'}
        robot.gripper(arm=arm, command=0)
        for height in [1.12, 1.06]:
            status = move(arm, [x, y, height])
            if status == 'rejected':
                continue
            if status == 'uncertain':
                return {'stop': 'lift_execution_uncertain', 'physical_success': 'unknown'}
            return {'stop': 'sequence_issued', 'physical_success': 'unknown'}
        return {'stop': 'lift_plans_rejected', 'physical_success': 'unknown'}
    return {'stop': 'approach_plans_rejected', 'physical_success': 'unknown'}
