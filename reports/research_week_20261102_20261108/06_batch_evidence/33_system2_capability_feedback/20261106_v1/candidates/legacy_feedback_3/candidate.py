def policy(robot, memory):
    def unit(q):
        n = sum(v*v for v in q) ** 0.5
        return [v/n for v in q] if n > 0.000001 else None

    quats = {
        'left': unit([0.613, -0.3593, 0.6163, 0.3392]),
        'right': unit([0.3814, -0.6197, 0.3785, 0.572])
    }

    def scene():
        data = robot.scene()
        result = []
        for key, obj in list(data.get('objects', {}).items())[:64]:
            if not isinstance(key, str) or '_' not in key:
                continue
            category, suffix = key.rsplit('_', 1)
            if not category or not suffix.isdigit() or int(suffix) < 1:
                continue
            p, d = obj.get('pose', []), obj.get('dims', [])
            if len(p) != 7 or len(d) != 3:
                continue
            if not all(isinstance(v, (int, float)) and v == v and abs(v) < 10 for v in list(p) + list(d)):
                continue
            if not all(v > 0 for v in d):
                continue
            result.append({'c': category, 'p': list(p), 'd': list(d)})
        return result

    def inside(item, basket):
        p, b, d = item['p'], basket['p'], basket['d']
        q = unit(b[3:7])
        if q is None:
            return False
        w, x, y, z = q
        dx, dy = p[0]-b[0], p[1]-b[1]
        lx = (1-2*(y*y+z*z))*dx + 2*(x*y+w*z)*dy
        ly = 2*(x*y-w*z)*dx + (1-2*(x*x+z*z))*dy
        return abs(lx) < d[0]/2-0.01 and abs(ly) < d[1]/2-0.01 and abs(p[2]-b[2]) < d[2]/2+item['d'][2]/2+0.025

    def move(arm, x, y, z):
        result = robot.approach(arm=arm, position_m=[x, y, z], quaternion_wxyz=quats[arm])
        if isinstance(result, dict) and result.get('primitive_error'):
            raise RuntimeError('Planning unavailable')

    def grip(arm, command):
        result = robot.gripper(arm=arm, command=command)
        if isinstance(result, dict) and result.get('primitive_error'):
            raise RuntimeError('Gripper unavailable')

    try:
        initial = scene()
        baskets = sorted([o for o in initial if o['c'] == 'basket'], key=lambda o: (o['p'][0], o['p'][1]))
        items = [o for o in initial if o['c'] != 'basket']
        categories = sorted(set(o['c'] for o in items))
        if not categories or len(categories) > len(baskets):
            return

        assignments, used = {}, set()
        for i, basket in enumerate(baskets):
            occupants = set(o['c'] for o in items if inside(o, basket))
            if len(occupants) == 1:
                category = next(iter(occupants))
                if category not in assignments:
                    assignments[category] = i
                    used.add(i)

        pending = [c for c in categories if c not in assignments]
        for _ in range(len(pending)):
            best = None
            for category in pending:
                group = [o for o in items if o['c'] == category]
                for i, basket in enumerate(baskets):
                    if i in used:
                        continue
                    cost = sum((o['p'][0]-basket['p'][0])**2 + (o['p'][1]-basket['p'][1])**2 for o in group)/len(group)
                    candidate = (cost, category, i)
                    if best is None or candidate < best:
                        best = candidate
            if best is None:
                return
            _, category, i = best
            assignments[category] = i
            used.add(i)
            pending.remove(category)

        queue = [o for o in items if not inside(o, baskets[assignments[o['c']]])]
        queue.sort(key=lambda o: (o['p'][0]-baskets[assignments[o['c']]]['p'][0])**2 + (o['p'][1]-baskets[assignments[o['c']]]['p'][1])**2)
        attempted = []
        for original in queue[:8]:
            current = scene()
            candidates = [o for o in current if o['c'] == original['c'] and (o['p'][0]-original['p'][0])**2 + (o['p'][1]-original['p'][1])**2 < 0.001225]
            if len(candidates) != 1:
                continue
            item = candidates[0]
            x, y, z = item['p'][:3]
            if any(c == item['c'] and (x-ax)**2 + (y-ay)**2 < 0.000625 for c, ax, ay in attempted):
                continue
            basket = baskets[assignments[item['c']]]
            if inside(item, basket):
                continue
            bx, by = basket['p'][:2]
            arm = 'left' if x+bx < 0 else 'right'
            contact = max(0.92, z+0.125)
            clearance = max(1.01, contact+0.045)
            if clearance > 1.08:
                return
            attempted.append((item['c'], x, y))
            grip(arm, 1)
            move(arm, x, y, clearance)
            move(arm, x, y, contact)
            grip(arm, 0)
            move(arm, x, y, clearance)
            # Complete this single transfer without interpreting RGB height as grasp proof.
            move(arm, bx, by, 1.01)
            grip(arm, 1)
            move(arm, bx, by, 1.06)
        return
    except Exception:
        # Stop on uncertainty; never retry a grasp or release at a failed waypoint.
        return
