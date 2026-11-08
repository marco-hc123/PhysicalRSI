def policy(robot, memory):
    def normalize(q):
        n = sum(v*v for v in q) ** 0.5
        return [v/n for v in q] if n > 0.000001 else None

    quats = {
        'left': normalize([0.613, -0.3593, 0.6163, 0.3392]),
        'right': normalize([0.3814, -0.6197, 0.3785, 0.572])
    }
    budget = {'calls': 0, 'motions': 0, 'rejections': 0}

    def charge(motion=False):
        if budget['calls'] >= 94 or (motion and budget['motions'] >= 40):
            raise RuntimeError('Local execution bound')
        budget['calls'] += 1
        if motion:
            budget['motions'] += 1

    def move(arm, position):
        charge(True)
        result = robot.approach(arm=arm, position_m=list(position), quaternion_wxyz=quats[arm])
        if isinstance(result, dict) and result.get('primitive_error'):
            if result['primitive_error'] == 'no_collision_free_path':
                budget['rejections'] += 1
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

    def rotation(obj):
        w, x, y, z = normalize(obj['p'][3:7])
        return [[1-2*(y*y+z*z), 2*(x*y-w*z), 2*(x*z+w*y)],
                [2*(x*y+w*z), 1-2*(x*x+z*z), 2*(y*z-w*x)]]

    def basis(basket):
        r = rotation(basket)
        a, c = r[0][0], r[1][0]
        n = (a*a+c*c) ** 0.5
        if n < 0.5:
            raise RuntimeError('Unsupported basket orientation')
        return a/n, c/n

    def local_xy(x, y, basket):
        a, c = basis(basket)
        dx, dy = x-basket['p'][0], y-basket['p'][1]
        return a*dx+c*dy, -c*dx+a*dy

    def world_xy(lx, ly, basket):
        a, c = basis(basket)
        return basket['p'][0]+a*lx-c*ly, basket['p'][1]+c*lx+a*ly

    def inside(item, basket, margin=0.012):
        lx, ly = local_xy(item['p'][0], item['p'][1], basket)
        return abs(lx) < basket['d'][0]/2-margin and abs(ly) < basket['d'][1]/2-margin

    def target_candidates(item, basket, basket_index, current, reservations, arm):
        a, c = basis(basket)
        r = rotation(item)
        ex = sum(abs(a*r[0][k]+c*r[1][k])*item['d'][k]/2 for k in range(3))
        ey = sum(abs(-c*r[0][k]+a*r[1][k])*item['d'][k]/2 for k in range(3))
        ux, uy = basket['d'][0]/2-ex-0.008, basket['d'][1]/2-ey-0.008
        if ux < 0 or uy < 0:
            return []
        occupied = []
        for obj in current:
            if obj['category'] != 'basket' and inside(obj, basket, 0.0):
                lx, ly = local_xy(obj['p'][0], obj['p'][1], basket)
                occupied.append((lx, ly, max(obj['d'][:2])/2))
        occupied += [(lx, ly, radius) for i, lx, ly, radius in reservations if i == basket_index]
        radius = max(item['d'][:2])/2
        sign = -1 if arm == 'left' else 1
        # Feedback-informed relative seeds, clipped to perceived basket geometry.
        # Neither an offset nor a height is presumed reachable.
        seeds = [(-0.0175, -0.035, 1.01), (sign*0.065, -0.055, 0.99)]
        targets = []
        for dx, dy, height in seeds:
            sx, sy = a*dx+c*dy, -c*dx+a*dy
            sx = max(-ux, min(ux, sx))
            sy = max(-uy, min(uy, sy))
            points = [(sx, sy)]
            points += [(lx, ly) for lx in [-0.85*ux, 0.0, 0.85*ux]
                       for ly in [-0.85*uy, 0.0, 0.85*uy]]
            def loss(point):
                lx, ly = point
                crowding = sum(max(0.0, (radius+rr+0.008)**2-(lx-ox)**2-(ly-oy)**2)
                               for ox, oy, rr in occupied)
                return 8*crowding+(lx-sx)**2+(ly-sy)**2
            lx, ly = min(points, key=loss)
            tx, ty = world_xy(lx, ly, basket)
            targets.append(([tx, ty, height], lx, ly, radius))
        return targets

    try:
        initial = read_scene()
        anchors = sorted([o for o in initial if o['category'] == 'basket'],
                         key=lambda o: (o['p'][0], o['p'][1]))
        items = [o for o in initial if o['category'] != 'basket']
        categories = sorted(set(o['category'] for o in items))
        if not categories or not anchors or len(anchors) > 8 or len(categories) > len(anchors):
            return

        # Small exact assignment favors retaining existing placements, then short routes.
        costs = {}
        for category in categories:
            group = [o for o in items if o['category'] == category]
            for i, basket in enumerate(anchors):
                distances = [(o['p'][0]-basket['p'][0])**2+(o['p'][1]-basket['p'][1])**2 for o in group]
                costs[(category, i)] = (5*sum(not inside(o, basket) for o in group)
                                        + 0.5*sum(distances) + 0.5*max(distances))
        states = {0: (0.0, [])}
        for category in categories:
            following = {}
            for mask, entry in states.items():
                score, path = entry
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
        assignments = dict(zip(categories, min(states.values(), key=lambda e: e[0])[1]))

        # Both grippers must be explicitly open, including the otherwise unused arm.
        grip('left', 1)
        grip('right', 1)
        attempted, reservations = [], []
        active = None
        closures = 0
        current = initial

        for turn in range(10):
            if closures >= 7 or budget['rejections'] >= 10:
                return
            if turn:
                current = read_scene()
            if not current:
                return
            visible = [o for o in current if o['category'] == 'basket']
            pairs = []
            for i, anchor in enumerate(anchors):
                for j, basket in enumerate(visible):
                    distance = sum((anchor['p'][k]-basket['p'][k])**2 for k in [0, 1])
                    if distance <= 0.0064:
                        pairs.append((distance, i, j))
            matched, used = {}, set()
            for distance, i, j in sorted(pairs):
                if i not in matched and j not in used:
                    matched[i] = visible[j]
                    used.add(j)

            by_category = {}
            for index, item in enumerate(current):
                category = item['category']
                if category not in assignments or assignments[category] not in matched:
                    continue
                basket = matched[assignments[category]]
                if inside(item, basket):
                    continue
                x, y, z = item['p'][:3]
                prior = sum(weight for cat, px, py, weight in attempted
                            if cat == category and (x-px)**2+(y-py)**2 < 0.000625)
                if prior >= 2:
                    continue
                contact = max(0.92, z+0.125+(item['d'][2]/2 if prior == 0 else 0.0))
                hover = max(1.01, contact+0.045)
                if hover > 1.08:
                    continue
                distance = (x-basket['p'][0])**2+(y-basket['p'][1])**2
                entry = (prior, distance, index, item, basket, contact, hover)
                by_category.setdefault(category, []).append(entry)
            if not by_category:
                return
            if active not in by_category:
                def group_priority(category):
                    basket = matched[assignments[category]]
                    foreign = sum(o['category'] not in ['basket', category] and inside(o, basket)
                                  for o in current)
                    work = by_category[category]
                    return (len(work)+foreign, len(work), sum(e[1] for e in work), category)
                active = min(by_category, key=group_priority)
            entry = min(by_category[active], key=lambda e: (e[0], e[1], e[2]))
            prior, distance, index, item, basket, contact, hover = entry
            x, y = item['p'][:2]
            basket_index = assignments[active]
            preferred = 'left' if basket['p'][0] < 0 else 'right'
            alternate = 'right' if preferred == 'left' else 'left'
            selected = None

            # Test actual release endpoints while empty; never probe by holding an object.
            for arm in [preferred, alternate]:
                if budget['rejections'] >= 10:
                    break
                targets = target_candidates(item, basket, basket_index, current, reservations, arm)
                for target, lx, ly, radius in targets:
                    if budget['rejections'] >= 10:
                        break
                    if not move(arm, target):
                        continue
                    if move(arm, [x, y, hover]):
                        selected = (arm, target, lx, ly, radius)
                    break
                if selected is not None:
                    break
            if selected is None:
                attempted.append((active, x, y, 2))
                continue
            arm, target, lx, ly, radius = selected
            # Reserve enough local allowance for release or a source-supported rollback.
            if budget['calls']+9 > 94 or budget['motions']+5 > 40:
                return
            attempted.append((active, x, y, 1))
            if not move(arm, [x, y, contact]):
                continue
            grip(arm, 0)
            closures += 1
            if not move(arm, [x, y, hover]):
                # Explicit rejection left the tool at the original supported contact.
                grip(arm, 1)
                move(arm, [x, y, hover])
                continue
            if not move(arm, target):
                # No arbitrary release and no carrying-arm switch. The failed call
                # executed nothing, so lowering at the original source is bounded.
                if not move(arm, [x, y, contact]):
                    return
                grip(arm, 1)
                move(arm, [x, y, hover])
                continue
            grip(arm, 1)
            # This reserves a commanded site; it is not evidence of delivery.
            reservations.append((basket_index, lx, ly, radius))
            # Retreat to a previously accepted source hover, not an invented home.
            move(arm, [x, y, hover])
    except Exception:
        # Unknown partial execution: preserve commands, do not retry or release.
        return
