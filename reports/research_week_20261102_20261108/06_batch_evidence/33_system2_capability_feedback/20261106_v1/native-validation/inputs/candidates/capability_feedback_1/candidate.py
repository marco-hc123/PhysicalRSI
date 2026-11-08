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
            if not isinstance(p, (list, tuple)) or not isinstance(d, (list, tuple)):
                continue
            if len(p) != 7 or len(d) != 3:
                continue
            values = list(p) + list(d)
            if not all(isinstance(v, (int, float)) and v == v and abs(v) < 10 for v in values):
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
        return abs(lx) < max(0, d[0]/2-0.012) and abs(ly) < max(0, d[1]/2-0.012)

    def approach(arm, position):
        result = robot.approach(arm=arm, position_m=position, quaternion_wxyz=quats[arm])
        if isinstance(result, dict) and result.get('primitive_error'):
            if result['primitive_error'] == 'no_collision_free_path':
                return False
            raise RuntimeError('Uncertain primitive result')
        return True

    try:
        initial = scene()
        baskets = sorted([o for o in initial if o['c'] == 'basket'], key=lambda o: (o['p'][0], o['p'][1]))
        items = [o for o in initial if o['c'] != 'basket']
        categories = sorted(set(o['c'] for o in items))
        if not categories or len(categories) > len(baskets):
            return

        assignments, used = {}, set()
        # Keep existing unmixed groupings when they are unambiguous.
        for i, basket in enumerate(baskets):
            occupants = set(o['c'] for o in items if inside(o, basket))
            if len(occupants) == 1:
                category = sorted(occupants)[0]
                if category not in assignments:
                    assignments[category] = i
                    used.add(i)
        pending = [c for c in categories if c not in assignments]
        for unused in range(len(pending)):
            options = []
            for category in pending:
                group = [o for o in items if o['c'] == category]
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

        # Freeze a spatial work list, not detector instance identities.
        jobs = []
        for item in items:
            basket = baskets[assignments[item['c']]]
            if not inside(item, basket):
                cost = (item['p'][0]-basket['p'][0])**2 + (item['p'][1]-basket['p'][1])**2
                jobs.append((cost, item, basket))
        jobs.sort(key=lambda entry: entry[0])

        for _, original, target in jobs[:8]:
            current = scene()
            matches = []
            for obj in current:
                if obj['c'] == original['c']:
                    distance = (obj['p'][0]-original['p'][0])**2 + (obj['p'][1]-original['p'][1])**2
                    if distance < 0.045**2:
                        matches.append((distance, obj))
            if not matches:
                continue
            matches.sort(key=lambda entry: entry[0])
            if len(matches) > 1 and matches[1][0]-matches[0][0] < 0.0001:
                continue
            item = matches[0][1]
            visible_baskets = [o for o in current if o['c'] == 'basket']
            near = [o for o in visible_baskets if (o['p'][0]-target['p'][0])**2 + (o['p'][1]-target['p'][1])**2 < 0.04**2]
            if len(near) != 1:
                return
            basket = near[0]
            if inside(item, basket):
                continue
            x, y, z = item['p'][:3]
            bx, by = basket['p'][:2]
            # Nominal object center is used as the contact target, not as measured lift height.
            contact = max(0.92, z + 0.125)
            clearance = max(1.01, contact + 0.055)
            if clearance > 1.08:
                continue
            preferred = 'left' if x + bx < 0 else 'right'
            alternatives = [preferred, 'right' if preferred == 'left' else 'left']
            selected = None
            # Exactly two pre-contact arm choices. Only explicit zero-execution
            # planning rejection permits this fallback; exceptions stop the policy.
            for arm in alternatives:
                robot.gripper(arm=arm, command=1)
                if not approach(arm, [x, y, clearance]):
                    continue
                if not approach(arm, [x, y, contact]):
                    return
                selected = arm
                break
            if selected is None:
                return
            arm = selected
            robot.gripper(arm=arm, command=0)
            if not approach(arm, [x, y, clearance]):
                return
            # No RGB-height, disappearance, suffix, or gripper-joint grasp test.
            # Execute the single planned transfer without retrying the grasp.
            if not approach(arm, [bx, by, 1.01]):
                return
            robot.gripper(arm=arm, command=1)
            if not approach(arm, [bx, by, 1.06]):
                return
    except Exception:
        # Preserve the current gripper command if execution becomes uncertain.
        return
