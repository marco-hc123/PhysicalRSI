def policy(robot, memory):
    try:
        scene_data = robot.scene()
    except Exception:
        return

    objects = scene_data.get('objects', {})
    if not objects:
        return

    baskets = {}
    categories = {}

    for key, info in objects.items():
        last_underscore = key.rfind('_')
        if last_underscore == -1:
            continue
        category = key[:last_underscore]

        if category == 'basket':
            baskets[key] = info
        else:
            if category not in categories:
                categories[category] = []
            categories[category].append(info)

    if not baskets or not categories:
        return

    basket_list = sorted(baskets.keys())
    category_list = sorted(categories.keys())

    assignment = {}
    for i, cat in enumerate(category_list):
        if i < len(basket_list):
            assignment[cat] = basket_list[i]

    right_quat = [0.3814, -0.6197, 0.3785, 0.572]

    for cat, basket_key in assignment.items():
        bp = baskets[basket_key]['pose']
        bx, by = bp[0], bp[1]

        for obj_info in categories[cat]:
            op = obj_info['pose']
            ox, oy, oz = op[0], op[1], op[2]

            pre_z = oz + 0.2
            if pre_z < 1.05:
                pre_z = 1.05

            gz = oz + 0.125
            if gz < 0.92:
                gz = 0.92

            try:
                robot.gripper(arm="right", command=1)
                robot.approach(arm="right", position_m=[ox, oy, pre_z], quaternion_wxyz=right_quat)
                robot.approach(arm="right", position_m=[ox, oy, gz], quaternion_wxyz=right_quat)
                robot.gripper(arm="right", command=0)
                robot.approach(arm="right", position_m=[ox, oy, pre_z], quaternion_wxyz=right_quat)
                robot.approach(arm="right", position_m=[bx, by, 1.01], quaternion_wxyz=right_quat)
                robot.gripper(arm="right", command=1)
            except Exception:
                continue

    return