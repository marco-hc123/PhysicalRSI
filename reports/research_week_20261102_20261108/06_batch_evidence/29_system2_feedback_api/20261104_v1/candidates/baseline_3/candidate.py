def policy(robot, memory):
    # All environmental information comes from the supplied RGB scene RPC.
    def read_scene():
        result = robot.scene()
        if not isinstance(result, dict):
            return None
        raw = result.get('objects')
        if not isinstance(raw, dict):
            return None
        parsed = []
        for key, value in raw.items():
            if not isinstance(key, str) or not isinstance(value, dict):
                continue
            parts = key.rsplit('_', 1)
            if len(parts) != 2 or not parts[1].isdigit():
                continue
            if int(parts[1]) < 1:
                continue
            pose = value.get('pose', [])
            dims = value.get('dims', [])
            if len(pose) < 3 or len(dims) < 3:
                continue
            if not all(isinstance(v, (int, float)) for v in list(pose[:3]) + list(dims[:3])):
                continue
            if not all(-3.0 < v < 3.0 for v in pose[:3]):
                continue
            if not all(0.0 < v < 1.5 for v in dims[:3]):
                continue
            parsed.append({'category': parts[0], 'p': list(pose[:3]), 'd': list(dims[:3])})
        return parsed

    def distance2(a, b):
        return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2

    def inside_basket(obj, baskets):
        for basket in baskets:
            if (abs(obj['p'][0] - basket['p'][0]) < basket['d'][0] * 0.5 + 0.015 and
                    abs(obj['p'][1] - basket['p'][1]) < basket['d'][1] * 0.5 + 0.015):
                return True
        return False

    try:
        scene = read_scene()
        if scene is None:
            return
        baskets = [o for o in scene if o['category'] == 'basket']
        objects = [o for o in scene if o['category'] != 'basket']
        if not baskets or not objects:
            return
        groups = {}
        for obj in objects:
            groups.setdefault(obj['category'], []).append(obj)
        if len(groups) > len(baskets):
            return

        # Existing unambiguous basket contents anchor the category assignment.
        assignment = {}
        used = []
        for index, basket in enumerate(baskets):
            contents = [o for o in objects if inside_basket(o, [basket])]
            categories = set(o['category'] for o in contents)
            if len(categories) > 1:
                return
            if len(categories) == 1:
                category = contents[0]['category']
                if category in assignment:
                    return
                assignment[category] = basket
                used.append(index)
        categories = sorted(groups, key=lambda c: (-len(groups[c]), c))
        for category in categories:
            if category in assignment:
                continue
            available = [i for i in range(len(baskets)) if i not in used]
            if not available:
                return
            chosen = min(available, key=lambda i: sum(distance2(o['p'], baskets[i]['p']) for o in groups[category]))
            assignment[category] = baskets[chosen]
            used.append(chosen)

        targets = [o for c in categories for o in groups[c] if not inside_basket(o, baskets)]
        if len(targets) > 24:
            return
        quaternions = {
            'left': [0.613, -0.3593, 0.6163, 0.3392],
            'right': [0.3814, -0.6197, 0.3785, 0.572]
        }
        for arm in quaternions:
            norm = sum(v * v for v in quaternions[arm]) ** 0.5
            quaternions[arm] = [v / norm for v in quaternions[arm]]

        for original in targets:
            fresh = read_scene()
            if fresh is None:
                return
            fresh_baskets = [o for o in fresh if o['category'] == 'basket']
            if not fresh_baskets:
                return
            candidates = [o for o in fresh if o['category'] == original['category'] and not inside_basket(o, fresh_baskets)]
            if not candidates:
                continue
            obj = min(candidates, key=lambda o: distance2(o['p'], original['p']))
            # Names are not persistent tracking IDs: match by category and proximity.
            if distance2(obj['p'], original['p']) > 0.08 ** 2:
                continue
            destination = assignment[original['category']]
            basket = min(fresh_baskets, key=lambda b: distance2(b['p'], destination['p']))
            if distance2(basket['p'], destination['p']) > 0.08 ** 2:
                return
            x, y, z = obj['p']
            bx, by, bz = basket['p']
            arm = 'left' if y + by >= 0.0 else 'right'
            quaternion = quaternions[arm]
            contact_z = max(0.92, z + 0.125)
            clearance = max(1.14, contact_z + 0.14, bz + basket['d'][2] * 0.5 + 0.18)
            if clearance > 1.5 or contact_z >= clearance:
                return

            robot.gripper(arm=arm, command=1)
            robot.approach(arm=arm, position_m=[x, y, clearance], quaternion_wxyz=quaternion)
            robot.approach(arm=arm, position_m=[x, y, contact_z], quaternion_wxyz=quaternion)
            robot.gripper(arm=arm, command=0)
            robot.approach(arm=arm, position_m=[x, y, clearance], quaternion_wxyz=quaternion)
            robot.approach(arm=arm, position_m=[bx, by, clearance], quaternion_wxyz=quaternion)
            robot.approach(arm=arm, position_m=[bx, by, 1.01], quaternion_wxyz=quaternion)
            robot.gripper(arm=arm, command=1)
            robot.approach(arm=arm, position_m=[bx, by, clearance], quaternion_wxyz=quaternion)
    except Exception:
        # No blind retries after uncertain planning, grasping, or transport.
        return
