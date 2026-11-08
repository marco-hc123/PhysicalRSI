def policy(robot, memory):
    def normalize(q):
        n = sum(v*v for v in q) ** 0.5
        return [v/n for v in q] if n > 0.000001 else None

    quats = {
        'left': normalize([0.613, -0.3593, 0.6163, 0.3392]),
        'right': normalize([0.3814, -0.6197, 0.3785, 0.572])
    }

    def observe():
        data = robot.scene()
        if not isinstance(data, dict) or not isinstance(data.get('objects'), dict):
            raise RuntimeError('Perception unavailable')
        result = []
        for key, obj in list(data['objects'].items())[:64]:
            if not isinstance(key, str) or '_' not in key or not isinstance(obj, dict):
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
            result.append({'category': category, 'p': list(p), 'd': list(d)})
        return result

    def inside(item, basket):
        p, b, d = item['p'], basket['p'], basket['d']
        q = normalize(b[3:7])
        if q is None:
            return False
        w, x, y, z = q
        dx, dy = p[0]-b[0], p[1]-b[1]
        lx = (1-2*(y*y+z*z))*dx + 2*(x*y+w*z)*dy
        ly = 2*(x*y-w*z)*dx + (1-2*(x*x+z*z))*dy
        return abs(lx) < d[0]/2-0.008 and abs(ly) < d[1]/2-0.008 and abs(p[2]-b[2]) < d[2]/2 + item['d'][2]/2 + 0.025

    def move(arm, x, y, z):
        result = robot.approach(arm=arm, position_m=[x, y, z], quaternion_wxyz=quats[arm])
        if isinstance(result, dict) and result.get('primitive_error'):
            raise RuntimeError('Planning unavailable')

    def grip(arm, command):
        result = robot.gripper(arm=arm, command=command)
        if isinstance(result, dict) and result.get('primitive_error'):
            raise RuntimeError('Gripper unavailable')

    try:
        initial = observe()
        baskets = sorted([o for o in initial if o['category'] == 'basket'], key=lambda o: (o['p'][0], o['p'][1]))
        items = [o for o in initial if o['category'] != 'basket']
        categories = sorted(set(o['category'] for o in items))
        if not categories or len(categories) > len(baskets):
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
            options = []
            for category in pending:
                group = [o for o in items if o['category'] == category]
                for i, basket in enumerate(baskets):
                    if i not in used:
                        cost = sum((o['p'][0]-basket['p'][0])**2 + (o['p'][1]-basket['p'][1])**2 for o in group)/len(group)
                        options.append((cost, category, i))
            if not options:
                return
            _, category, i = min(options)
            assignments[category] = i
            used.add(i)
            pending.remove(category)

        attempted = []
        for turn in range(min(10, len(items))):
            current = initial if turn == 0 else observe()
            choices = []
            for item in current:
                category = item['category']
                if category not in assignments:
                    continue
                x, y, z = item['p'][:3]
                if any(category == c and (x-ax)**2 + (y-ay)**2 < 0.035**2 for c, ax, ay in attempted):
                    continue
                basket = baskets[assignments[category]]
                if inside(item, basket):
                    continue
                cost = (x-basket['p'][0])**2 + (y-basket['p'][1])**2
                choices.append((cost, item, basket))
            if not choices:
                return
            choices.sort(key=lambda entry: entry[0])
            _, item, basket = choices[0]
            x, y, z = item['p'][:3]
            bx, by = basket['p'][:2]
            attempted.append((item['category'], x, y))
            arm = 'left' if x + bx < 0 else 'right'
            # Target the object's center rather than placing the contact at its top surface.
            contact_z = max(0.92, z + 0.125)
            clearance_z = max(1.01, contact_z + 0.045)
            if clearance_z > 1.08:
                return
            grip(arm, 1)
            move(arm, x, y, contact_z)
            grip(arm, 0)
            move(arm, x, y, clearance_z)
            # RGB visibility after closing is not a reliable grasp-success test.
            # Execute the single planned transfer without another grasp attempt.
            move(arm, bx, by, 1.01)
            grip(arm, 1)
            move(arm, bx, by, 1.06)
    except Exception:
        # Do not retry or release at an arbitrary location after an uncertain operation.
        return
