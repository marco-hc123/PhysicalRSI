def policy(robot, memory):
    def read_scene():
        data = robot.scene()
        result = []
        for key, obj in list(data.get('objects', {}).items())[:64]:
            if not isinstance(key, str) or '_' not in key:
                continue
            category, suffix = key.rsplit('_', 1)
            if not category or not suffix.isdigit() or int(suffix) < 1:
                continue
            p = obj.get('pose', [])
            d = obj.get('dims', [])
            if len(p) != 7 or len(d) != 3:
                continue
            if not all(isinstance(v, (int, float)) and v == v and abs(v) < 10 for v in p + d):
                continue
            if not all(v > 0 for v in d):
                continue
            result.append({'category': category, 'p': p, 'd': d})
        return result

    def normalize(q):
        n = sum(v * v for v in q) ** 0.5
        return [v / n for v in q] if n > 0.000001 else None

    quats = {
        'left': normalize([0.613, -0.3593, 0.6163, 0.3392]),
        'right': normalize([0.3814, -0.6197, 0.3785, 0.572])
    }

    def inside(item, basket):
        p, b, d = item['p'], basket['p'], basket['d']
        q = normalize(b[3:7])
        if q is None:
            return False
        w, x, y, z = q
        dx, dy = p[0] - b[0], p[1] - b[1]
        lx = (1 - 2 * (y*y + z*z)) * dx + 2 * (x*y + w*z) * dy
        ly = 2 * (x*y - w*z) * dx + (1 - 2 * (x*x + z*z)) * dy
        return abs(lx) < d[0] * 0.5 - 0.008 and abs(ly) < d[1] * 0.5 - 0.008 and p[2] < 1.0

    def move(arm, x, y, z):
        result = robot.approach(arm=arm, position_m=[x, y, z], quaternion_wxyz=quats[arm])
        if isinstance(result, dict) and result.get('primitive_error'):
            raise RuntimeError('Planning unavailable')

    try:
        initial = read_scene()
        baskets = sorted([o for o in initial if o['category'] == 'basket'], key=lambda o: o['p'][0])
        items = [o for o in initial if o['category'] != 'basket']
        categories = sorted(set(o['category'] for o in items))
        if not baskets or not categories or len(categories) > len(baskets):
            return

        # Preserve unambiguous existing groupings before assigning empty baskets.
        assignments = {}
        used = set()
        for i, basket in enumerate(baskets):
            occupants = set(o['category'] for o in items if inside(o, basket))
            if len(occupants) == 1:
                category = next(iter(occupants))
                if category not in assignments:
                    assignments[category] = i
                    used.add(i)

        # Assignment depends only on the current visible category positions.
        pending = [c for c in categories if c not in assignments]
        for unused in range(len(pending)):
            best = None
            for category in pending:
                group = [o for o in items if o['category'] == category]
                for i, basket in enumerate(baskets):
                    if i in used:
                        continue
                    cost = sum((o['p'][0] - basket['p'][0])**2 + (o['p'][1] - basket['p'][1])**2 for o in group) / len(group)
                    candidate = (cost, category, i)
                    if best is None or candidate < best:
                        best = candidate
            if best is None:
                return
            _, category, i = best
            assignments[category] = i
            used.add(i)
            pending.remove(category)

        attempted = []
        for turn in range(min(12, len(items))):
            current = read_scene()
            choices = []
            for item in current:
                category = item['category']
                if category not in assignments:
                    continue
                p = item['p']
                if any(category == c and (p[0]-x)**2 + (p[1]-y)**2 < 0.0049 for c, x, y in attempted):
                    continue
                basket = baskets[assignments[category]]
                if inside(item, basket):
                    continue
                cost = (p[0]-basket['p'][0])**2 + (p[1]-basket['p'][1])**2
                choices.append((cost, item, basket))
            if not choices:
                return
            choices.sort(key=lambda entry: entry[0])
            _, item, basket = choices[0]
            category = item['category']
            x, y, z = item['p'][:3]
            attempted.append((category, x, y))
            bx, by = basket['p'][:2]
            arm = 'left' if x + bx < 0 else 'right'
            contact_z = max(0.92, z + item['d'][2] * 0.5 + 0.125)
            clearance_z = max(1.01, contact_z + 0.055)
            if clearance_z > 1.10:
                return

            # Planning failure before contact does not trigger another grasp attempt.
            robot.gripper(arm=arm, command=1)
            move(arm, x, y, clearance_z)
            move(arm, x, y, contact_z)
            robot.gripper(arm=arm, command=0)
            move(arm, x, y, clearance_z)

            # Joint settling is not grasp evidence. Require visible upward motion.
            lifted_scene = read_scene()
            lifted = [o for o in lifted_scene if o['category'] == category and o['p'][2] > z + 0.025]
            if len(lifted) != 1:
                return
            move(arm, bx, by, 1.01)
            robot.gripper(arm=arm, command=1)
            move(arm, bx, by, 1.07)
    except Exception:
        # Do not release a possibly held object at an arbitrary failure location.
        return
