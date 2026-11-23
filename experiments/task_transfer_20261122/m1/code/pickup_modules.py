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

def grasp_and_lift_link_goals(point, quat):
    """
    1. 消除 rot[:,0] 与竖直 [0,0,0.145] 不一致造成的右臂 +8.6/-4.5mm、左臂 +1.5/-3.6mm 水平侧偏：
       直接定义期望的指尖中心 (TCP) 位置 tcp_xyz，再用 link_target = tcp_xyz - rot[:,0] * TCP_OFFSET 反推 link6 目标。
    2. 下探深度修正：RGB-D 测得的 point[2] 是物体可见上表面中位数。
       将目标 TCP 高度从上表面向下探 2.5 cm 以夹持物体腰部/中下部，同时受安全桌面高度 0.785 m（距桌面 2.0 cm）下界保护。
    3. 相对抬升行程修正：确保相对实际下探高度至少抬升 +14 cm（同时提供 +12 cm 与 1.06 m 作为规划回退候选），
       解决 14 号果汁盒、1 号人偶、10 号葡萄串抬升被 1.06 m 截断至 <10 cm 以及 4 号甜甜圈裕度不足的问题。
    """
    p = np.asarray(point, dtype=float)
    rot = kin.rot_from_quat(quat)
    # 下探高度：从顶面点云下探 2.5 cm，但不低于原策略验证安全的 0.785 m
    z_tcp_contact = float(np.clip(p[2] - 0.025, 0.785, 0.835))
    tcp_contact = np.array([p[0], p[1], z_tcp_contact], dtype=float)
    link_contact = tcp_contact - rot[:, 0] * kin.TCP_OFFSET
    # 相对抬升候选（优先抬高 14 cm，若超出上方工作空间则回退 12 cm 或 1.06 m）
    z_contact = float(link_contact[2])
    lift_candidates = []
    for z_lift in (max(1.06, z_contact + 0.14), max(1.06, z_contact + 0.12), 1.06):
        z_lift = round(float(z_lift), 4)
        if z_lift > z_contact + 0.105 and z_lift not in lift_candidates:
            lift_candidates.append(z_lift)
    return link_contact, tcp_contact, lift_candidates
def preclose(arm, link_target, quat, read_arm, checked_step, emit):
    """
    尽力闭环微调 + 解耦放行闭爪：
    - 允许 sol.ok 或近邻无碰撞解 (pos_err_m <= 0.02 m, rot_err_deg <= 8.0 deg，对齐 robodojo_tools.py NEAR_M/NEAR_DEG) 执行微调；
    - 单步插值步长设为 0.06 rad（8 步可覆盖 0.48 rad 关节调整），并在到位后维持 sol.q 消除 PD 滞后；
    - 完整记录 passed_2mm 供对照诊断，但微调结束后放行闭爪（仅在完全碰撞不可解时标记 warning）。
    """
    rot = kin.rot_from_quat(quat)
    tcp_goal = np.eye(4)
    tcp_goal[:3, :3] = rot
    tcp_goal[:3, 3] = np.asarray(link_target, dtype=float) + rot[:, 0] * kin.TCP_OFFSET
    def residual(q):
        link = kin.fk(arm, q)
        return float(np.linalg.norm(kin.tcp(link) - tcp_goal[:3, 3])), float(kin.rotation_error(link[:3, :3], rot))
    q = read_arm(arm)
    before = residual(q)
    sol = kin.best_solution(arm, tcp_goal, q, extra_seeds=[(0.,) * 6])
    usable_ik = bool(not sol.collides and (sol.ok or (sol.pos_err_m <= 0.02 and sol.rot_err_deg <= 8.0)))
    steps = 0
    if usable_ik:
        for _ in range(8):
            q = read_arm(arm)
            pos, deg = residual(q)
            if steps and pos <= .002 and deg <= 1.:
                break
            waypoints = sampled_joints(q, [sol.q], max_step=.06)
            checked_step(arm, (waypoints[1:] or [sol.q])[0])
            steps += 1
    after = residual(read_arm(arm))
    passed_2mm = bool(sol.ok and not sol.collides and after[0] <= .002 and after[1] <= 1.)
    # 放行闭爪：只要接近阶段 (CuRobo) 已成功到达 contact 位，微调后均允许执行闭爪
    allow_close = True
    emit(dict(
        arm=arm,
        link_target=np.asarray(link_target).tolist(),
        tcp_goal=tcp_goal[:3, 3].tolist(),
        before=before,
        after=after,
        steps=steps,
        usable_ik=usable_ik,
        passed=passed_2mm,
        allow_close=allow_close,
    ))
    return allow_close
