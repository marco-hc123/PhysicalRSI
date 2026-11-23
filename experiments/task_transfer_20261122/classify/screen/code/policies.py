"""Frozen variants. Keep the parent matching and object-ordering code byte-identical."""
import ast
from pathlib import Path
import numpy as np
import teacher_kin as kin
import grasp_geometry as geometry
from pickup_modules import preclose
from visual_scene import cloud_for

def build_sources(batch):
    dst=batch/'policies';dst.mkdir(exist_ok=True)
    text=(batch/'inputs/baseline/classify_objects.py').read_text()
    marker='            contact_z = max(0.92,'
    assert text.count(marker)==1
    prefix=text[:text.index(marker)]
    suffix=text[text.index('    except Exception:'):]
    for i in range(6):
        source=text if i==0 else prefix+f"            if not robot.migrated_turn('C{i}', item, basket, quats):\n                return\n"+suffix
        ast.parse(source)
        (dst/f'C{i}.py').write_text(source)
    assert (dst/'C0.py').read_bytes()==(batch/'inputs/baseline/classify_objects.py').read_bytes()

def migrated_turn(s,v,item,basket,quats):
    guard=v in ('C4','C5')
    yaw='Y0' if v=='C1' else 'Y1'
    dyn=v in ('C3','C4','C5')
    bx,by=basket['p'][:2];category=item['category']
    src=s.target_instance(category,item['p'][:2])
    b=s.target_instance('basket',(bx,by))
    drop_xy=np.array([bx,by])
    if guard and b:
        pts,_=cloud_for(b,s.views)
        if pts is not None:
            measured=np.percentile(pts[:,:2],[2,98],axis=0).mean(axis=0)
            drop_xy+=np.clip(measured-drop_xy,[-.025,-.02],[.025,.02])
    for attempt in range(1,3 if v=='C5' else 2):
        if attempt==2:
            s.scene()
            src=s.target_instance(category,item['p'][:2],max_distance=.09)
            if src is None:
                s.record['stop']='same_item_not_relocalized'
                return True
            s.begin(category,src['xyz'][:2],basket['p'][:2],retry=True)
        cloud,counts=cloud_for(src,s.views) if src else (None,{})
        s.record['cloud_points_by_camera']=counts
        if cloud is None:
            s.record['stop']='selected_instance_cloud_missing'
            return guard
        point,minor,ratio,fb=geometry.target(cloud,'T3')
        rule='T3'
        if v=='C5' and ratio<1.8:
            rule='T0';point,minor,ratio,fb=geometry.target(cloud,rule)
        z,zfb=geometry.depth(cloud,point,'Z2')
        tcp=np.r_[point[:2],z]
        s.record.update(rule=rule,axis_ratio=float(ratio),target_fallback=bool(fb),depth_fallback=bool(zfb),tcp_goal=tcp.tolist())
        preferred='left' if item['p'][0]+bx<0 else 'right'
        for arm in [preferred,'right' if preferred=='left' else 'left']:
            rot,choice,_=geometry.poses(arm,tcp,minor,ratio,yaw,s.joints(arm))
            quat=list(map(float,kin.quat_wxyz(rot)))
            wrist,_=geometry.goals(tcp,rot)
            clearance=max(1.02,float(wrist[2])+.08)
            if s.move('approach',arm,[*wrist[:2],clearance],quat):break
        else:
            s.record['stop']='approach_plans_rejected'
            # The parent already continues after both approaches are rejected.
            return True
        s.record.update(arm=arm,yaw=choice)
        s.grip('open',arm,1)
        if not s.move('contact',arm,wrist,quat):
            s.record['stop']='contact_plan_rejected'
            if guard:s.release_for_next(arm)
            return guard
        s.phase='preclose'
        preclose(arm,wrist,quat,s.joints,s.correct,lambda row:s.record.update(preclose=row))
        if dyn:s.steady_close(arm)
        else:s.grip('close',arm,0)
        s.record['ee_before_lift']=s.opening(arm)
        lifted=True
        if dyn:lifted=s.move('lift',arm,[*wrist[:2],wrist[2]+.03],quat,slow=True)
        if lifted:lifted=s.move('lift',arm,[*wrist[:2],clearance],quat)
        if not lifted and v=='C5':
            base=np.array([-.30 if arm=='left' else .30,-.45])
            dv=base-wrist[:2]
            inward=wrist[:2]+.02*dv/max(np.linalg.norm(dv),1.e-9)
            s.record['inward_recovery']=True
            lifted=s.move('lift',arm,[*inward,clearance],quat,slow=True)
        if not lifted:
            s.record['stop']='lift_plan_rejected'
            if guard:s.release_for_next(arm)
            return guard
        s.after_lift(arm)
        if guard and s.opening(arm)<.015:
            s.record.update(vetoed=True,stop='vetoed_empty_transport')
            s.release_for_next(arm)
            if v=='C5' and attempt==1:continue
            return True
        if guard:
            dx,dy=drop_xy
            dests=[[dx-.015,dy-.035,1.01],[dx+(-.045 if arm=='left' else .045),dy-.045,.99],[dx,dy-.025,1.02]]
        else:
            dests=[[bx+(-.065 if arm=='left' else .065),by-.055,.99] if abs(bx)<.1 else [bx-.0175,by-.035,1.01]]
        for dest in dests:
            if s.move('transport',arm,dest,quats[arm]):
                s.record['ee_at_basket']=s.opening(arm)
                s.grip('deposit',arm,1)
                s.record.update(deposited=True,stop='deposited')
                return True
        s.record['stop']='drop_plans_rejected'
        if guard:s.release_for_next(arm)
        return guard
