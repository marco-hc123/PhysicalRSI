def policy(robot, memory):
    # All geometry comes from the public RGB scene primitive.
    def observe():
        try:
            result = robot.scene()
            objects = result.get('objects', {})
            clean = []
            for key, value in objects.items():
                if not isinstance(key, str) or '_' not in key:
                    continue
                category, suffix = key.rsplit('_', 1)
                if not category or not suffix.isdigit() or int(suffix) < 1:
                    continue
                pose = value.get('pose', [])
                dims = value.get('dims', [])
                if len(pose) < 3 or len(dims) < 3:
                    continue
                xyz = [float(pose[i]) for i in range(3)]
                size = [float(dims[i]) for i in range(3)]
                if not all(v == v and abs(v) < 10 for v in xyz):
                    continue
                if not all(v == v and 0 < v < 3 for v in size):
                    continue
                clean.append({'key': key, 'category': category,
                              'p': xyz, 'd': size})
            return clean
        except Exception:
            return None

    def distance(a, b):
        return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2

    def inside_basket(obj, baskets):
        for basket in baskets:
            if (abs(obj['p'][0] - basket['p'][0]) <= basket['d'][0] * 0.5
                    and abs(obj['p'][1] - basket['p'][1]) <= basket['d'][1] * 0.5):
                return True
        return False

    quaternions = {'left': [0.613, -0.3593, 0.6163, 0.3392],
                   'right': [0.3814, -0.6197, 0.3785, 0.572]}
    for arm in quaternions:
        q = quaternions[arm]
        norm = sum(v * v for v in q) ** 0.5
        quaternions[arm] = [v / norm for v in q]

    def move(arm, x, y, z):
        robot.approach(arm=arm, position_m=[x, y, z],
                       quaternion_wxyz=quaternions[arm])

    scene = observe()
    if scene is None:
        return
    baskets = sorted([o for o in scene if o['category'] == 'basket'],
                     key=lambda o: (o['p'][1], o['p'][0]))
    targets = [o for o in scene if o['category'] != 'basket'
               and not inside_basket(o, baskets)]
    categories = sorted(set(o['category'] for o in targets))
    if not targets or len(categories) > len(baskets):
        return

    # Assign distinct baskets using observed category centroids, not instance IDs.
    centers = {}
    for category in categories:
        members = [o for o in targets if o['category'] == category]
        centers[category] = [sum(o['p'][i] for o in members) / len(members)
                             for i in range(2)]
    assignment = {}
    available = list(baskets)
    remaining = list(categories)
    for _ in range(len(categories)):
        choices = [(distance(centers[c], b['p']), c, index)
                   for c in remaining for index, b in enumerate(available)]
        if not choices:
            return
        _, category, index = min(choices)
        assignment[category] = available.pop(index)
        remaining.remove(category)

    # Each initial detection receives at most one manipulation attempt.
    targets.sort(key=lambda o: (o['category'], o['p'][1], o['p'][0]))
    placed = {c: 0 for c in categories}
    used_locations = []
    for original in targets:
        fresh = observe()
        if fresh is None:
            return
        fresh_baskets = [o for o in fresh if o['category'] == 'basket']
        basket = assignment[original['category']]
        nearby_baskets = [b for b in fresh_baskets
                          if distance(b['p'], basket['p']) < 0.04]
        if not nearby_baskets:
            return
        basket = min(nearby_baskets, key=lambda b: distance(b['p'], basket['p']))
        candidates = [o for o in fresh
                      if o['category'] == original['category']
                      and not inside_basket(o, fresh_baskets)
                      and distance(o['p'], original['p']) < 0.0064
                      and not any(c == o['category'] and distance(o['p'], p) < 0.0004
                                  for c, p in used_locations)]
        if not candidates:
            continue
        obj = min(candidates, key=lambda o: distance(o['p'], original['p']))
        x, y, z = obj['p']
        bx, by, bz = basket['p']
        # Select the arm on the same side as the transport midpoint.
        arm = 'left' if y + by >= 0 else 'right'
        grasp_z = max(0.92, z + 0.125)
        clearance = max(1.14, grasp_z + 0.14, bz + basket['d'][2] * 0.5 + 0.16)
        if clearance > 1.45 or grasp_z > 1.15:
            continue
        count = placed[obj['category']]
        # Small, interior offsets reduce repeated releases onto one point.
        offsets = [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]
        ox, oy = offsets[count % len(offsets)]
        dx = min(0.025, max(0.0, (basket['d'][0] - obj['d'][0]) * 0.15))
        dy = min(0.025, max(0.0, (basket['d'][1] - obj['d'][1]) * 0.15))
        rx, ry = bx + ox * dx, by + oy * dy
        try:
            robot.gripper(arm=arm, command=1)
            move(arm, x, y, clearance)
            move(arm, x, y, grasp_z)
        except Exception:
            # No grasp was commanded; do not repeatedly probe an unavailable path.
            return
        try:
            robot.gripper(arm=arm, command=0)
            move(arm, x, y, clearance)
            move(arm, rx, ry, clearance)
            move(arm, rx, ry, 1.01)
            robot.gripper(arm=arm, command=1)
            move(arm, rx, ry, clearance)
        except Exception:
            # A closed gripper is not evidence of a grasp. Stop on uncertainty.
            return
        used_locations.append((obj['category'], list(obj['p'])))
        placed[obj['category']] += 1
