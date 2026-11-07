def policy(robot, memory):
    def normalize_quat(q):
        norm = (q[0]**2 + q[1]**2 + q[2]**2 + q[3]**2) ** 0.5
        if norm < 1e-6:
            return [1.0, 0.0, 0.0, 0.0]
        return [q[0]/norm, q[1]/norm, q[2]/norm, q[3]/norm]

    left_quat = normalize_quat([0.613, -0.3593, 0.6163, 0.3392])

    try:
        scene_data = robot.scene()
    except Exception:
        return
    objects = scene_data.get("objects", {})

    baskets = {}
    categories = set()
    for key, obj_data in objects.items():
        last_underscore = key.rfind("_")
        category = key[:last_underscore]
        if category == "basket":
            baskets[key] = obj_data
        else:
            categories.add(category)

    if not baskets or not categories:
        return

    basket_list = sorted(baskets.keys())
    category_list = sorted(categories)

    basket_assignment = {}
    for i, cat in enumerate(category_list):
        basket_assignment[cat] = basket_list[i % len(basket_list)]

    failed_items = set()
    max_iterations = 100

    for iteration in range(max_iterations):
        try:
            scene_data = robot.scene()
        except Exception:
            break
        objects = scene_data.get("objects", {})

        item_to_move = None
        for key, obj_data in objects.items():
            if key in failed_items:
                continue
            last_underscore = key.rfind("_")
            category = key[:last_underscore]
            if category != "basket":
                item_x = obj_data["pose"][0]
                item_y = obj_data["pose"][1]

                in_basket = False
                for b_key, b_data in baskets.items():
                    b_pose = b_data["pose"]
                    b_x, b_y = b_pose[0], b_pose[1]
                    if abs(item_x - b_x) < b_data["dims"][0] / 2 and abs(item_y - b_y) < b_data["dims"][1] / 2:
                        in_basket = True
                        break

                if not in_basket:
                    item_to_move = (key, category, obj_data)
                    break

        if item_to_move is None:
            break

        key, category, obj_data = item_to_move
        item_pose = obj_data["pose"]
        item_x, item_y, item_z = item_pose[0], item_pose[1], item_pose[2]
        item_dims = obj_data.get("dims", [0.05, 0.05, 0.05])

        basket_key = basket_assignment[category]
        basket_pose = baskets[basket_key]["pose"]
        basket_x, basket_y = basket_pose[0], basket_pose[1]

        grasp_z = item_z + item_dims[2] / 2.0 + 0.125

        try:
            robot.approach(arm="left", position_m=[item_x, item_y, grasp_z],
                          quaternion_wxyz=left_quat)
        except RuntimeError:
            failed_items.add(key)
            continue

        robot.gripper(arm="left", command=0)

        try:
            robot.approach(arm="left", position_m=[item_x, item_y, grasp_z + 0.2],
                          quaternion_wxyz=left_quat)
        except RuntimeError:
            robot.gripper(arm="left", command=1)
            failed_items.add(key)
            continue

        try:
            robot.approach(arm="left", position_m=[basket_x, basket_y, 1.01],
                          quaternion_wxyz=left_quat)
        except RuntimeError:
            robot.gripper(arm="left", command=1)
            failed_items.add(key)
            continue

        robot.gripper(arm="left", command=1)

    memory["grasp_z_offset"] = 0.125
    memory["basket_release_z"] = 1.01
    memory["left_quat"] = [0.613, -0.3593, 0.6163, 0.3392]