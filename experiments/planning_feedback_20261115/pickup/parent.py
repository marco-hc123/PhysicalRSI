def policy(robot, memory):
    quats = {'left':[0.613,-0.3593,0.6163,0.3392], 'right':[0.3814,-0.6197,0.3785,0.572]}
    for arm in quats:
        norm = sum(v*v for v in quats[arm])**0.5
        quats[arm] = [v/norm for v in quats[arm]]
    def move(arm, position):
        value = robot.approach(arm=arm,position_m=position,quaternion_wxyz=quats[arm])
        return not value.get('primitive_error')
    objects = robot.scene()['objects']
    if 'target_1' not in objects:
        return {'stop':'target_not_detected'}
    x,y,z = objects['target_1']['pose'][:3]
    preferred = 'left' if x<=0 else 'right'
    for arm in [preferred, 'right' if preferred=='left' else 'left']:
        if not move(arm,[x,y,1.02]):
            continue
        robot.gripper(arm=arm,command=1)
        if not move(arm,[x,y,.93]):
            return {'stop':'contact_plan_rejected'}
        robot.gripper(arm=arm,command=0)
        if not move(arm,[x,y,1.06]):
            return {'stop':'lift_plan_rejected'}
        return {'stop':'program_complete','physical_success':'unknown'}
    return {'stop':'approach_plans_rejected'}
