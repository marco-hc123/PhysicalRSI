def policy(robot, memory):
    def category(key):
        parts = key.rsplit('_', 1)
        if len(parts) != 2 or not parts[1].isdigit() or int(parts[1]) < 1:
            return None
        return parts[0]

    def valid(obj):
        if not isinstance(obj, dict):
            return False
        p, d = obj.get('pose', []), obj.get('dims', [])
        return len(p) == 7 and len(d) == 3 and all(isinstance(v, (int, float)) and v == v and abs(v) < 100 for v in p + d) and all(v > 0 for v in d)

    def inside(obj, basket):
        p, b = obj['pose'], basket['pose']
        q = b[3:7]
        n = sum(v*v for v in q) ** 0.5
        if n < 0.000001:
            return False
        w, x, y, z = [v/n for v in q]
        dx, dy = p[0]-b[0], p[1]-b[1]
        local_x = (1-2*(y*y+z*z))*dx + 2*(x*y+w*z)*dy
        local_y = 2*(x*y-w*z)*dx + (1-2*(x*x+z*z))*dy
        return abs(local_x) < max(0, basket['dims'][0]/2-0.012) and abs(local_y) < max(0, basket['dims'][1]/2-0.012) and abs(p[2]-b[2]) < basket['dims'][2]+0.04

    quats = {'left': [0.613, -0.3593, 0.6163, 0.3392], 'right': [0.3814, -0.6197, 0.3785, 0.572]}
    for arm in quats:
        n = sum(v*v for v in quats[arm]) ** 0.5
        quats[arm] = [v/n for v in quats[arm]]

    try:
        initial = robot.scene().get('objects', {})
        baskets = {}
        groups = {}
        for key, obj in initial.items():
            cat = category(key)
            if cat is None or not valid(obj):
                return
            if cat == 'basket':
                baskets[key] = obj
            else:
                groups.setdefault(cat, []).append(obj)
        if not groups or len(groups) > len(baskets):
            return

        assignment = {}
        occupied = {}
        for cat in sorted(groups):
            found = set()
            for obj in groups[cat]:
                for key, basket in baskets.items():
                    if inside(obj, basket):
                        found.add(key)
            if len(found) > 1:
                return
            if found:
                key = next(iter(found))
                if key in occupied and occupied[key] != cat:
                    return
                assignment[cat] = key
                occupied[key] = cat

        remaining = [cat for cat in groups if cat not in assignment]
        remaining.sort(key=lambda cat: sum(o['pose'][0] for o in groups[cat])/len(groups[cat]))
        available = [key for key in baskets if key not in occupied]
        available.sort(key=lambda key: baskets[key]['pose'][0])
        for i, cat in enumerate(remaining):
            assignment[cat] = available[i]

        # Spatial attempt records do not assume persistent instance suffixes.
        attempted = []
        for turn in range(8):
            objects = initial if turn == 0 else robot.scene().get('objects', {})
            live_baskets = {}
            for key in baskets:
                if key not in objects or not valid(objects[key]):
                    return
                live_baskets[key] = objects[key]
            candidates = []
            for key, obj in objects.items():
                cat = category(key)
                if cat == 'basket':
                    continue
                if cat not in assignment or not valid(obj):
                    return
                p = obj['pose']
                if inside(obj, live_baskets[assignment[cat]]):
                    continue
                if any(cat == oldcat and (p[0]-ox)**2+(p[1]-oy)**2 < 0.0049 for oldcat, ox, oy in attempted):
                    continue
                target = live_baskets[assignment[cat]]['pose']
                distance = (p[0]-target[0])**2+(p[1]-target[1])**2
                candidates.append((distance, key, cat, obj))
            if not candidates:
                return
            candidates.sort(key=lambda item: (item[0], item[1]))
            _, key, cat, obj = candidates[0]
            x, y, z = obj['pose'][:3]
            attempted.append((cat, x, y))
            target = live_baskets[assignment[cat]]['pose']
            arm = 'left' if x + target[0] < 0 else 'right'
            q = quats[arm]
            contact_z = max(0.92, z + 0.125)
            clearance_z = max(1.01, contact_z + 0.045)
            if clearance_z > 1.09:
                return
            robot.gripper(arm=arm, command=1)
            robot.approach(arm=arm, position_m=[x, y, clearance_z], quaternion_wxyz=q)
            robot.approach(arm=arm, position_m=[x, y, contact_z], quaternion_wxyz=q)
            robot.gripper(arm=arm, command=0)
            robot.approach(arm=arm, position_m=[x, y, clearance_z], quaternion_wxyz=q)
            robot.approach(arm=arm, position_m=[target[0], target[1], 1.01], quaternion_wxyz=q)
            robot.gripper(arm=arm, command=1)
    except Exception:
        # A failed trajectory or uncertain RPC must not trigger another grasp
        # or an uncontrolled release at an intermediate location.
        return
