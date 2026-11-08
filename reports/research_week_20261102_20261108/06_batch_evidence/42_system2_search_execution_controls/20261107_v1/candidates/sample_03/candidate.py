def policy(robot, memory):
    def normalize(q):
        n = sum(v * v for v in q) ** 0.5
        if n < 0.000001:
            return None
        return [v / n for v in q]

    quats = {
        'left': normalize([0.613, -0.3593, 0.6163, 0.3392]),
        'right': normalize([0.3814, -0.6197, 0.3785, 0.572])
    }

    def scene():
        data = robot.scene()
        if not isinstance(data, dict) or not isinstance(data.get('objects'), dict):
            return None
        objects = []
        for key, obj in list(data['objects'].items())[:96]:
            if not isinstance(key, str) or '_' not in key or not isinstance(obj, dict):
                continue
            category, suffix = key.rsplit('_', 1)
            if not category or not suffix.isdigit() or int(suffix) < 1:
                continue
            p, d = obj.get('pose'), obj.get('dims')
            if not isinstance(p, (list, tuple)) or not isinstance(d, (list, tuple)):
                continue
            if len(p) != 7 or len(d) != 3:
                continue
            if not all(isinstance(v, (int, float)) and v == v and abs(v) < 10 for v in list(p) + list(d)):
                continue
            if not all(v > 0 for v in d):
                continue
            q = normalize(p[3:7])
            if q is None:
                continue
            objects.append({'category': category, 'p': list(p), 'd': list(d), 'q': q})
        return objects

    def basis(basket):
        w, x, y, z = basket['q']
        return (1 - 2 * (y*y + z*z), 2 * (x*y - w*z),
                2 * (x*y + w*z), 1 - 2 * (x*x + z*z))

    def inside(item, basket):
        a, b, c, d = basis(basket)
        dx = item['p'][0] - basket['p'][0]
        dy = item['p'][1] - basket['p'][1]
        lx, ly = a*dx + c*dy, b*dx + d*dy
        margin = 0.015 + 0.15 * min(item['d'][0], item['d'][1])
        return (abs(lx) < basket['d'][0]/2 - margin and
                abs(ly) < basket['d'][1]/2 - margin)

    def move(arm, position):
        result = robot.approach(arm=arm, position_m=position, quaternion_wxyz=quats[arm])
        if isinstance(result, dict) and result.get('primitive_error'):
            if result['primitive_error'] == 'no_collision_free_path':
                return False
            raise RuntimeError('Uncertain approach execution')
        return True

    def grip(arm, command):
        result = robot.gripper(arm=arm, command=command)
        if isinstance(result, dict) and result.get('primitive_error'):
            raise RuntimeError('Uncertain gripper execution')

    try:
        initial = scene()
        if initial is None:
            return
        baskets = sorted([o for o in initial if o['category'] == 'basket'],
                         key=lambda o: (o['p'][0], o['p'][1]))
        items = [o for o in initial if o['category'] != 'basket']
        categories = sorted(set(o['category'] for o in items))
        if not categories or len(categories) > len(baskets) or len(baskets) > 8:
            return

        # Bounded minimum-cost one-to-one category assignment. Existing
        # occupants reduce the cost without requiring persistent instance IDs.
        costs = []
        for category in categories:
            group = [o for o in items if o['category'] == category]
            row = []
            for basket in baskets:
                value = 0.0
                for item in group:
                    if not inside(item, basket):
                        dx = item['p'][0] - basket['p'][0]
                        dy = item['p'][1] - basket['p'][1]
                        value += 0.03 + dx*dx + dy*dy
                row.append(value)
            costs.append(row)
        states = {0: (0.0, [])}
        for row in costs:
            following = {}
            for mask, state in states.items():
                for i in range(len(baskets)):
                    bit = 1 << i
                    if mask & bit:
                        continue
                    new_mask = mask | bit
                    value = state[0] + row[i]
                    previous = following.get(new_mask)
                    if previous is None or value < previous[0]:
                        following[new_mask] = (value, state[1] + [i])
            states = following
        if not states:
            return
        selected = min(states.values(), key=lambda state: state[0])[1]
        assignment = {category: selected[i] for i, category in enumerate(categories)}

        attempts = []
        tentative_drops = []
        routed = set()

        for turn in range(12):
            current = scene()
            if current is None:
                return
            observed_baskets = [o for o in current if o['category'] == 'basket']
            available = list(observed_baskets)
            matched = {}
            for i, anchor in enumerate(baskets):
                if not available:
                    break
                candidate = min(available, key=lambda b: (b['p'][0]-anchor['p'][0])**2 + (b['p'][1]-anchor['p'][1])**2)
                distance = ((candidate['p'][0]-anchor['p'][0])**2 +
                            (candidate['p'][1]-anchor['p'][1])**2)
                if distance < 0.01:
                    matched[i] = candidate
                    available.remove(candidate)

            choices = []
            for item in current:
                category = item['category']
                if category not in assignment:
                    continue
                index = assignment[category]
                basket = matched.get(index)
                if basket is None or inside(item, basket):
                    continue
                x, y = item['p'][:2]
                nearby = [r for r in attempts if r['category'] == category and
                          (x-r['x'])**2 + (y-r['y'])**2 < 0.001225]
                record = min(nearby, key=lambda r: (x-r['x'])**2 + (y-r['y'])**2) if nearby else None
                count = record['count'] if record is not None else 0
                if count >= 2:
                    continue
                distance = (x-basket['p'][0])**2 + (y-basket['p'][1])**2
                choices.append((count, distance, item, basket, index, record))
            if not choices:
                # Lack of visible work is not a task-success signal.
                return
            choices.sort(key=lambda entry: (entry[0], entry[1]))
            _, _, item, basket, index, record = choices[0]
            x, y, z = item['p'][:3]
            bx, by = basket['p'][:2]

            # Interior release slots are geometry-derived, not fixed world offsets.
            occupied = [(o['p'][0], o['p'][1]) for o in current
                        if o['category'] != 'basket' and inside(o, basket)]
            occupied += [(px, py) for bi, px, py in tentative_drops if bi == index]
            rx, ry = bx, by
            if occupied:
                half_item = max(item['d'][0], item['d'][1]) / 2
                sx = max(0.0, basket['d'][0]/2 - half_item - 0.025) * 0.55
                sy = max(0.0, basket['d'][1]/2 - half_item - 0.025) * 0.55
                a, b, c, d = basis(basket)
                slots = []
                for u in [-sx, 0.0, sx]:
                    for v in [-sy, 0.0, sy]:
                        px, py = bx + a*u + b*v, by + c*u + d*v
                        clearance = min((px-ox)**2 + (py-oy)**2 for ox, oy in occupied)
                        score = clearance - 0.15*((px-bx)**2 + (py-by)**2)
                        slots.append((score, px, py))
                _, rx, ry = max(slots, key=lambda slot: slot[0])

            contact_z = max(0.92, z + item['d'][2]/2 + 0.125)
            rim_z = basket['p'][2] + basket['d'][2]/2
            carry_z = max(1.04, contact_z + 0.055,
                          rim_z + 0.125 + item['d'][2] + 0.012)
            preferred = 'left' if 0.4*x + 0.6*rx < 0 else 'right'
            if record is not None and record.get('arm'):
                preferred = 'right' if record['arm'] == 'left' else 'left'
            alternate = 'right' if preferred == 'left' else 'left'
            if record is None:
                record = {'category': item['category'], 'x': x, 'y': y, 'count': 0, 'arm': None}
                attempts.append(record)
            record['count'] += 1

            arm = None
            for candidate in [preferred, alternate]:
                grip(candidate, 1)
                # Visit the destination hover empty-handed once per arm/basket.
                # A normal return is not treated as proof of exact arrival.
                route_key = (candidate, index)
                if route_key not in routed:
                    if not move(candidate, [rx, ry, carry_z]):
                        continue
                    routed.add(route_key)
                if move(candidate, [x, y, carry_z]):
                    arm = candidate
                    break
            if arm is None:
                continue
            record['arm'] = arm

            if not move(arm, [x, y, contact_z]):
                return
            grip(arm, 0)
            # Explicit extra closed settling before any lift.
            grip(arm, 0)
            if not move(arm, [x, y, carry_z]):
                return

            # Split long transfers; retain the closed setpoint throughout.
            distance = ((rx-x)**2 + (ry-y)**2) ** 0.5
            if distance > 0.30:
                if not move(arm, [(x+rx)/2, (y+ry)/2, carry_z]):
                    return
            if not move(arm, [rx, ry, carry_z]):
                return
            # A separate final descent also gives the lateral target another
            # bounded convergence phase before opening.
            if not move(arm, [rx, ry, 1.01]):
                return
            grip(arm, 1)
            grip(arm, 1)
            tentative_drops.append((index, rx, ry))
            if not move(arm, [rx, ry, max(carry_z, 1.075)]):
                return
            # Only a later, positively detected outside object can become a
            # retry candidate. Missing objects and nominal Z prove nothing.
    except Exception:
        # Do not issue recovery motions after uncertain partial execution.
        # In particular, preserve a closed gripper if transport was interrupted.
        return
