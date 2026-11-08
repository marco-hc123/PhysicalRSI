def policy(robot, memory):
    def normalize(q):
        n = sum(v * v for v in q) ** 0.5
        return [v / n for v in q] if n > 0.000001 else None

    quats = {
        'left': normalize([0.613, -0.3593, 0.6163, 0.3392]),
        'right': normalize([0.3814, -0.6197, 0.3785, 0.572])
    }

    def read_scene():
        data = robot.scene()
        if not isinstance(data, dict) or not isinstance(data.get('objects'), dict):
            return []
        result = []
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
            if not all(v > 0 for v in d) or normalize(p[3:7]) is None:
                continue
            result.append({'category': category, 'p': list(p), 'd': list(d)})
        return result

    def basis(basket):
        w, x, y, z = normalize(basket['p'][3:7])
        return (1 - 2 * (y*y + z*z), 2 * (x*y - w*z),
                2 * (x*y + w*z), 1 - 2 * (x*x + z*z))

    def inside(item, basket, margin=0.016):
        a, b, c, d = basis(basket)
        dx = item['p'][0] - basket['p'][0]
        dy = item['p'][1] - basket['p'][1]
        lx, ly = a*dx + c*dy, b*dx + d*dy
        return (abs(lx) < basket['d'][0]/2 - margin and
                abs(ly) < basket['d'][1]/2 - margin)

    def move(arm, position):
        result = robot.approach(arm=arm, position_m=position, quaternion_wxyz=quats[arm])
        if isinstance(result, dict) and result.get('primitive_error'):
            if result['primitive_error'] == 'no_collision_free_path':
                return False
            raise RuntimeError('Uncertain motion execution')
        return True

    def grip(arm, command):
        result = robot.gripper(arm=arm, command=command)
        if isinstance(result, dict) and result.get('primitive_error'):
            raise RuntimeError('Uncertain gripper execution')

    def release_site(item, basket, basket_index, current, reservations):
        # Stay inside a footprint-dependent margin rather than using a fixed world offset.
        half_item = max(item['d'][0], item['d'][1]) / 2
        ux = 0.8 * max(0.0, basket['d'][0]/2 - max(0.025, half_item + 0.012))
        uy = 0.8 * max(0.0, basket['d'][1]/2 - max(0.025, half_item + 0.012))
        a, b, c, d = basis(basket)
        occupied = [(o['p'][0], o['p'][1]) for o in current
                    if o['category'] != 'basket' and inside(o, basket, 0.0)]
        occupied += [(x, y) for i, x, y in reservations if i == basket_index]
        candidates = []
        for lx in [0.0, -ux, ux]:
            for ly in [0.0, -uy, uy]:
                x = basket['p'][0] + a*lx + b*ly
                y = basket['p'][1] + c*lx + d*ly
                center_cost = lx*lx + ly*ly
                separation = min(((x-ox)**2 + (y-oy)**2 for ox, oy in occupied), default=0.0)
                score = separation - 0.15*center_cost if occupied else -center_cost
                candidates.append((score, -center_cost, x, y))
        best = max(candidates, key=lambda v: (v[0], v[1]))
        return best[2], best[3]

    def transport(arm, start, destination, level):
        dx, dy = destination[0]-start[0], destination[1]-start[1]
        distance = (dx*dx + dy*dy) ** 0.5
        segments = max(1, min(3, int(distance/0.18) + 1))
        last = list(start)
        elevated = False
        for step in range(1, segments + 1):
            fraction = step / segments
            target = [start[0] + fraction*dx, start[1] + fraction*dy, level]
            if not move(arm, target):
                # A returned no-path result certifies zero execution of that call only.
                # Permit one higher route, never an arm switch while potentially carrying.
                if elevated or level + 0.025 > 1.08:
                    return False
                level += 0.025
                if not move(arm, [last[0], last[1], level]):
                    return False
                target[2] = level
                if not move(arm, target):
                    return False
                elevated = True
            last = target
        return True

    try:
        initial = read_scene()
        anchors = sorted([o for o in initial if o['category'] == 'basket'],
                         key=lambda o: (o['p'][0], o['p'][1]))
        items = [o for o in initial if o['category'] != 'basket']
        categories = sorted(set(o['category'] for o in items))
        if not categories or not anchors or len(anchors) > 8 or len(categories) > len(anchors):
            return

        # Exact small assignment: first avoid disturbing already grouped objects,
        # then favor shorter transfers. No category-specific basket identities.
        costs = {}
        for category in categories:
            group = [o for o in items if o['category'] == category]
            for i, basket in enumerate(anchors):
                total = 0.0
                for obj in group:
                    distance2 = sum((obj['p'][k]-basket['p'][k])**2 for k in [0, 1])
                    total += 0.001*distance2 if inside(obj, basket) else 1.0 + 0.05*distance2
                costs[(category, i)] = total
        states = {0: (0.0, [])}
        for category in categories:
            following = {}
            for mask, entry in states.items():
                score, path = entry
                for i in range(len(anchors)):
                    if mask & (1 << i):
                        continue
                    new_mask = mask | (1 << i)
                    value = score + costs[(category, i)]
                    if new_mask not in following or value < following[new_mask][0]:
                        following[new_mask] = (value, path + [i])
            states = following
        if not states:
            return
        best = min(states.values(), key=lambda entry: entry[0])
        assignments = dict(zip(categories, best[1]))
        attempted = []
        reservations = []

        for turn in range(12):
            current = read_scene()
            visible_baskets = [o for o in current if o['category'] == 'basket']
            # Reassociate baskets geometrically; instance suffixes are not persistent IDs.
            pairs = []
            for i, anchor in enumerate(anchors):
                for j, basket in enumerate(visible_baskets):
                    distance2 = sum((anchor['p'][k]-basket['p'][k])**2 for k in [0, 1])
                    if distance2 <= 0.0064:
                        pairs.append((distance2, i, j))
            matched, used = {}, set()
            for distance2, i, j in sorted(pairs):
                if i not in matched and j not in used:
                    matched[i] = visible_baskets[j]
                    used.add(j)

            choices = []
            for index, item in enumerate(current):
                category = item['category']
                if category not in assignments:
                    continue
                basket_index = assignments[category]
                if basket_index not in matched:
                    continue
                basket = matched[basket_index]
                if inside(item, basket):
                    continue
                x, y, z = item['p'][:3]
                prior = sum(1 for c, px, py in attempted
                            if c == category and (x-px)**2 + (y-py)**2 < 0.001225)
                if prior >= 2:
                    continue
                # Nominal Z is used only to set the contact geometry, never to verify lifting.
                contact = max(0.92, z + 0.125)
                level = max(1.03, contact + 0.065)
                if level > 1.08:
                    continue
                distance2 = (x-basket['p'][0])**2 + (y-basket['p'][1])**2
                choices.append((3.0*prior + distance2, index, item, basket, basket_index, contact, level))
            if not choices:
                return
            choice = min(choices, key=lambda entry: (entry[0], entry[1]))
            _, _, item, basket, basket_index, contact, level = choice
            x, y = item['p'][:2]
            tx, ty = release_site(item, basket, basket_index, current, reservations)
            attempted.append((item['category'], x, y))
            preferred = 'left' if x + tx < 0 else 'right'
            alternate = 'right' if preferred == 'left' else 'left'
            arm = None
            for candidate in [preferred, alternate]:
                if move(candidate, [x, y, level]):
                    arm = candidate
                    break
            if arm is None:
                attempted.append((item['category'], x, y))
                continue

            grip(arm, 1)
            if not move(arm, [x, y, contact]):
                return
            grip(arm, 0)
            if not move(arm, [x, y, level]):
                return
            if not transport(arm, [x, y], [tx, ty], level):
                return
            if not move(arm, [tx, ty, 1.01]):
                return
            grip(arm, 1)
            # Reserve the commanded release site conservatively, not as delivery evidence.
            reservations.append((basket_index, tx, ty))
            if not move(arm, [tx, ty, min(1.08, max(1.055, level))]):
                return
            # Only after a completed release sequence may fresh perception support another cycle.
    except Exception:
        # No retries, reopening, or arm switching after uncertain partial execution.
        return
