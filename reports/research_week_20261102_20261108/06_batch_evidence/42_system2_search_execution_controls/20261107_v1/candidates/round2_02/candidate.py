def policy(robot, memory):
    calls = 0
    limit = 96

    def normalize(q):
        n = sum(v*v for v in q) ** 0.5
        return [v/n for v in q] if n > 0.000001 else None

    quats = {
        'left': normalize([0.613, -0.3593, 0.6163, 0.3392]),
        'right': normalize([0.3814, -0.6197, 0.3785, 0.572])
    }

    def invoke(method, **kwargs):
        nonlocal calls
        if calls >= limit:
            raise RuntimeError('Local RPC limit')
        calls += 1
        if method == 'scene':
            result = robot.scene()
        elif method == 'approach':
            result = robot.approach(**kwargs)
        else:
            result = robot.gripper(**kwargs)
        if isinstance(result, dict) and result.get('primitive_error'):
            if method == 'approach' and result['primitive_error'] == 'no_collision_free_path':
                return False
            raise RuntimeError('Uncertain primitive execution')
        return result

    def move(arm, position):
        result = invoke('approach', arm=arm, position_m=list(position),
                        quaternion_wxyz=quats[arm])
        return result is not False

    def grip(arm, command):
        invoke('gripper', arm=arm, command=command)

    def read_scene():
        data = invoke('scene')
        if not isinstance(data, dict) or not isinstance(data.get('objects'), dict):
            raise RuntimeError('Perception unavailable')
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
            if not all(isinstance(v, (int, float)) and v == v and abs(v) < 10
                       for v in list(p) + list(d)):
                continue
            if not all(v > 0 for v in d) or normalize(p[3:7]) is None:
                continue
            result.append({'category': category, 'p': list(p), 'd': list(d)})
        return result

    def basis(obj):
        w, x, y, z = normalize(obj['p'][3:7])
        return (1-2*(y*y+z*z), 2*(x*y-w*z),
                2*(x*y+w*z), 1-2*(x*x+z*z))

    def inside(item, basket, margin=0.014):
        a, b, c, d = basis(basket)
        dx = item['p'][0] - basket['p'][0]
        dy = item['p'][1] - basket['p'][1]
        lx, ly = a*dx+c*dy, b*dx+d*dy
        return (abs(lx) < basket['d'][0]/2-margin and
                abs(ly) < basket['d'][1]/2-margin)

    def distance2(one, two):
        return sum((one['p'][k]-two['p'][k])**2 for k in [0, 1])

    def release_candidates(item, basket, arm, current, reservations, index):
        a, b, c, d = basis(basket)
        radius = max(item['d'][0], item['d'][1])/2
        ux = basket['d'][0]/2-radius-0.012
        uy = basket['d'][1]/2-radius-0.012
        if ux <= 0 or uy <= 0:
            return []
        ux, uy = 0.94*ux, 0.94*uy
        bx, by = basket['p'][:2]
        sign = -1.0 if arm == 'left' else 1.0
        world_half_x = (abs(a)*basket['d'][0]+abs(b)*basket['d'][1])/2
        straddles_midline = abs(bx) <= world_half_x

        # The supplied offset intervention is a prior, not an assumed feasible endpoint.
        dx = sign*0.065 if straddles_midline else -0.0175
        dy = -0.055 if straddles_midline else -0.035
        lx = max(-ux, min(ux, a*dx+c*dy))
        ly = max(-uy, min(uy, b*dx+d*dy))
        raw = [(lx, ly), (-ux, -uy), (ux, -uy),
               (-ux, uy), (ux, uy), (0.0, -uy), (0.0, 0.0)]
        occupied = [(o['p'][0], o['p'][1], max(o['d'][0], o['d'][1])/2)
                    for o in current if o['category'] != 'basket' and inside(o, basket, 0.0)]
        occupied += [(x, y, r) for i, x, y, r in reservations if i == index]
        ranked, seen = [], []
        for order, (lx, ly) in enumerate(raw):
            tx, ty = bx+a*lx+b*ly, by+c*lx+d*ly
            if any((tx-x)**2+(ty-y)**2 < 0.000025 for x, y in seen):
                continue
            seen.append((tx, ty))
            overlap = sum(max(0.0, (radius+r+0.012)**2-(tx-x)**2-(ty-y)**2)
                          for x, y, r in occupied)
            front_cost = max(0.0, ty-by)
            side_cost = max(0.0, -sign*(tx-bx))
            score = 20.0*overlap + 0.02*front_cost + 0.01*side_cost + 0.0001*order
            ranked.append((score, order, tx, ty))
        ranked.sort(key=lambda entry: (entry[0], entry[1]))
        points = [(entry[2], entry[3]) for entry in ranked[:3]]
        if not points:
            return []
        if straddles_midline:
            # Test the modest lower release endpoint before trying another altitude.
            candidates = [[points[0][0], points[0][1], 0.99],
                          [points[0][0], points[0][1], 1.01]]
            if len(points) > 1:
                candidates.append([points[1][0], points[1][1], 0.99])
            return candidates
        return [[x, y, 1.01] for x, y in points]

    try:
        initial = read_scene()
        anchors = sorted([o for o in initial if o['category'] == 'basket'],
                         key=lambda o: (o['p'][0], o['p'][1]))
        items = [o for o in initial if o['category'] != 'basket']
        categories = sorted(set(o['category'] for o in items))
        if not anchors or len(anchors) > 8 or len(categories) > len(anchors):
            return
        grip('left', 1)
        grip('right', 1)
        if not categories:
            return

        # Exact bounded assignment: preserve existing occupants first, then reduce
        # distance and cross-body transfers. Category names carry no basket identity.
        costs = {}
        for category in categories:
            group = [o for o in items if o['category'] == category]
            for i, basket in enumerate(anchors):
                cost = 0.0
                for obj in group:
                    dist = distance2(obj, basket)
                    if inside(obj, basket):
                        cost += 0.001*dist
                    else:
                        crosses = obj['p'][0]*basket['p'][0] < -0.01
                        cost += 1.0 + 0.5*dist + (0.18 if crosses else 0.0)
                costs[(category, i)] = cost
        states = {0: (0.0, [])}
        for category in categories:
            following = {}
            for mask, (cost, path) in states.items():
                for i in range(len(anchors)):
                    if mask & (1 << i):
                        continue
                    new_mask = mask | (1 << i)
                    value = cost + costs[(category, i)]
                    if new_mask not in following or value < following[new_mask][0]:
                        following[new_mask] = (value, path+[i])
            states = following
        if not states:
            return
        assignment = dict(zip(categories, min(states.values(), key=lambda e: e[0])[1]))
        attempts, reservations = [], []
        active_category = None
        current = initial

        for turn in range(8):
            # Leave enough RPC capacity for bounded precontact checks and rollback.
            if limit-calls < 20:
                return
            if turn:
                current = read_scene()
            visible = [o for o in current if o['category'] == 'basket']
            pairs = []
            for i, anchor in enumerate(anchors):
                for j, basket in enumerate(visible):
                    dist = distance2(anchor, basket)
                    if dist <= 0.0064:
                        pairs.append((dist, i, j))
            matched, used = {}, set()
            for dist, i, j in sorted(pairs):
                if i not in matched and j not in used:
                    matched[i] = visible[j]
                    used.add(j)

            choices, remaining = [], {}
            for order, item in enumerate(current):
                category = item['category']
                if category not in assignment:
                    continue
                index = assignment[category]
                if index not in matched:
                    continue
                basket = matched[index]
                if inside(item, basket):
                    continue
                remaining[category] = remaining.get(category, 0)+1
                x, y, z = item['p'][:3]
                prior = sum(1 for cat, px, py in attempts
                            if cat == category and (x-px)**2+(y-py)**2 < 0.000625)
                if prior >= 2:
                    continue
                contact = max(0.92, z+item['d'][2]/2+0.125)
                clearance = max(1.01, contact+0.055)
                if clearance > 1.08:
                    continue
                choices.append((prior, distance2(item, basket), order, item,
                                basket, index, contact, clearance))
            if not choices:
                return
            available = set(entry[3]['category'] for entry in choices)
            if active_category not in available:
                active_category = min(available,
                                      key=lambda cat: (remaining.get(cat, 100),
                                                       min(e[1] for e in choices if e[3]['category'] == cat),
                                                       cat))
            eligible = [e for e in choices if e[3]['category'] == active_category]
            prior, dist, order, item, basket, index, contact, clearance = min(
                eligible, key=lambda e: (e[0], e[1], e[2]))
            x, y = item['p'][:2]
            attempts.append((item['category'], x, y))
            source_high = [x, y, clearance]
            source_contact = [x, y, contact]
            a, b, c, d = basis(basket)
            half_x = (abs(a)*basket['d'][0]+abs(b)*basket['d'][1])/2
            if abs(basket['p'][0]) <= half_x:
                preferred = 'left' if x < 0 else 'right'
            else:
                preferred = 'left' if basket['p'][0] < 0 else 'right'
            alternate = 'right' if preferred == 'left' else 'left'
            arm, destination = None, None

            # All destination feasibility checks occur with open grippers, before
            # contact. These are real motions, not a fabricated planning query.
            for candidate_arm in [preferred, alternate]:
                destinations = release_candidates(item, basket, candidate_arm,
                                                  current, reservations, index)
                if not destinations:
                    continue
                if not move(candidate_arm, source_high):
                    continue
                for target in destinations[:3]:
                    if limit-calls < 12:
                        return
                    if not move(candidate_arm, target):
                        continue
                    if not move(candidate_arm, source_high):
                        # Explicit rejection leaves the open arm at the tested site.
                        return
                    arm, destination = candidate_arm, target
                    break
                if arm is not None:
                    break
            if arm is None:
                attempts.append((item['category'], x, y))
                active_category = None
                continue
            if limit-calls < 10:
                return

            if not move(arm, source_contact):
                # No contact motion executed; both grippers are still open.
                active_category = None
                continue
            grip(arm, 0)
            if not move(arm, source_high):
                # Zero execution leaves the tool at its original contact site.
                grip(arm, 1)
                return
            if not move(arm, destination):
                # Do not escalate height or change arms while potentially holding.
                # The failed call executed nothing: return to the original support.
                if not move(arm, source_contact):
                    return
                grip(arm, 1)
                if not move(arm, source_high):
                    return
                attempts.append((item['category'], x, y))
                active_category = None
                continue
            grip(arm, 1)
            reservations.append((index, destination[0], destination[1],
                                 max(item['d'][0], item['d'][1])/2))
            # Retreat along the previously traversed source/site connection rather
            # than assuming an upward basket endpoint is feasible.
            if not move(arm, source_high):
                return
            # A completed release sequence permits another observation, but is not
            # evidence of grasp retention, category completion, or native success.
    except Exception:
        # Uncertain execution: preserve the last explicit gripper commands.
        return
