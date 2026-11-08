def policy(robot, memory):
    def category(key):
        if not isinstance(key, str):
            return None
        parts = key.rsplit('_', 1)
        if len(parts) != 2 or not parts[0] or not parts[1].isdigit():
            return None
        if int(parts[1]) < 1:
            return None
        return parts[0]

    def valid(obj):
        if not isinstance(obj, dict):
            return False
        p, d = obj.get('pose'), obj.get('dims')
        if not isinstance(p, (list, tuple)) or len(p) != 7:
            return False
        if not isinstance(d, (list, tuple)) or len(d) != 3:
            return False
        for value in p:
            if not isinstance(value, (int, float)) or not abs(value) < 10:
                return False
        for value in d:
            if not isinstance(value, (int, float)) or not 0 < value < 2:
                return False
        return True

    def observe():
        data = robot.scene()
        if not isinstance(data, dict) or not isinstance(data.get('objects'), dict):
            return None
        result = {}
        for key, obj in data['objects'].items():
            if category(key) is not None and valid(obj):
                result[key] = obj
        return result

    def normalized(q):
        n = sum(v * v for v in q) ** 0.5
        if n < 0.000001:
            return None
        return [v / n for v in q]

    def inside(obj, basket):
        p, b, d = obj['pose'], basket['pose'], basket['dims']
        q = normalized(b[3:7])
        if q is None:
            return False
        w, x, y, z = q
        dx, dy = p[0] - b[0], p[1] - b[1]
        local_x = (1 - 2 * (y*y + z*z)) * dx + 2 * (x*y + w*z) * dy
        local_y = 2 * (x*y - w*z) * dx + (1 - 2 * (x*x + z*z)) * dy
        return (abs(local_x) < max(0, d[0] / 2 - 0.008)
                and abs(local_y) < max(0, d[1] / 2 - 0.008)
                and abs(p[2] - b[2]) < d[2] / 2 + obj['dims'][2] / 2 + 0.04)

    quats = {
        'left': normalized([0.613, -0.3593, 0.6163, 0.3392]),
        'right': normalized([0.3814, -0.6197, 0.3785, 0.572])
    }
    try:
        objects = observe()
    except Exception:
        return
    if not objects:
        return

    baskets = {}
    groups = {}
    for key, obj in objects.items():
        cat = category(key)
        if cat == 'basket':
            baskets[key] = obj
        else:
            groups.setdefault(cat, []).append(obj)
    if not groups or len(groups) > len(baskets):
        return
    if sum(len(items) for items in groups.values()) > 16:
        return

    # Reserve existing category/basket associations before allocating empty baskets.
    assignment = {}
    available = set(baskets)
    pairs = []
    for cat in sorted(groups):
        for bk in sorted(baskets):
            count = sum(1 for obj in groups[cat] if inside(obj, baskets[bk]))
            if count:
                pairs.append((-count, cat, bk))
    for negative_count, cat, bk in sorted(pairs):
        if cat not in assignment and bk in available:
            assignment[cat] = bk
            available.remove(bk)

    # Allocate remaining categories by observed transport distance, without sharing.
    distances = []
    for cat in sorted(groups):
        if cat in assignment:
            continue
        cx = sum(obj['pose'][0] for obj in groups[cat]) / len(groups[cat])
        cy = sum(obj['pose'][1] for obj in groups[cat]) / len(groups[cat])
        for bk in sorted(available):
            bp = baskets[bk]['pose']
            distances.append(((cx-bp[0])**2 + (cy-bp[1])**2, cat, bk))
    for distance, cat, bk in sorted(distances):
        if cat not in assignment and bk in available:
            assignment[cat] = bk
            available.remove(bk)
    if len(assignment) != len(groups):
        return

    # Snapshot spatial targets, not adapter instance identities. Each gets one attempt.
    targets = []
    for cat in sorted(groups):
        bk = assignment[cat]
        for obj in groups[cat]:
            if not inside(obj, baskets[bk]):
                p, b = obj['pose'], baskets[bk]['pose']
                distance = (p[0]-b[0])**2 + (p[1]-b[1])**2
                targets.append((distance, cat, p[0], p[1], p[2]))
    targets.sort()
    opened = {'left': False, 'right': False}

    for distance, cat, ox, oy, oz in targets:
        try:
            current = observe()
        except Exception:
            return
        if current is None:
            return
        bk = assignment[cat]
        if bk not in current or category(bk) != 'basket':
            return
        basket = current[bk]
        candidates = []
        for key, obj in current.items():
            if category(key) != cat:
                continue
            p = obj['pose']
            delta = (p[0]-ox)**2 + (p[1]-oy)**2 + (p[2]-oz)**2
            if delta < 0.035**2:
                candidates.append((delta, key))
        if not candidates:
            continue
        candidates.sort()
        if len(candidates) > 1 and candidates[1][0] - candidates[0][0] < 0.0001:
            return
        obj = current[candidates[0][1]]
        if inside(obj, basket):
            continue
        p, bp = obj['pose'], basket['pose']
        arm = 'left' if p[0] + bp[0] < 0 else 'right'
        q = quats[arm]
        # Contact offset is above the object's center, not above its top surface.
        contact_z = max(0.92, p[2] + 0.125)
        clearance_z = max(1.01, contact_z + 0.045)
        if clearance_z > 1.10:
            return
        try:
            if not opened[arm]:
                robot.gripper(arm=arm, command=1)
                opened[arm] = True
            robot.approach(arm=arm, position_m=[p[0], p[1], clearance_z], quaternion_wxyz=q)
            robot.approach(arm=arm, position_m=[p[0], p[1], contact_z], quaternion_wxyz=q)
            robot.gripper(arm=arm, command=0)
            opened[arm] = False
            robot.approach(arm=arm, position_m=[p[0], p[1], clearance_z], quaternion_wxyz=q)
            robot.approach(arm=arm, position_m=[bp[0], bp[1], 1.01], quaternion_wxyz=q)
            robot.gripper(arm=arm, command=1)
            opened[arm] = True
        except Exception:
            # In particular, never open at an arbitrary location after a failed lift.
            # No alternative grasp, arm, or transport is attempted under uncertainty.
            return
