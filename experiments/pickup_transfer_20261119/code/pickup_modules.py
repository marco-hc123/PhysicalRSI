"""Public RGB-D target and bounded pre-close control adapters for the frozen pickup program."""
import numpy as np
import teacher_kin as kin
from teacher_functions import world_points, voxel_downsample_3d, sampled_joints

def point_target(views, segmenter, description):
    clouds=[]
    evidence=[]
    for name,view in views.items():
        mask=segmenter.segment(view['color'][...,:3],text_prompt=description)
        counts={'camera':name,'score':mask.score,'points':0}
        if mask.found:
            pts,_=world_points(view,*np.nonzero(mask.mask))
            pts=pts[np.isfinite(pts).all(axis=1)]
            # Retain the frozen parent's table workspace.
            pts=pts[(np.abs(pts[:,0])<.6)&(pts[:,1]>-.5)&(pts[:,1]<.3)&(pts[:,2]>=.765)]
            if len(pts):
                counts['points']=len(pts)
                clouds.append(pts)
        evidence.append(counts)
    if not clouds:return None,evidence
    fused=voxel_downsample_3d(np.concatenate(clouds))
    return np.median(fused,axis=0),evidence

def contact_link_goal(point):
    # Original contact command .93 m for a .785 m nominal object point.
    return np.asarray(point)+[0.,0.,.93-.785]

def preclose(arm,link_target,quat,read_arm,checked_step,emit):
    """checked_step must retain existing collision, joint and episode budget guards."""
    rot=kin.rot_from_quat(quat)
    tcp_goal=np.eye(4)
    tcp_goal[:3,:3]=rot
    tcp_goal[:3,3]=link_target+rot[:,0]*kin.TCP_OFFSET
    def residual(q):
        link=kin.fk(arm,q)
        return float(np.linalg.norm(kin.tcp(link)-tcp_goal[:3,3])),float(kin.rotation_error(link[:3,:3],rot))
    q=read_arm(arm)
    before=residual(q)
    sol=kin.best_solution(arm,tcp_goal,q,extra_seeds=[(0.,)*6])
    steps=0
    if sol.ok and not sol.collides:
        for _ in range(8):
            q=read_arm(arm)
            pos,deg=residual(q)
            if steps and pos<=.002 and deg<=1.:break
            waypoints=sampled_joints(q,[sol.q],max_step=.03)
            checked_step(arm,(waypoints[1:] or [sol.q])[0])
            steps+=1
    after=residual(read_arm(arm))
    passed=bool(sol.ok and not sol.collides and after[0]<=.002 and after[1]<=1.)
    emit(dict(arm=arm,link_target=np.asarray(link_target).tolist(),tcp_goal=tcp_goal[:3,3].tolist(),before=before,after=after,steps=steps,passed=passed))
    return passed
