def policy(robot, memory):
    def unit(q):
        n = sum(v * v for v in q) ** 0.5
        return [v / n for v in q] if n > 0.000001 else None

    orientations = {
        'left': unit([0.613, -0.3593, 0.6163, 0.3392]),
        'right': unit([0.3814, -0.6197, 0.3785, 0.572])
    }
    calls = {'motion': 0, 'gripper': 0}

    def check(result):
        if isinstance(result, dict) and result.get('primitive_error'):
            if result['primitive_error'] == 'no_collision_free_path':
                return False
            raise RuntimeError('Uncertain primitive execution')
        return True

    def move(arm, position):
        if calls['motion'] >= 80:
            raise RuntimeError('Local motion bound')
        calls['motion'] += 1
        return check(robot.approach(arm=arm, position_m=position,
                                    quaternion_wxyz=orientations[arm]))

    def grip(arm, command):
        if calls['gripper'] >= 60:
            raise RuntimeError('Local gripper bound')
        calls['gripper'] += 1
        if not check(robot.gripper(arm=arm, command=command)):
            raise RuntimeError('Gripper execution unavailable')

    def scene():
        data = robot.scene()
        if not isinstance(data, dict) or not isinstance(data.get('objects'), dict):
            return None
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
            if not all(isinstance(v, (int, float)) and v == v and abs(v) < 10
                       for v in list(p) + list(d)):
                continue
            if min(d) <= 0 or unit(p[3:7]) is None:
                continue
            objects.append({'category': category, 'p': list(p), 'd': list(d)})
        return objects

    def basis(basket):
        w, x, y, z = unit(basket['p'][3:7])
        return (1 - 2 * (y*y + z*z), 2 * (x*y - w*z),
                2 * (x*y + w*z), 1 - 2 * (x*x + z*z))

    def inside(item, basket):
        a, b, c, d = basis(basket)
        dx = item['p'][0] - basket['p'][0]
        dy = item['p'][1] - basket['p'][1]
        lx, ly = a*dx + c*dy, b*dx + d*dy
        return (abs(lx) < basket['d'][0] / 2 - 0.012 and
                abs(ly) < basket['d'][1] / 2 - 0.012)

    def distance2(a, b):
        return (a['p'][0] - b['p'][0])**2 + (a['p'][1] - b['p'][1])**2

    def release_xy(item, basket, objects):
        radius = max(item['d'][:2]) / 2
        hx = max(0.0, basket['d'][0] / 2 - radius - 0.025) * 0.85
        hy = max(0.0, basket['d'][1] / 2 - radius - 0.025) * 0.85
        offsets = [(0, 0), (hx, 0), (-hx, 0), (0, hy), (0, -hy),
                   (hx, hy), (hx, -hy), (-hx, hy), (-hx, -hy)]
        occupants = [o for o in objects if o['category'] != 'basket'
                     and o is not item and inside(o, basket)]
        a, b, c, d = basis(basket)
        best = None
        for index, (lx, ly) in enumerate(offsets):
            x = basket['p'][0] + a*lx + b*ly
            y = basket['p'][1] + c*lx + d*ly
            cost = 0.1 * (lx*lx + ly*ly)
            for other in occupants:
                separation = ((x-other['p'][0])**2 + (y-other['p'][1])**2)**0.5
                wanted = radius + max(other['d'][:2]) / 2 + 0.012
                cost += 1000 * max(0.0, wanted-separation)**2
            candidate = (cost, index, x, y)
            if best is None or candidate < best:
                best = candidate
        return best[2], best[3]

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

        # Globally assign baskets, prioritizing preservation of visible occupants.
        costs = []
        for category in categories:
            group = [o for o in items if o['category'] == category]
            costs.append([sum(0.0 if inside(o, basket) else
                              1.0 + 0.1 * distance2(o, basket) for o in group)
                          for basket in baskets])
        states = {0: (0.0, ())}
        for row in costs:
            following = {}
            for mask, (cost, path) in states.items():
                for i in range(len(baskets)):
                    if mask & (1 << i):
                        continue
                    new_mask = mask | (1 << i)
                    candidate = (cost + row[i], path + (i,))
                    if new_mask not in following or candidate < following[new_mask]:
                        following[new_mask] = candidate
            states = following
        if not states:
            return
        allocation = min(states.values())[1]
        assignment = dict(zip(categories, allocation))
        attempts = []

        for cycle in range(min(12, len(items) + 4)):
            if calls['motion'] > 70 or calls['gripper'] > 55:
                return
            current = scene()
            if current is None:
                return
            visible = [o for o in current if o['category'] == 'basket']
            # Frame-local names are discarded; baskets are reassociated spatially.
            matched, used = {}, set()
            for index, anchor in enumerate(baskets):
                options = sorted((distance2(anchor, basket), j)
                                 for j, basket in enumerate(visible) if j not in used)
                if not options or options[0][0] > 0.0064:
                    return
                if len(options) > 1 and options[1][0] - options[0][0] < 0.0002:
                    return
                j = options[0][1]
                matched[index] = visible[j]
                used.add(j)
            for index in matched:
                baskets[index] = matched[index]

            choices = []
            for item in current:
                category = item['category']
                if category not in assignment:
                    continue
                basket = matched[assignment[category]]
                if inside(item, basket):
                    continue
                x, y = item['p'][:2]
                nearby = [record for record in attempts
                          if record['category'] == category and
                          (record['x']-x)**2 + (record['y']-y)**2 < 0.000625]
                record = min(nearby, key=lambda r: (r['x']-x)**2 + (r['y']-y)**2) if nearby else None
                count = record['count'] if record else 0
                if count >= 2:
                    continue
                cost = distance2(item, basket) + 0.15 * count
                choices.append((cost, len(choices), item, basket, record))
            if not choices:
                return
            _, _, item, basket, record = min(choices, key=lambda entry: entry[:2])
            x, y, z = item['p'][:3]
            tx, ty = release_xy(item, basket, current)
            prior_count = record['count'] if record else 0

            # Nominal Z supports a contact target, not a measured lift test.
            contact = max(0.92, z + 0.125 - 0.004 * prior_count)
            cruise = max(1.055, contact + 0.065)
            if cruise > 1.08:
                return
            preferred = 'left' if x + tx < 0 else 'right'
            if record is not None and record.get('arm'):
                preferred = 'right' if record['arm'] == 'left' else 'left'
            alternate = 'right' if preferred == 'left' else 'left'
            arm = None
            for candidate in (preferred, alternate):
                if move(candidate, [x, y, cruise]):
                    arm = candidate
                    break
            if record is None:
                record = {'category': item['category'], 'x': x, 'y': y,
                          'count': 0, 'arm': None}
                attempts.append(record)
            record['count'] += 1
            record['arm'] = arm
            if arm is None:
                continue

            grip(arm, 1)
            if not move(arm, [x, y, contact]):
                return
            grip(arm, 0)
            grip(arm, 0)

            # One height-only alternative is allowed after a zero-execution rejection.
            recovery = [False]
            def carry(position):
                if move(arm, position):
                    return True
                if recovery[0] or position[2] >= 1.079:
                    return False
                recovery[0] = True
                return move(arm, [position[0], position[1], 1.08])

            if not carry([x, y, cruise]):
                return
            if (x-tx)**2 + (y-ty)**2 > 0.0784:
                if not carry([(x+tx)/2, (y+ty)/2, cruise]):
                    return
            if not carry([tx, ty, cruise]):
                return
            # Release is centered within the basket, without fixed world offsets.
            if not move(arm, [tx, ty, 1.01]):
                return
            grip(arm, 0)
            grip(arm, 1)
            if not move(arm, [tx, ty, min(1.08, cruise + 0.015)]):
                return
            # The next cycle obtains fresh RGB after the hand has cleared the basket.
    except Exception:
        # Never open or switch arms after uncertain partial physical execution.
        return
