def policy(robot, memory):
    def category(key):
        if not isinstance(key, str) or '_' not in key:
            return None
        name, suffix = key.rsplit('_', 1)
        if not name or not suffix.isdigit() or int(suffix) < 1:
            return None
        return name

    def decode(raw):
        result = []
        if not isinstance(raw, dict):
            return result
        objects = raw.get('objects', {})
        if not isinstance(objects, dict):
            return result
        for key, value in objects.items():
            name = category(key)
            if name is None or not isinstance(value, dict):
                continue
            pose = value.get('pose', [])
            dims = value.get('dims', [])
            if not isinstance(pose, (list, tuple)) or len(pose) < 3:
                continue
            xyz = pose[:3]
            if not all(isinstance(v, (int, float)) and v == v and abs(v) < 10 for v in xyz):
                continue
            if not isinstance(dims, (list, tuple)) or len(dims) < 3:
                dims = [0.05, 0.05, 0.05]
            if not all(isinstance(v, (int, float)) and v == v and 0 < v < 2 for v in dims[:3]):
                continue
            result.append({'key': key, 'category': name, 'p': list(xyz), 'dims': list(dims[:3])})
        return result

    def distance2(a, b):
        return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2

    try:
        initial = decode(robot.scene())
    except Exception:
        return
    baskets = sorted([o for o in initial if o['category'] == 'basket'], key=lambda o: (o['p'][0], o['p'][1]))
    if not baskets:
        return

    def in_basket(p, basket):
        b = basket['p']
        d = basket['dims']
        return abs(p[0] - b[0]) <= max(0.065, d[0] / 2) and abs(p[1] - b[1]) <= max(0.065, d[1] / 2)

    groups = {}
    for obj in initial:
        if obj['category'] != 'basket':
            groups.setdefault(obj['category'], []).append(obj)
    if not groups or len(groups) > len(baskets):
        return

    # Preserve unambiguous existing sorting before assigning unused baskets.
    assignment = {}
    used = set()
    for index, basket in enumerate(baskets):
        occupants = set(o['category'] for o in initial if o['category'] != 'basket' and in_basket(o['p'], basket))
        if len(occupants) > 1:
            return
        if occupants:
            name = next(iter(occupants))
            if name in assignment:
                return
            assignment[name] = index
            used.add(index)
    remaining = sorted([name for name in groups if name not in assignment], key=lambda name: (-len(groups[name]), name))
    for name in remaining:
        choices = [i for i in range(len(baskets)) if i not in used]
        index = min(choices, key=lambda i: sum(distance2(o['p'], baskets[i]['p']) for o in groups[name]))
        assignment[name] = index
        used.add(index)

    quaternions = {'left': [0.613, -0.3593, 0.6163, 0.3392], 'right': [0.3814, -0.6197, 0.3785, 0.572]}
    for arm in quaternions:
        q = quaternions[arm]
        length = sum(v * v for v in q) ** 0.5
        quaternions[arm] = [v / length for v in q]

    targets = []
    for name in sorted(groups):
        basket = baskets[assignment[name]]
        for obj in groups[name]:
            if not in_basket(obj['p'], basket):
                targets.append((obj, basket))
    # Bound work explicitly; never retry an uncertain grasp or placement.
    for original, basket in targets[:16]:
        try:
            observed = decode(robot.scene())
        except Exception:
            return
        candidates = [o for o in observed if o['category'] == original['category'] and not any(in_basket(o['p'], b) for b in baskets)]
        if not candidates:
            continue
        obj = min(candidates, key=lambda o: distance2(o['p'], original['p']))
        if distance2(obj['p'], original['p']) > 0.08 ** 2:
            continue
        p = obj['p']
        contact_z = max(0.92, p[2] + 0.125)
        if contact_z > 1.10:
            continue
        destination = basket['p']
        arm = 'left' if (p[1] + destination[1]) >= 0 else 'right'
        q = quaternions[arm]
        clearance = max(1.14, contact_z + 0.12)
        try:
            robot.gripper(arm=arm, command=1)
            robot.approach(arm=arm, position_m=[p[0], p[1], clearance], quaternion_wxyz=q)
            robot.approach(arm=arm, position_m=[p[0], p[1], contact_z], quaternion_wxyz=q)
        except Exception:
            # Nothing was intentionally grasped; skip this target.
            continue
        try:
            robot.gripper(arm=arm, command=0)
            robot.approach(arm=arm, position_m=[p[0], p[1], clearance], quaternion_wxyz=q)
            robot.approach(arm=arm, position_m=[destination[0], destination[1], clearance], quaternion_wxyz=q)
            robot.approach(arm=arm, position_m=[destination[0], destination[1], 1.01], quaternion_wxyz=q)
            robot.gripper(arm=arm, command=1)
            robot.approach(arm=arm, position_m=[destination[0], destination[1], clearance], quaternion_wxyz=q)
        except Exception:
            # A closed gripper or interrupted transfer has uncertain state.
            return
