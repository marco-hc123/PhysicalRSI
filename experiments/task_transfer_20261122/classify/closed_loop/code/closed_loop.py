"""Closed-loop additions to the frozen C3 grasp and original basket assignment."""
import numpy as np


def retreat_path(sample, current, initial):
    path = sample(current, [initial], max_step=.12)[1:]
    if len(path) > 30:
        return []
    return path


def neighbor(record, cat, xy):
    return record['category'] == cat and sum((a-b)**2 for a,b in zip(record['xy'],xy)) < .0016


def unavailable(records, cat, xy):
    nearby = [r for r in records if neighbor(r,cat,xy)]
    return len(nearby) >= 2 or any(r['deposited'] and r.get('ee_at_basket',0) >= .020 for r in nearby)


def assignments_now(current, baskets, assigned, inside):
    items = [o for o in current if o['category'] != 'basket']
    visible = sorted((o for o in current if o['category']=='basket'),key=lambda o:tuple(o['p'][:2]))
    def dist(a,b):
        return sum((a['p'][i]-b['p'][i])**2 for i in (0,1))
    available = {}
    for b in visible:
        indices = [i for i, ref in enumerate(baskets) if dist(ref,b)<.0025]
        if not indices:
            indices = [len(baskets)]
            baskets.append(b)
        if len(indices)==1 and indices[0] not in assigned.values():
            available[indices[0]] = b
    pending = {o['category'] for o in items} - set(assigned)
    added = {}
    empty = {}
    for i,b in sorted(available.items()):
        occupants = {o['category'] for o in items if inside(o,b)}
        if not occupants:
            empty[i] = b
        elif len(occupants)==1 and occupants <= pending:
            cat = occupants.pop()
            added[cat] = assigned[cat] = i
            pending.remove(cat)
    while empty and pending:
        options=[]
        for cat in pending:
            group = [o for o in items if o['category']==cat]
            for i,b in empty.items():
                options.append((sum(dist(o,b) for o in group)/len(group),cat,i))
        _,cat,i = min(options)
        added[cat] = assigned[cat] = i
        pending.remove(cat)
        del empty[i]
    return added


def depth_c7(cloud, point, base):
    distance=np.linalg.norm(cloud[:,:2]-point[:2],axis=1)
    local=cloud[distance<=.015]
    if len(local)<15:
        local=cloud[distance<=.025]
    if len(local)<15:
        return base
    top=float(np.percentile(local[:,2],90))
    h=max(0.,top-.765)
    if h>=.025:
        return base
    return float(np.clip(.765+.50*h,.777,max(.777,top-.006)))


def grasp(session, variant, item, basket, quats):
    from policies import migrated_turn
    if variant=='C6':
        result=migrated_turn(session,'C3',item,basket,quats)
        if session.record['deposited']:
            session.retreat(session.record['arm'])
        return result

    import teacher_kin as kin
    import grasp_geometry as geom
    from pickup_modules import preclose
    from visual_scene import cloud_for
    s=session
    bx,by=basket['p'][:2]
    cat=item['category']
    xy=item['p'][:2]
    src=s.target_instance(cat,xy)
    cloud,counts=cloud_for(src,s.views) if src else (None,{})
    if cloud is None:
        s.record.update(stop='selected_instance_cloud_missing',cloud_points_by_camera=counts)
        return False
    point,minor,ratio,fb=geom.target(cloud,'T3')
    z,zfb=geom.depth(cloud,point,'Z2')
    z=depth_c7(cloud,point,z)
    # Retry the same public target with the requested depth change only.
    for attempt in range(2):
        if attempt:
            s.begin(cat,xy,basket['p'][:2],retry=True)
            z=max(.776,z-.004)
        tcp=np.r_[point[:2],z]
        s.record.update(rule='T3',cloud_points_by_camera=counts,axis_ratio=float(ratio),
                        target_fallback=bool(fb),depth_fallback=bool(zfb),tcp_goal=tcp.tolist())
        preferred='left' if xy[0]+bx<0 else 'right'
        for arm in (preferred,'right' if preferred=='left' else 'left'):
            rot,choice,_=geom.poses(arm,tcp,minor,ratio,'Y1',s.joints(arm))
            quat=list(map(float,kin.quat_wxyz(rot)))
            wrist,_=geom.goals(tcp,rot)
            clearance=max(1.02,float(wrist[2])+.08)
            if s.move('approach',arm,[*wrist[:2],clearance],quat):
                break
        else:
            s.record['stop']='approach_plans_rejected'
            return True
        s.record.update(arm=arm,yaw=choice)
        s.grip('open',arm,1)
        if not s.move('contact',arm,wrist,quat):
            s.record['stop']='contact_plan_rejected'
            return False
        s.phase='preclose'
        preclose(arm,wrist,quat,s.joints,s.correct,lambda row:s.record.update(preclose=row))
        s.steady_close(arm)
        s.record['ee_before_lift']=s.opening(arm)
        if not (s.move('lift',arm,[*wrist[:2],wrist[2]+.03],quat,slow=True)
                and s.move('lift',arm,[*wrist[:2],clearance],quat)):
            s.record['stop']='lift_plan_rejected'
            return False
        s.after_lift(arm)
        if s.opening(arm)<.012:
            s.record.update(vetoed=True,stop='vetoed_empty_transport')
            s.release_for_next(arm)
            if sum(neighbor(r,cat,xy) for r in s.records)==1:
                continue
            s.retreat(arm)
            return True
        off=-.065 if arm=='left' else .065
        dests=([[bx+off,by-.035,.99],[bx+off,by-.055,.99]] if abs(bx)<.1
               else [[bx-.015,by-.015,1.00],[bx-.0175,by-.035,1.01]])
        for i,dest in enumerate(dests):
            if s.move('transport',arm,dest,quats[arm]):
                s.record.update(ee_at_basket=s.opening(arm),destination=i+1)
                s.grip('deposit',arm,1)
                s.record.update(deposited=True,stop='deposited')
                s.retreat(arm)
                return True
        s.record['stop']='drop_plans_rejected'
        return False
