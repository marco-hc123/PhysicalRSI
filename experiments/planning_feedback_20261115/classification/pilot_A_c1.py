def policy(robot, memory):
    def normalize(q):
        n = sum(v*v for v in q) ** 0.5
        return [v/n for v in q] if n > 0.000001 else None

    quats = {
        'left': normalize([0.613, -0.3593, 0.6163, 0.3392]),
        'right': normalize([0.3814, -0.6197, 0.3785, 0.572])
    }
    commanded = {}

    def checked(result):
        if isinstance(result, dict) and result.get('primitive_error'):
            raise RuntimeError('Uncertain execution')
        return result

    def move(arm, p, q):
        result = robot.approach(arm=arm, position_m=p, quaternion_wxyz=q)
        if isinstance(result, dict) and result.get('primitive_error'):
            if result['primitive_error'] == 'no_collision_free_path':
                return False
            raise RuntimeError('Uncertain execution')
        commanded[arm] = [list(p), list(q)]
        return True

    def grip(arm, command):
        checked(robot.gripper(arm=arm, command=command))

    def joints(arm):
        result = checked(robot.reobserve())
        values = result.get('state', {}).get(arm + '_arm_joint_state', [])
        if len(values) != 6:
            raise RuntimeError('Missing joint observation')
        if not all(isinstance(v, (int, float)) and v == v and abs(v) < 20 for v in values):
            raise RuntimeError('Invalid joint observation')
        return list(values)

    def read_scene():
        data = checked(robot.scene())
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
            if not all(isinstance(v, (int, float)) and v == v and abs(v) < 10 for v in list(p) + list(d)):
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

    def rotate(q, axis, angle):
        r = [1.0, 0.0, 0.0, 0.0]
        r[axis+1] = angle/2
        a, b, c, d = r
        w, x, y, z = q
        return normalize([a*w-b*x-c*y-d*z, a*x+b*w+c*z-d*y, a*y-b*z+c*w+d*x, a*z+b*y-c*x+d*w])

    def allowed_return_pose(p):
        return abs(p[0]) < 0.8 and -0.7 < p[1] < 0.35 and 0.94 <= p[2] <= 1.5

    def return_toward_origin(arm, target):
        # Experimental local Cartesian inverse control using observed joints.
        # Commanded poses are references, not measured Cartesian endpoints.
        previous_cost = None
        for iteration in range(6):
            p, q = commanded[arm]
            base = joints(arm)
            error = [target[i]-base[i] for i in range(6)]
            cost = sum(v*v for v in error)
            if cost < 0.01:
                return
            if previous_cost is not None and cost > previous_cost*1.4:
                return
            previous_cost = cost
            columns = []
            for axis in range(6):
                pp, qq = list(p), list(q)
                step = 0.012 if axis < 3 else 0.035
                if axis < 3:
                    pp[axis] += step
                else:
                    qq = rotate(q, axis-3, step)
                if not allowed_return_pose(pp) or not move(arm, pp, qq):
                    return
                observed = joints(arm)
                columns.append([(observed[i]-base[i])/step for i in range(6)])
            rows = []
            for i in range(6):
                row = []
                for j in range(6):
                    value = sum(columns[i][k]*columns[j][k] for k in range(6))
                    row.append(value + (0.02 if i == j else 0.0))
                row.append(sum(columns[i][k]*error[k] for k in range(6)))
                rows.append(row)
            for i in range(6):
                pivot = i
                for j in range(i+1, 6):
                    if abs(rows[j][i]) > abs(rows[pivot][i]):
                        pivot = j
                rows[i], rows[pivot] = rows[pivot], rows[i]
                divisor = rows[i][i]
                if abs(divisor) < 0.00000001:
                    return
                rows[i] = [v/divisor for v in rows[i]]
                for j in range(6):
                    if j != i:
                        factor = rows[j][i]
                        rows[j] = [rows[j][k]-factor*rows[i][k] for k in range(7)]
            delta = [rows[i][6] for i in range(6)]
            if not all(v == v and abs(v) < 100 for v in delta):
                return
            scale = max([1.0] + [abs(delta[i])/0.08 for i in range(3)] + [abs(delta[i])/0.3 for i in range(3, 6)])
            delta = [v/scale for v in delta]
            pp = [p[i]+delta[i] for i in range(3)]
            qq = list(q)
            for axis in range(3):
                qq = rotate(qq, axis, delta[axis+3])
            if not allowed_return_pose(pp) or not move(arm, pp, qq):
                return

    try:
        origins = {'left': joints('left'), 'right': joints('right')}
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
                break
            choices.sort(key=lambda entry: entry[0])
            _, item, basket = choices[0]
            x, y, z = item['p'][:3]
            bx, by = basket['p'][:2]
            attempted.append((item['category'], x, y))
            contact_z = max(0.92, z + item['d'][2]/2 + 0.125)
            clearance_z = max(1.06, contact_z + 0.045)
            if clearance_z > 1.08:
                return
            preferred = 'left' if x+bx < 0 else 'right'
            alternate = 'right' if preferred == 'left' else 'left'
            arm = None
            for candidate in [preferred, alternate]:
                if move(candidate, [x, y, clearance_z], quats[candidate]):
                    arm = candidate
                    break
            if arm is None:
                continue
            q = quats[arm]
            grip(arm, 1)
            if not move(arm, [x, y, contact_z], q):
                return
            grip(arm, 0)
            if not move(arm, [x, y, clearance_z], q):
                return
            # Cross the rim at clearance, then release above the basket center.
            if not move(arm, [bx, by, clearance_z], q):
                return
            if not move(arm, [bx, by, 1.01], q):
                return
            grip(arm, 1)
            if not move(arm, [bx, by, clearance_z], q):
                return
            # Withdraw before selecting another object from RGB observations.
            park = [-0.25 if arm == 'left' else 0.25, -0.30, clearance_z]
            if not move(arm, park, q):
                return

        # Disappearance does not establish delivery. This attempts endpoint
        # return without declaring that classification or return succeeded.
        for arm in ['left', 'right']:
            if arm in commanded:
                grip(arm, 1)
                return_toward_origin(arm, origins[arm])
    except Exception:
        # No observation or action follows uncertain execution.
        return
