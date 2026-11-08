def policy(robot, memory):
    def normalize(q):
        n = sum(v * v for v in q) ** 0.5
        return [v / n for v in q] if n > 0.000001 else None

    quats = {
        'left': normalize([0.613, -0.3593, 0.6163, 0.3392]),
        'right': normalize([0.3814, -0.6197, 0.3785, 0.572])
    }

    def check(result):
        if isinstance(result, dict) and result.get('primitive_error'):
            if result['primitive_error'] == 'no_collision_free_path':
                return False
            raise RuntimeError('Uncertain primitive execution')
        return True

    def move(arm, position):
        return check(robot.approach(arm=arm, position_m=position, quaternion_wxyz=quats[arm]))

    def grip(arm, command):
        if not check(robot.gripper(arm=arm, command=command)):
            raise RuntimeError('Unexpected gripper rejection')

    def read_scene():
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
            p, d = obj.get('pose'), obj.get('dims')
            if not isinstance(p, (list, tuple)) or not isinstance(d, (list, tuple)):
                continue
            if len(p) != 7 or len(d) != 3:
                continue
            if not all(isinstance(v, (int, float)) and v == v and abs(v) < 10 for v in list(p) + list(d)):
                continue
            if not all(v > 0 for v in d) or normalize(p[3:7]) is None:
                continue
            result.append({'category': category, 'p': list(p), 'd': list(d)})
        return result

    def rotation(basket):
        w, x, y, z = normalize(basket['p'][3:7])
        return (1 - 2 * (y*y + z*z), 2 * (x*y - w*z),
                2 * (x*y + w*z), 1 - 2 * (x*x + z*z))

    def inside(item, basket):
        a, b, c, d = rotation(basket)
        dx = item['p'][0] - basket['p'][0]
        dy = item['p'][1] - basket['p'][1]
        lx, ly = a*dx + c*dy, b*dx + d*dy
        margin = 0.015 + min(0.02, min(item['d'][:2]) * 0.25)
        return abs(lx) < basket['d'][0]/2 - margin and abs(ly) < basket['d'][1]/2 - margin

    def radius(item):
        return 0.5 * (item['d'][0]**2 + item['d'][1]**2) ** 0.5

    def release_points(item, basket, current, arm):
        # Empty baskets prefer the centre. Occupied baskets prefer separated,
        # interior locations derived from observed dimensions, not fixed offsets.
        a, b, c, d = rotation(basket)
        r = radius(item)
        hx = max(0.0, basket['d'][0]/2 - r - 0.018)
        hy = max(0.0, basket['d'][1]/2 - r - 0.018)
        occupants = [o for o in current if o is not item and o['category'] != 'basket' and inside(o, basket)]
        candidates = []
        for fx in [0.0, -0.85, 0.85]:
            for fy in [0.0, -0.85, 0.85]:
                lx, ly = fx*hx, fy*hy
                x = basket['p'][0] + a*lx + b*ly
                y = basket['p'][1] + c*lx + d*ly
                overlap = 0.0
                for other in occupants:
                    separation = ((x-other['p'][0])**2 + (y-other['p'][1])**2) ** 0.5
                    overlap += max(0.0, r + radius(other) + 0.012 - separation)**2
                side_cost = x if arm == 'right' else -x
                candidates.append((overlap, lx*lx + ly*ly - 0.0001*side_cost, x, y))
        candidates.sort()
        points = []
        for _, _, x, y in candidates:
            if all((x-p[0])**2 + (y-p[1])**2 > 0.0001 for p in points):
                points.append([x, y])
            if len(points) == 3:
                break
        return points

    try:
        initial = read_scene()
        anchors = sorted([o for o in initial if o['category'] == 'basket'], key=lambda o: (o['p'][0], o['p'][1]))
        items = [o for o in initial if o['category'] != 'basket']
        categories = sorted(set(o['category'] for o in items))
        if not categories or len(categories) > len(anchors) or len(anchors) > 8:
            return

        # Small bounded assignment DP: first minimize required relocations,
        # then observed planar travel. Basket identities are spatial anchors.
        states = {0: (0, 0.0, ())}
        for category in categories:
            group = [o for o in items if o['category'] == category]
            next_states = {}
            for mask, value in states.items():
                for i, basket in enumerate(anchors):
                    if mask & (1 << i):
                        continue
                    misses = sum(1 for o in group if not inside(o, basket))
                    distance = sum((o['p'][0]-basket['p'][0])**2 + (o['p'][1]-basket['p'][1])**2 for o in group)
                    candidate = (value[0] + misses, value[1] + distance, value[2] + (i,))
                    new_mask = mask | (1 << i)
                    if new_mask not in next_states or candidate < next_states[new_mask]:
                        next_states[new_mask] = candidate
            states = next_states
        if not states:
            return
        allocation = min(states.values())[2]
        assignments = {category: allocation[i] for i, category in enumerate(categories)}
        attempts = []

        for turn in range(16):
            current = read_scene()
            visible_baskets = [o for o in current if o['category'] == 'basket']
            pairs = []
            for i, anchor in enumerate(anchors):
                for j, basket in enumerate(visible_baskets):
                    distance = (anchor['p'][0]-basket['p'][0])**2 + (anchor['p'][1]-basket['p'][1])**2
                    if distance < 0.0144:
                        pairs.append((distance, i, j))
            matched, used = {}, set()
            for _, i, j in sorted(pairs):
                if i not in matched and j not in used:
                    matched[i] = visible_baskets[j]
                    used.add(j)
            for i, basket in matched.items():
                anchors[i] = basket

            choices = []
            for item in current:
                category = item['category']
                if category not in assignments or assignments[category] not in matched:
                    continue
                basket = matched[assignments[category]]
                if inside(item, basket):
                    continue
                x, y = item['p'][:2]
                nearby = [a for a in attempts if a['category'] == category and (x-a['x'])**2 + (y-a['y'])**2 < 0.0009]
                if len(nearby) >= 2:
                    continue
                contact = max(0.92, item['p'][2] + 0.125)
                rim = basket['p'][2] + basket['d'][2]/2
                height = max(1.065, contact + 0.09, rim + 0.125 + item['d'][2]/2 + 0.02)
                if height > 1.13:
                    continue
                distance = (x-basket['p'][0])**2 + (y-basket['p'][1])**2
                choices.append((len(nearby), distance, item, basket, contact, height, nearby))
            if not choices:
                return
            choices.sort(key=lambda v: (v[0], v[1]))
            _, _, item, basket, contact, height, nearby = choices[0]
            x, y = item['p'][:2]
            preferred = 'left' if x + basket['p'][0] < 0 else 'right'
            if nearby and nearby[-1]['arm'] is not None:
                preferred = 'right' if nearby[-1]['arm'] == 'left' else 'left'
            alternate = 'right' if preferred == 'left' else 'left'
            record = {'category': item['category'], 'x': x, 'y': y, 'arm': None}
            attempts.append(record)

            arm = None
            # Alternate arms only after an explicit zero-execution rejection.
            for candidate in [preferred, alternate]:
                if move(candidate, [x, y, height]):
                    arm = candidate
                    break
            if arm is None:
                attempts.append(dict(record))
                continue
            record['arm'] = arm
            grip(arm, 1)
            if not move(arm, [x, y, contact]):
                if not move(arm, [x, y, height]):
                    return
                continue

            # Nominal centre-depth contact rather than top-surface contact;
            # a second close supplies bounded stationary settling, not proof.
            grip(arm, 0)
            grip(arm, 0)
            carry_height = height
            if not move(arm, [x, y, carry_height]):
                carry_height = min(1.15, height + 0.02)
                if not move(arm, [x, y, carry_height]):
                    return

            destination = None
            for point in release_points(item, basket, current, arm):
                dx, dy = point
                if not move(arm, [dx, dy, carry_height]):
                    continue
                if not move(arm, [dx, dy, 1.01]):
                    continue
                destination = point
                break
            if destination is None:
                return

            # Separate high transport, low placement, stationary release and
            # vertical withdrawal. Primitive completion is never a grasp test.
            grip(arm, 0)
            grip(arm, 1)
            grip(arm, 1)
            if not move(arm, [destination[0], destination[1], carry_height]):
                return
            # Fresh RGB drives the next choice; no persistent instance IDs,
            # disappearance test, nominal-Z lift test, or success assertion.
    except Exception:
        # An exception may follow partial physical execution. Do not issue
        # speculative recovery or alter the last commanded gripper state.
        return
