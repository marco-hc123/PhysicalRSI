def policy(robot, memory):
    def normalize(q):
        n = sum(v*v for v in q) ** 0.5
        return [v/n for v in q] if n > 0.000001 else None

    quats = {
        'left': normalize([0.613, -0.3593, 0.6163, 0.3392]),
        'right': normalize([0.3814, -0.6197, 0.3785, 0.572])
    }

    def read_scene():
        data = robot.scene()
        result = []
        for key, obj in list(data.get('objects', {}).items())[:64]:
            if not isinstance(key, str) or '_' not in key or not isinstance(obj, dict):
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
        dx, dy = p[0]-b[0], p[1]-b[1]
        lx = (1-2*(y*y+z*z))*dx + 2*(x*y+w*z)*dy
        ly = 2*(x*y-w*z)*dx + (1-2*(x*x+z*z))*dy
        return abs(lx) < d[0]/2-0.012 and abs(ly) < d[1]/2-0.012

    def release_target(item, basket, arm, current, reservations):
        bx, by = basket['p'][:2]
        q = normalize(basket['p'][3:7])
        radius = 0.5*(item['d'][0]**2 + item['d'][1]**2)**0.5
        if q is None:
            return [bx, by, 1.01], radius
        w, x, y, z = q
        r00 = 1-2*(y*y+z*z)
        r01 = 2*(x*y-w*z)
        r10 = 2*(x*y+w*z)
        r11 = 1-2*(x*x+z*z)
        hx = max(0.0, basket['d'][0]/2-radius-0.012)
        hy = max(0.0, basket['d'][1]/2-radius-0.012)
        ox, oy = -0.0175, -0.035
        if abs(bx) < 0.1:
            ox = -0.065 if arm == 'left' else 0.065
            oy = -0.055
        base_x = max(-hx, min(hx, r00*ox+r10*oy))
        base_y = max(-hy, min(hy, r01*ox+r11*oy))
        candidates = [(base_x, base_y)]
        for lx in [-hx, 0.0, hx]:
            for ly in [-hy, 0.0, hy]:
                candidates.append((lx, ly))
        obstacles = []
        for other in current:
            if other['category'] != 'basket' and inside(other, basket):
                other_radius = 0.5*(other['d'][0]**2+other['d'][1]**2)**0.5
                obstacles.append((other['p'][0], other['p'][1], other_radius))
        for abx, aby, tx, ty, rr in reservations:
            if (abx-bx)**2+(aby-by)**2 < 0.0025:
                obstacles.append((tx, ty, rr))
        best = None
        best_score = None
        for lx, ly in candidates:
            tx = bx+r00*lx+r01*ly
            ty = by+r10*lx+r11*ly
            preference = (lx-base_x)**2+(ly-base_y)**2
            score = -0.01*preference
            if obstacles:
                clearance = min((tx-px)**2+(ty-py)**2-(radius+rr+0.012)**2 for px, py, rr in obstacles)
                score += clearance
            if best_score is None or score > best_score:
                best_score = score
                best = [tx, ty, 1.01]
        return best, radius

    def move(arm, position):
        result = robot.approach(arm=arm, position_m=position, quaternion_wxyz=quats[arm])
        if isinstance(result, dict) and result.get('primitive_error'):
            if result['primitive_error'] == 'no_collision_free_path':
                return False
            raise RuntimeError('Uncertain primitive execution')
        return True

    try:
        initial = read_scene()
        baskets = sorted([o for o in initial if o['category'] == 'basket'], key=lambda o: (o['p'][0], o['p'][1]))
        items = [o for o in initial if o['category'] != 'basket']
        categories = sorted(set(o['category'] for o in items))
        if not categories or len(categories) > len(baskets) or len(baskets) > 8:
            return

        assignments, used = {}, set()
        for i, basket in enumerate(baskets):
            occupants = sorted(set(o['category'] for o in items if inside(o, basket)))
            if len(occupants) == 1 and occupants[0] not in assignments:
                assignments[occupants[0]] = i
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
        reservations = []
        for turn in range(6):
            current = read_scene()
            visible_baskets = [o for o in current if o['category'] == 'basket']
            choices = []
            for item in current:
                category = item['category']
                if category not in assignments:
                    continue
                p = item['p']
                if any(category == c and (p[0]-x)**2+(p[1]-y)**2 < 0.0016 for c, x, y in attempted):
                    continue
                anchor = baskets[assignments[category]]
                matches = [b for b in visible_baskets if (b['p'][0]-anchor['p'][0])**2+(b['p'][1]-anchor['p'][1])**2 < 0.0025]
                if len(matches) != 1:
                    continue
                basket = matches[0]
                if inside(item, basket):
                    continue
                cost = (p[0]-basket['p'][0])**2+(p[1]-basket['p'][1])**2
                choices.append((cost, item, basket))
            if not choices:
                return
            choices.sort(key=lambda entry: entry[0])
            _, item, basket = choices[0]
            x, y, z = item['p'][:3]
            bx, by = basket['p'][:2]
            attempted.append((item['category'], x, y))
            contact_z = max(0.92, z + item['d'][2]/2 + 0.125)
            clearance_z = max(1.01, contact_z + 0.045)
            if clearance_z > 1.08:
                return
            preferred = 'left' if x+bx < 0 else 'right'
            alternate = 'right' if preferred == 'left' else 'left'
            arm = None
            for candidate in [preferred, alternate]:
                if move(candidate, [x, y, clearance_z]):
                    arm = candidate
                    break
            if arm is None:
                continue
            destination, radius = release_target(item, basket, arm, current, reservations)
            robot.gripper(arm=arm, command=1)
            if not move(arm, [x, y, contact_z]):
                return
            robot.gripper(arm=arm, command=0)
            if not move(arm, [x, y, clearance_z]):
                return
            if not move(arm, destination):
                return
            robot.gripper(arm=arm, command=1)
            # A reservation records release intent, not attachment or placement success.
            reservations.append((bx, by, destination[0], destination[1], radius))
    except Exception:
        # Uncertain execution is terminal; preserve the latched gripper state.
        return
