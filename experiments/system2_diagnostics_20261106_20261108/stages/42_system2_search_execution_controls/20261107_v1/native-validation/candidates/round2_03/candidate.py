def policy(robot, memory):
    calls = 0

    def charge():
        nonlocal calls
        if calls >= 100:
            raise RuntimeError('RPC budget exhausted')
        calls += 1

    def normalize(q):
        n = sum(v*v for v in q) ** 0.5
        return [v/n for v in q] if n > 0.000001 else None

    quats = {
        'left': normalize([0.613, -0.3593, 0.6163, 0.3392]),
        'right': normalize([0.3814, -0.6197, 0.3785, 0.572])
    }

    def move(arm, position):
        charge()
        result = robot.approach(arm=arm, position_m=list(position), quaternion_wxyz=quats[arm])
        if isinstance(result, dict) and result.get('primitive_error'):
            if result['primitive_error'] == 'no_collision_free_path':
                return False
            raise RuntimeError('Uncertain motion execution')
        return True

    def grip(arm, command):
        charge()
        result = robot.gripper(arm=arm, command=command)
        if isinstance(result, dict) and result.get('primitive_error'):
            raise RuntimeError('Uncertain gripper execution')

    def read_scene():
        charge()
        data = robot.scene()
        if not isinstance(data, dict) or not isinstance(data.get('objects'), dict):
            return []
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
            if min(d) <= 0 or normalize(p[3:7]) is None:
                continue
            objects.append({'category': category, 'p': list(p), 'd': list(d)})
        return objects

    def basis(obj):
        w, x, y, z = normalize(obj['p'][3:7])
        return (1-2*(y*y+z*z), 2*(x*y-w*z),
                2*(x*y+w*z), 1-2*(x*x+z*z))

    def inside(item, basket, margin=0.012):
        a, b, c, d = basis(basket)
        dx = item['p'][0] - basket['p'][0]
        dy = item['p'][1] - basket['p'][1]
        return (abs(a*dx+c*dy) < basket['d'][0]/2-margin and
                abs(b*dx+d*dy) < basket['d'][1]/2-margin)

    def distance2(item, basket):
        return sum((item['p'][k]-basket['p'][k])**2 for k in [0, 1])

    def release_sites(item, basket, index, arm, current, reservations):
        a, b, c, d = basis(basket)
        ia, ib, ic, ident = basis(item)
        ex = (abs(a*ia+c*ic)*item['d'][0] + abs(a*ib+c*ident)*item['d'][1])/2
        ey = (abs(b*ia+d*ic)*item['d'][0] + abs(b*ib+d*ident)*item['d'][1])/2
        ux = basket['d'][0]/2-ex-0.012
        uy = basket['d'][1]/2-ey-0.012
        if ux < 0 or uy < 0:
            return []
        bx, by = basket['p'][:2]
        radius = max(item['d'][:2])/2
        occupied = [(o['p'][0], o['p'][1], max(o['d'][:2])/2)
                    for o in current if o['category'] != 'basket' and inside(o, basket, 0.0)]
        occupied += [(x, y, r) for i, x, y, r in reservations if i == index]
        side = -1 if arm == 'left' else 1
        candidates = []
        for fx in [-0.9, -0.25, 0.0, 0.25, 0.9]:
            for fy in [-0.9, -0.25, 0.0, 0.25, 0.9]:
                lx, ly = fx*ux, fy*uy
                x, y = bx+a*lx+b*ly, by+c*lx+d*ly
                gap = min((((x-ox)**2+(y-oy)**2)**0.5-radius-r
                           for ox, oy, r in occupied), default=0.1)
                # Prefer clear sites on the robot-facing, selected-arm side.
                bias = -(y-by) + 0.5*side*(x-bx)
                candidates.append((gap >= 0.006, bias+0.15*min(0.08, gap), x, y))
        candidates.sort(key=lambda entry: (entry[0], entry[1]), reverse=True)
        selected = []
        for _, _, x, y in candidates:
            if not selected or min((x-px)**2+(y-py)**2 for px, py in selected) >= 0.0004:
                selected.append((x, y))
                if len(selected) == 2:
                    break
        return selected

    try:
        initial = read_scene()
        anchors = sorted([o for o in initial if o['category'] == 'basket'],
                         key=lambda o: (o['p'][0], o['p'][1]))
        items = [o for o in initial if o['category'] != 'basket']
        categories = sorted(set(o['category'] for o in items))
        if not categories or not anchors or len(anchors) > 8 or len(categories) > len(anchors):
            return

        # Find a distinct basket assignment, chiefly minimizing required moves.
        costs = {}
        for category in categories:
            group = [o for o in items if o['category'] == category]
            for i, basket in enumerate(anchors):
                cost = 0.0
                for obj in group:
                    if inside(obj, basket):
                        cost += 0.001*distance2(obj, basket)
                    else:
                        crossing = max(0.0, -obj['p'][0]*basket['p'][0])
                        cost += 1.0+0.05*distance2(obj, basket)+0.3*crossing
                costs[(category, i)] = cost
        states = {0: (0.0, [])}
        for category in categories:
            following = {}
            for mask, (score, path) in states.items():
                for i in range(len(anchors)):
                    if mask & (1 << i):
                        continue
                    new_mask = mask | (1 << i)
                    value = score+costs[(category, i)]
                    if new_mask not in following or value < following[new_mask][0]:
                        following[new_mask] = (value, path+[i])
            states = following
        if not states:
            return
        assignments = dict(zip(categories, min(states.values(), key=lambda entry: entry[0])[1]))

        # The inactive gripper must also be open during separation transitions.
        grip('left', 1)
        grip('right', 1)
        attempts, reservations = [], []
        manipulations = 0

        for turn in range(12):
            # Reserve enough calls for a complete cycle or a source-site rollback.
            if calls > 80 or manipulations >= 8:
                return
            current = initial if turn == 0 else read_scene()
            visible = [o for o in current if o['category'] == 'basket']
            pairs = []
            for i, anchor in enumerate(anchors):
                for j, basket in enumerate(visible):
                    dist = distance2(anchor, basket)
                    if dist <= 0.0064:
                        pairs.append((dist, i, j))
            matched, used = {}, set()
            for _, i, j in sorted(pairs):
                if i not in matched and j not in used:
                    matched[i] = visible[j]
                    used.add(j)

            records = []
            for item in current:
                category = item['category']
                if category not in assignments:
                    continue
                index = assignments[category]
                if index not in matched or inside(item, matched[index]):
                    continue
                x, y, z = item['p'][:3]
                prior = sum(1 for cat, px, py in attempts
                            if cat == category and (x-px)**2+(y-py)**2 < 0.000625)
                if prior >= 2:
                    continue
                contact = max(0.92, z+item['d'][2]/2+0.125)
                level = max(1.01, contact+0.045)
                if level > 1.08:
                    continue
                records.append((item, matched[index], index, prior, contact, level))
            if not records:
                return

            # Finish small groups instead of moving one object from every class.
            # Clearing a foreign occupant is also work toward that group.
            group_options = []
            for category in categories:
                index = assignments[category]
                if index not in matched:
                    continue
                basket = matched[index]
                needed = [r for r in records if r[0]['category'] == category or inside(r[0], basket, 0.0)]
                if not needed:
                    continue
                work = sum(1 for o in current if o['category'] == category and not inside(o, basket))
                work += sum(1 for o in current if o['category'] not in ['basket', category] and inside(o, basket, 0.0))
                best = min(needed, key=lambda r: (r[3], distance2(r[0], r[1])))
                group_options.append((work+2*best[3], distance2(best[0], best[1]), best))
            if not group_options:
                return
            item, basket, index, prior, contact, level = min(group_options, key=lambda entry: (entry[0], entry[1]))[2]
            x, y = item['p'][:2]
            attempts.append((item['category'], x, y))
            preferred = 'left' if x+2*basket['p'][0] < 0 else 'right'
            arms = [preferred, 'right' if preferred == 'left' else 'left']
            chosen = None
            endpoint_tests = 0

            # Test both ends with an open gripper before committing to contact.
            for arm in arms:
                if not move(arm, [x, y, level]):
                    continue
                sites = release_sites(item, basket, index, arm, current, reservations)
                if not sites:
                    continue
                nominal = max(1.01, contact+0.02)
                lower = max(0.99, contact+0.02)
                proposals = [(sites[0][0], sites[0][1], nominal)]
                if lower < nominal-0.005:
                    proposals.append((sites[0][0], sites[0][1], lower))
                if len(sites) > 1:
                    proposals.append((sites[1][0], sites[1][1], nominal))
                destination = None
                for point in proposals:
                    if endpoint_tests >= 5:
                        break
                    endpoint_tests += 1
                    if move(arm, point):
                        destination = list(point)
                        break
                if destination is not None:
                    if move(arm, [x, y, level]):
                        chosen = (arm, destination)
                        break
                if endpoint_tests >= 5:
                    break
            if chosen is None:
                continue
            arm, destination = chosen
            if not move(arm, [x, y, contact]):
                continue
            manipulations += 1
            grip(arm, 0)
            if not move(arm, [x, y, level]):
                # Explicit zero execution leaves the tool at the original contact.
                grip(arm, 1)
                move(arm, [x, y, level])
                continue
            if not move(arm, destination):
                # This rejected carry did not execute. Restore only at the known
                # source support, never by opening at an arbitrary failure point.
                if not move(arm, [x, y, contact]):
                    return
                grip(arm, 1)
                move(arm, [x, y, level])
                continue
            grip(arm, 1)
            reservations.append((index, destination[0], destination[1], max(item['d'][:2])/2))
            # A reservation records a command, not verified delivery.
            if not move(arm, [destination[0], destination[1], level]):
                move(arm, [x, y, level])
    except Exception:
        # An exception may follow partial execution: preserve gripper state.
        return
