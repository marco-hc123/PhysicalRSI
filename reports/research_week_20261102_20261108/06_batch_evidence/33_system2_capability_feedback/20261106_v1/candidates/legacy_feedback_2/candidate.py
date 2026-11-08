def policy(robot, memory):
    def normalize(q):
        n = sum(v * v for v in q) ** 0.5
        if n < 0.000001:
            return None
        return [v / n for v in q]

    quaternions = {
        'left': normalize([0.613, -0.3593, 0.6163, 0.3392]),
        'right': normalize([0.3814, -0.6197, 0.3785, 0.572])
    }

    def read_scene():
        result = []
        data = robot.scene()
        for key, obj in list(data.get('objects', {}).items())[:64]:
            if not isinstance(key, str) or '_' not in key:
                continue
            category, suffix = key.rsplit('_', 1)
            if not category or not suffix.isdigit() or int(suffix) < 1:
                continue
            p, d = obj.get('pose', []), obj.get('dims', [])
            if len(p) != 7 or len(d) != 3:
                continue
            values = list(p) + list(d)
            if not all(isinstance(v, (int, float)) and v == v and abs(v) < 10 for v in values):
                continue
            if not all(v > 0 for v in d):
                continue
            result.append({'category': category, 'p': list(p), 'd': list(d)})
        return result

    def inside(item, basket):
        p, b, d = item['p'], basket['p'], basket['d']
        q = normalize(b[3:7])
        if q is None:
            return False
        w, x, y, z = q
        dx, dy, dz = p[0] - b[0], p[1] - b[1], p[2] - b[2]
        lx = (1 - 2*(y*y + z*z))*dx + 2*(x*y + w*z)*dy + 2*(x*z - w*y)*dz
        ly = 2*(x*y - w*z)*dx + (1 - 2*(x*x + z*z))*dy + 2*(y*z + w*x)*dz
        return abs(lx) < d[0]/2 - 0.008 and abs(ly) < d[1]/2 - 0.008 and abs(dz) < d[2]/2 + item['d'][2]/2 + 0.025

    def move(arm, x, y, z):
        result = robot.approach(arm=arm, position_m=[x, y, z], quaternion_wxyz=quaternions[arm])
        if isinstance(result, dict) and result.get('primitive_error'):
            raise RuntimeError('Planning unavailable')

    def grip(arm, command):
        result = robot.gripper(arm=arm, command=command)
        if isinstance(result, dict) and result.get('primitive_error'):
            raise RuntimeError('Gripper unavailable')

    try:
        initial = read_scene()
        baskets = sorted([o for o in initial if o['category'] == 'basket'], key=lambda o: (o['p'][0], o['p'][1]))
        items = [o for o in initial if o['category'] != 'basket']
        categories = sorted(set(o['category'] for o in items))
        if not baskets or not categories or len(categories) > len(baskets):
            return

        assignments, used = {}, set()
        for i, basket in enumerate(baskets):
            occupants = set(o['category'] for o in items if inside(o, basket))
            if len(occupants) == 1:
                category = sorted(occupants)[0]
                if category not in assignments:
                    assignments[category] = i
                    used.add(i)

        pending = [c for c in categories if c not in assignments]
        for unused in range(len(pending)):
            best = None
            for category in pending:
                group = [o for o in items if o['category'] == category]
                for i, basket in enumerate(baskets):
                    if i in used:
                        continue
                    cost = sum((o['p'][0]-basket['p'][0])**2 + (o['p'][1]-basket['p'][1])**2 for o in group) / len(group)
                    candidate = (cost, category, i)
                    if best is None or candidate < best:
                        best = candidate
            if best is None:
                return
            cost, category, i = best
            assignments[category] = i
            used.add(i)
            pending.remove(category)

        # Each initial visible instance receives at most one manipulation attempt.
        jobs = []
        for item in items:
            basket = baskets[assignments[item['category']]]
            if not inside(item, basket):
                cost = (item['p'][0]-basket['p'][0])**2 + (item['p'][1]-basket['p'][1])**2
                jobs.append((cost, item, basket))
        jobs.sort(key=lambda entry: entry[0])
        opened = set()

        for turn, job in enumerate(jobs[:10]):
            cost, original, basket = job
            if turn == 0:
                item = original
            else:
                current = read_scene()
                matches = [o for o in current if o['category'] == original['category'] and (o['p'][0]-original['p'][0])**2 + (o['p'][1]-original['p'][1])**2 < 0.0025]
                if len(matches) != 1:
                    continue
                item = matches[0]
                if inside(item, basket):
                    continue

            x, y, z = item['p'][:3]
            bx, by = basket['p'][:2]
            arm = 'left' if x + bx < 0 else 'right'
            # Place the fingers around the object's centre, not above its top.
            contact_z = max(0.92, z + 0.125)
            clearance_z = max(1.01, contact_z + 0.06)
            if clearance_z > 1.08:
                return
            if arm not in opened:
                grip(arm, 1)
                opened.add(arm)
            move(arm, x, y, clearance_z)
            move(arm, x, y, contact_z)
            grip(arm, 0)
            move(arm, x, y, clearance_z)
            # Execute one transfer; neither joint settling nor RGB visibility
            # is treated as proof of grasp success.
            move(arm, bx, by, 1.01)
            grip(arm, 1)
    except Exception:
        # Stop without retrying or releasing at an arbitrary failure location.
        return
