def policy(robot, memory):
    def normalized(q):
        n = sum(v*v for v in q) ** 0.5
        return [v/n for v in q]

    quats = {
        'left': normalized([0.613, -0.3593, 0.6163, 0.3392]),
        'right': normalized([0.3814, -0.6197, 0.3785, 0.572])
    }

    def observe():
        data = robot.scene()
        if not isinstance(data, dict) or not isinstance(data.get('objects'), dict):
            raise ValueError('Perception unavailable')
        result = []
        for key, value in list(data['objects'].items())[:64]:
            if not isinstance(key, str) or '_' not in key or not isinstance(value, dict):
                continue
            category, suffix = key.rsplit('_', 1)
            if not category or not suffix.isdigit() or int(suffix) < 1:
                continue
            p, d = value.get('pose', []), value.get('dims', [])
            if not isinstance(p, (list, tuple)) or not isinstance(d, (list, tuple)):
                continue
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
        q = b[3:7]
        n = sum(v*v for v in q) ** 0.5
        if n < 0.000001:
            return False
        w, x, y, z = [v/n for v in q]
        dx, dy = p[0]-b[0], p[1]-b[1]
        lx = (1-2*(y*y+z*z))*dx + 2*(x*y+w*z)*dy
        ly = 2*(x*y-w*z)*dx + (1-2*(x*x+z*z))*dy
        return abs(lx) < d[0]/2-0.012 and abs(ly) < d[1]/2-0.012

    def move(arm, x, y, z):
        result = robot.approach(arm=arm, position_m=[x, y, z], quaternion_wxyz=quats[arm])
        if isinstance(result, dict) and result.get('primitive_error'):
            if result['primitive_error'] == 'no_collision_free_path':
                return False
            raise RuntimeError('Uncertain primitive outcome')
        return True

    try:
        initial = observe()
        baskets = sorted([o for o in initial if o['c'] == 'basket'], key=lambda o: o['p'][0])
        items = [o for o in initial if o['c'] != 'basket']
        categories = sorted(set(o['c'] for o in items))
        if not baskets or not categories or len(categories) > len(baskets):
            return

        assignment, used = {}, set()
        for i, basket in enumerate(baskets):
            occupants = set(o['c'] for o in items if inside(o, basket))
            if len(occupants) == 1:
                category = next(iter(occupants))
                if category not in assignment:
                    assignment[category] = i
                    used.add(i)
        for category in categories:
            if category in assignment:
                continue
            group = [o for o in items if o['c'] == category]
            available = [i for i in range(len(baskets)) if i not in used]
            i = min(available, key=lambda j: sum((o['p'][0]-baskets[j]['p'][0])**2 + (o['p'][1]-baskets[j]['p'][1])**2 for o in group))
            assignment[category] = i
            used.add(i)

        work = [o for o in items if not inside(o, baskets[assignment[o['c']]])]
        work.sort(key=lambda o: (o['p'][0]-baskets[assignment[o['c']]]['p'][0])**2 + (o['p'][1]-baskets[assignment[o['c']]]['p'][1])**2)
        for original in work[:6]:
            current = observe()
            matches = [o for o in current if o['c'] == original['c'] and (o['p'][0]-original['p'][0])**2 + (o['p'][1]-original['p'][1])**2 < 0.0025]
            if len(matches) != 1:
                continue
            item = matches[0]
            basket = baskets[assignment[item['c']]]
            if inside(item, basket):
                continue
            x, y, z = item['p'][:3]
            bx, by = basket['p'][:2]
            contact = max(0.92, z + item['d'][2]/2 + 0.125)
            clearance = max(1.01, contact + 0.045)
            if clearance > 1.08:
                continue
            preferred = 'left' if x + bx < 0 else 'right'
            other = 'right' if preferred == 'left' else 'left'
            selected = None
            # Only explicit zero-execution rejection permits this bounded fallback.
            for arm in [preferred, other]:
                robot.gripper(arm=arm, command=1)
                if not move(arm, x, y, clearance):
                    continue
                if not move(arm, x, y, contact):
                    return
                selected = arm
                break
            if selected is None:
                return
            robot.gripper(arm=selected, command=0)
            if not move(selected, x, y, clearance):
                return
            # RGB Z is nominal, not dynamic height: do not gate transport on it.
            # This is a single open-loop transfer, not a verified grasp.
            if not move(selected, bx, by, 1.01):
                return
            robot.gripper(arm=selected, command=1)
            if not move(selected, bx, by, 1.055):
                return
    except Exception:
        # No uncertain manipulation retries or arbitrary emergency releases.
        return
