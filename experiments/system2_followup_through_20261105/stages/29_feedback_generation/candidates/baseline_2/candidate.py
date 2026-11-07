def policy(robot, memory):
    def read_scene():
        data = robot.scene()
        objects = data.get('objects')
        if not isinstance(objects, dict):
            return None
        result = []
        for key, value in objects.items():
            if not isinstance(key, str) or not isinstance(value, dict):
                continue
            parts = key.rsplit('_', 1)
            if len(parts) != 2 or not parts[1].isdigit() or int(parts[1]) < 1:
                continue
            pose = value.get('pose', [])
            dims = value.get('dims', [])
            if len(pose) < 3 or len(dims) < 3:
                continue
            try:
                p = [float(pose[i]) for i in range(3)]
                d = [float(dims[i]) for i in range(3)]
            except (TypeError, ValueError):
                continue
            if not all(-3.0 < v < 3.0 for v in p):
                continue
            if not all(0.0 < v < 1.5 for v in d):
                continue
            result.append({'category': parts[0], 'p': p, 'd': d})
        return result

    def distance2(a, b):
        return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2

    def inside(item, basket):
        return (abs(item['p'][0] - basket['p'][0]) < basket['d'][0] * 0.5
                and abs(item['p'][1] - basket['p'][1]) < basket['d'][1] * 0.5)

    try:
        initial = read_scene()
    except Exception:
        return
    if not initial:
        return
    baskets = [o for o in initial if o['category'] == 'basket']
    items = [o for o in initial if o['category'] != 'basket']
    groups = {}
    for item in items:
        groups.setdefault(item['category'], []).append(item)
    if not baskets or len(groups) > len(baskets):
        return

    # Assign distinct baskets from observed geometry, preserving any existing
    # unambiguous same-category grouping before considering travel distance.
    assigned = {}
    unused = list(range(len(baskets)))
    categories = sorted(groups, key=lambda c: (-len(groups[c]), c))
    for category in categories:
        group = groups[category]
        def cost(index):
            basket = baskets[index]
            own = sum(1 for item in group if inside(item, basket))
            foreign = sum(1 for item in items
                          if item['category'] != category and inside(item, basket))
            travel = sum(distance2(item['p'], basket['p']) for item in group)
            return (foreign, -own, travel)
        chosen = min(unused, key=cost)
        assigned[category] = baskets[chosen]
        unused.remove(chosen)

    quaternions = {
        'left': [0.613, -0.3593, 0.6163, 0.3392],
        'right': [0.3814, -0.6197, 0.3785, 0.572]
    }
    for arm in quaternions:
        q = quaternions[arm]
        norm = sum(v * v for v in q) ** 0.5
        quaternions[arm] = [v / norm for v in q]

    # Fixed finite worklist: never rediscover and repeatedly manipulate an
    # object merely because the RGB adapter gives it a new instance suffix.
    work = []
    for category in categories:
        basket = assigned[category]
        for item in sorted(groups[category], key=lambda o: distance2(o['p'], basket['p'])):
            if not inside(item, basket):
                work.append((category, item['p'], basket))
    deposited = {category: 0 for category in categories}

    for category, original_position, basket in work:
        try:
            current = read_scene()
        except Exception:
            return
        if current is None:
            return
        candidates = [o for o in current
                      if o['category'] == category
                      and not inside(o, basket)
                      and distance2(o['p'], original_position) < 0.12 ** 2]
        if not candidates:
            continue
        item = min(candidates, key=lambda o: distance2(o['p'], original_position))
        x, y, z = item['p']
        bx, by, bz = basket['p']
        arm = 'left' if (y + by) >= 0.0 else 'right'
        q = quaternions[arm]
        contact_z = max(0.92, z + 0.125)
        clearance_z = max(1.14, contact_z + 0.10)
        if clearance_z > 1.45:
            return

        # Small interior offsets reduce stacking without approaching walls.
        slot = deposited[category] % 4
        dx = min(0.025, basket['d'][0] * 0.12)
        dy = min(0.025, basket['d'][1] * 0.12)
        drop_x = bx + (dx if slot % 2 else -dx)
        drop_y = by + (dy if slot // 2 else -dy)
        try:
            robot.gripper(arm=arm, command=1)
            robot.approach(arm=arm, position_m=[x, y, clearance_z], quaternion_wxyz=q)
            robot.approach(arm=arm, position_m=[x, y, contact_z], quaternion_wxyz=q)
            robot.gripper(arm=arm, command=0)
            robot.approach(arm=arm, position_m=[x, y, clearance_z], quaternion_wxyz=q)
            robot.approach(arm=arm, position_m=[drop_x, drop_y, clearance_z], quaternion_wxyz=q)
            robot.approach(arm=arm, position_m=[drop_x, drop_y, 1.01], quaternion_wxyz=q)
            robot.gripper(arm=arm, command=1)
            robot.approach(arm=arm, position_m=[drop_x, drop_y, clearance_z], quaternion_wxyz=q)
        except Exception:
            # Planning or manipulation uncertainty is not evidence of a grasp;
            # do not issue a second speculative manipulation attempt.
            return
        deposited[category] += 1
