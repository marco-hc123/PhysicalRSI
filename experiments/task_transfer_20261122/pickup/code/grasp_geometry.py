"""Frozen XY, wrist orientation and approach-height rules."""
import numpy as np
import teacher_kin as kin
from compare_target_xy import compare


def target(cloud, rule):
    xy = cloud[:, :2]
    mean = xy.mean(0)
    val, vec = np.linalg.eigh(np.cov((xy-mean).T))
    major, minor = vec[:, 1], vec[:, 0]
    uv = (xy - mean) @ vec
    mid = np.percentile(uv[:, 1], [2, 98]).mean()
    near = abs(uv[:, 1] - mid) <= .015
    span = np.percentile(xy, [2, 98], axis=0).mean(0)
    if rule == 'T0':
        center = np.median(xy, axis=0)
    elif rule == 'T1':
        center = span
    elif rule == 'T2':
        center = compare(cloud)['candidates']['waist']['xyz_m'][:2]
    elif rule == 'T3':
        center = mean + mid * major + np.median(uv[near, 0]) * minor if near.sum() >= 30 else span
    else:
        raise ValueError(rule)
    return np.r_[center,np.median(cloud[:,2])], minor, val[1]/max(val[0],1e-9), bool(rule=='T3' and near.sum()<30)


def depth(cloud, point, rule):
    base = float(np.clip(point[2]-.025,.785,.835))
    if rule == 'Z1':
        return base, False
    dist = np.linalg.norm(cloud[:,:2]-point[:2],axis=1)
    local = cloud[dist<=.015]
    if len(local)<15:
        local=cloud[dist<=.025]
    if len(local)<15:
        return base, True
    top=np.percentile(local[:,2],90)
    return float(np.clip(.765+.55*max(0,top-.765),.783,max(.783,top-.008))), False


def rotate(rot, angle):
    c,s=np.cos(angle),np.sin(angle)
    return np.array([[c,-s,0],[s,c,0],[0,0,1]]) @ rot


def poses(arm, tcp, minor, ratio, yaw, start):
    q=np.array([.613,-.3593,.6163,.3392] if arm=='left' else [.3814,-.6197,.3785,.572])
    base=kin.rot_from_quat(q/np.linalg.norm(q))
    delta=np.arctan2(minor[1],minor[0])-np.arctan2(base[1,1],base[0,1])
    options=[('base',base)]
    if yaw=='Y1' and ratio>=1.4:
        options=[('aligned_0',rotate(base,delta)),('aligned_180',rotate(base,delta+np.pi))]+options
    records=[]
    for name,rot in options:
        T=np.eye(4); T[:3,:3]=rot; T[:3,3]=tcp
        sol=kin.best_solution(arm,T,start,extra_seeds=[(0.,)*6])
        cost=float(np.dot([2,2,1.5,1,1,.5],abs(np.array(sol.q)-start)))
        records.append(dict(name=name,ok=bool(sol.ok and not sol.collides),cost=cost))
    good=[i for i,r in enumerate(records) if r['ok'] and r['name']!='base']
    i=min(good,key=lambda j:records[j]['cost']) if good else len(records)-1
    return options[i][1],options[i][0],records


def goals(tcp,rot):
    link=tcp-rot[:,0]*kin.TCP_OFFSET
    lifts=[round(float(x),4) for x in (max(1.06,link[2]+.14),max(1.06,link[2]+.12),1.06) if x>link[2]+.105]
    return link,list(dict.fromkeys(lifts))
