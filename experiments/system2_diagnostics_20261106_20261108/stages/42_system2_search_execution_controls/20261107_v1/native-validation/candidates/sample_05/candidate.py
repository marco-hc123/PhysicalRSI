def policy(robot, memory):
    def normalize(q):
        n = sum(v * v for v in q) ** 0.5
        return [v / n for v in q] if n > 0.000001 else None

    quaternions = {
        'left': normalize([0.613, -0.3593, 0.6163, 0.3392]),
        'right': normalize([0.3814, -0.6197, 0.3785, 0.572])
    }

    def read_scene():
        data = robot.scene()
        if not isinstance(data, dict) or not isinstance(data.get('objects'), dict):
            return []
        objects = []
        for key, value in list(data['objects'].items())[:64]:
            if not isinstance(key, str) or '_' not in key or not isinstance(value, dict):
                continue
            category, suffix = key.rsplit('_', 1)
            if not category or not suffix.isdigit() or int(suffix) < 1:
                continue
            p, d = value.get('pose'), value.get('dims')
            if not isinstance(p, (list, tuple)) or not isinstance(d, (list, tuple)):
                continue
            if len(p) != 7 or len(d) != 3:
                continue
            if not all(isinstance(v, (int, float)) and v == v and abs(v) < 10 for v in list(p) + list(d)):
                continue
            if not all(v > 0 for v in d):
                continue
            objects.append({'category': category, 'p': list(p), 'd': list(d)})
        return objects

    def aligned(item, basket):
        q = normalize(basket['p'][3:7])
        if q is None:
            return False
        w, x, y, z = q
        dx = item['p'][0] - basket['p'][0]
        dy = item['p'][1] - basket['p'][1]
        lx = (1 - 2 * (y*y + z*z)) * dx + 2 * (x*y + w*z) * dy
        ly = 2 * (x*y - w*z) * dx + (1 - 2 * (x*x + z*z)) * dy
        return abs(lx) < basket['d'][0] / 2 - 0.012 and abs(ly) < basket['d'][1] / 2 - 0.012

    def move(arm, position):
        result = robot.approach(arm=arm, position_m=position, quaternion_wxyz=quaternions[arm])
        if isinstance(result, dict) and result.get('primitive_error'):
            if result['primitive_error'] == 'no_collision_free_path':
                return False
            raise RuntimeError('Uncertain motion execution')
        return True

    def grip(arm, command):
        result = robot.gripper(arm=arm, command=command)
        if isinstance(result, dict) and result.get('primitive_error'):
            raise RuntimeError('Uncertain gripper execution')

    def distance2(a, b):
        return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2

    try:
        initial = read_scene()
        anchors = sorted([o for o in initial if o['category'] == 'basket'], key=lambda b: (b['p'][0], b['p'][1]))
        items = [o for o in initial if o['category'] != 'basket']
        categories = sorted(set(o['category'] for o in items))
        if not categories or not anchors or len(anchors) > 8 or len(categories) > len(anchors):
            return
        if any(normalize(b['p'][3:7]) is None for b in anchors):
            return

        # Minimize visible relocations first, then estimated transport distance.
        # This uses public RGB geometry, not persistent instance identities.
        states = {0: (0, 0.0, [])}
        for category in categories:
            group = [o for o in items if o['category'] == category]
            costs = []
            for basket in anchors:
                relocations = sum(1 for o in group if not aligned(o, basket))
                travel = sum(distance2(o['p'], basket['p']) for o in group)
                costs.append((relocations, travel))
            next_states = {}
            for mask, state in states.items():
                for index in range(len(anchors)):
                    bit = 1 << index
                    if mask & bit:
                        continue
                    cost = costs[index]
                    candidate = (state[0] + cost[0], state[1] + cost[1], state[2] + [index])
                    new_mask = mask | bit
                    old = next_states.get(new_mask)
                    if old is None or candidate[:2] < old[:2]:
                        next_states[new_mask] = candidate
            states = next_states
        if not states:
            return
        best = min(states.values(), key=lambda state: state[:2])
        assignments = dict(zip(categories, best[2]))
        history = []

        for cycle in range(16):
            current = read_scene()
            visible_baskets = [o for o in current if o['category'] == 'basket']
            matched = {}
            for index, anchor in enumerate(anchors):
                nearby = sorted(visible_baskets, key=lambda b: distance2(b['p'], anchor['p']))
                if not nearby or distance2(nearby[0]['p'], anchor['p']) > 0.0081:
                    continue
                basket = nearby[0]
                nearest_anchor = min(range(len(anchors)), key=lambda j: distance2(basket['p'], anchors[j]['p']))
                if nearest_anchor != index:
                    continue
                if len(nearby) > 1:
                    first = distance2(nearby[0]['p'], anchor['p']) ** 0.5
                    second = distance2(nearby[1]['p'], anchor['p']) ** 0.5
                    if second - first < 0.025:
                        continue
                matched[index] = basket

            choices = []
            for item in current:
                category = item['category']
                if category not in assignments:
                    continue
                basket = matched.get(assignments[category])
                if basket is None or aligned(item, basket):
                    continue
                previous = [h for h in history if h[0] == category and distance2(item['p'], h[1]) < 0.000324]
                if any(h[2] == 'blocked' for h in previous) or len(previous) >= 2:
                    continue
                contact_z = max(0.92, item['p'][2] + 0.125)
                basket_top = basket['p'][2] + basket['d'][2] / 2
                clearance_z = max(1.04, contact_z + 0.07, basket_top + 0.125 + item['d'][2] / 2 + 0.015)
                if clearance_z > 1.16:
                    continue
                choices.append((len(previous), distance2(item['p'], basket['p']), item, basket, contact_z, clearance_z))
            if not choices:
                return
            choices.sort(key=lambda entry: (entry[0], entry[1]))
            _, travel2, item, basket, contact_z, clearance_z = choices[0]
            x, y = item['p'][:2]
            bx, by = basket['p'][:2]
            category = item['category']
            preferred = 'left' if x + bx < 0 else 'right'
            alternate = 'right' if preferred == 'left' else 'left'
            arm = None

            # Alternate-arm attempts occur only after explicit zero-execution
            # path rejection, before any closing command.
            for candidate in [preferred, alternate]:
                if not move(candidate, [x, y, clearance_z]):
                    continue
                grip(candidate, 1)
                if not move(candidate, [x, y, contact_z]):
                    continue
                arm = candidate
                break
            if arm is None:
                history.append((category, [x, y], 'blocked'))
                continue

            # Contact is near the nominal object center rather than its top edge.
            # The second close adds bounded settling; neither call proves a grasp.
            grip(arm, 0)
            grip(arm, 0)
            if not move(arm, [x, y, clearance_z]):
                clearance_z += 0.025
                if not move(arm, [x, y, clearance_z]):
                    return

            last_x, last_y = x, y
            if travel2 > 0.1296:
                mx, my = (x + bx) / 2, (y + by) / 2
                if move(arm, [mx, my, clearance_z]):
                    last_x, last_y = mx, my

            # Transport above the basket center before descending vertically.
            # A rejected path permits one same-arm higher-clearance route.
            if not move(arm, [bx, by, clearance_z]):
                higher_z = clearance_z + 0.025
                if not move(arm, [last_x, last_y, higher_z]):
                    return
                if not move(arm, [bx, by, higher_z]):
                    return
                clearance_z = higher_z
            if not move(arm, [bx, by, 1.01]):
                return
            grip(arm, 1)
            grip(arm, 1)
            history.append((category, [x, y], 'released'))
            if not move(arm, [bx, by, clearance_z]):
                return
            # The next cycle obtains fresh RGB detections. Disappearance, Z,
            # and instance suffixes are never used to certify delivery.
    except Exception:
        # Partial execution is uncertain: preserve the last explicit gripper
        # command and do not restart the manipulation.
        return
