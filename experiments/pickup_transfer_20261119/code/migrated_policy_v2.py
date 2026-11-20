"""Integrated pickup using public observations and frozen CuRobo action guards."""
from shared_io import *
import re
import sys
import traceback
import numpy as np
from pickup_modules import point_target, contact_link_goal, preclose
class NativeTerminal(Exception):
    pass
def run():
    old=ROOT/'result/46_research_week_20261109_20261115/raw/53_aligned_pickup_heldout_20261115'
    contract=old/'recovery/scoring-exit-repair/native_v2/code'
    original=ROOT/'result/16_system2_integration/25_system2_integration_20261030T050100Z/integration-sources'
    assets=ROOT/'models/recorded_policy_assets/skill-assets/implementations/code-skills'
    bundle=assets/'implementations/rdj_v1_classify_objects/6bb861ace4b706d9'
    sys.path[:0]=[str(contract),str(original),str(bundle),str(ROOT/'repos/lab-runtime/curobo'),str(next(assets.glob('implementations/rdj_pour/*/rdj_pour/assets/sam3_source')))]
    sys.path.append(str(ROOT/"envs/simulator/lib/python3.11/site-packages"))
    import warp
    warp.config.kernel_cache_dir=os.environ['WARP_CACHE_PATH']
    import curobo._src.runtime as runtime
    runtime.cache_dir=os.environ['CUROBO_CACHE_DIR']
    from gripper_contract import GripperContract
    from trajectory_contract import DiagnosticBackend
    from rdj_v1_classify_objects.curobo_planner import CuroboPlanner
    from sam3_local import LocalSam3
    from PIL import Image
    import torch
    assert torch.cuda.device_count()==1
    cfg=json.loads((old/'reference-runtime.json').read_text())['policy_spec']['configuration']
    backend=DiagnosticBackend.__new__(DiagnosticBackend)
    backend.configuration,backend.output,backend.mode,backend.counter,backend.last_record=cfg,R,cfg['trajectory_mode'],0,None
    joints=['joint'+str(i) for i in range(1,7)]
    yml=ROOT/'result/28_h100_offline_acceptance/20261104_v5/planning/robot-paths-only.yml'
    backend.planners={arm:CuroboPlanner(robot_origin_pose=[0,0,0,1,0,0,0],active_joints_name=joints,all_joints=joints,dt=.004,yml_path=str(yml),table_height=-.025) for arm in ('left','right')}
    sam=LocalSam3(str(sorted(assets.glob('assets/sam3/*/sam3.pt'))[0]))
    write('policy-ready.json',{'pid':os.getpid(),'planner':str(yml)})
    obs=wait('obs-0.json',420)
    sequence=0
    names=('cam_head','cam_left_wrist','cam_right_wrist')
    with np.load(R/'public-start.npz') as ar:
        views={n:{k:ar[n+'_'+k] for k in ('color','depth','extrinsic_matrix','intrinsic_matrix')} for n in names}
    target=re.fullmatch(r'Pick up the (.+?) by 10 cm\.?',obs['instruction'].strip(),re.I)
    assert target
    point,evidence=point_target(views,sam,target.group(1).replace('_',' '))
    write('target.json',{'description':target.group(1),'point':None if point is None else point.tolist(),'views':evidence})
    def step(action,*,deadline):
        nonlocal obs,sequence
        write(f'cmd-{sequence}.json',{'action':action,'phase':phase})
        sequence+=1
        obs=wait(f'obs-{sequence}.json')
        if obs['terminal']:raise NativeTerminal
    def state(*,deadline):return obs['state']
    robot=GripperContract(latch_gripper_commands=True,diagnostic_backend=backend,observe=state,plan=backend.plan,step=step,perceive=None,dimensions=cfg['dimensions'],joint_limits=cfg['joint_limits'],max_joint_step=.25,timeout_s=180,max_waypoints=500,gripper_steps=6)
    def read(arm):return robot._state(time.monotonic()+180)[arm+'_arm_joint_state']
    def correct(arm,q):
        end=time.monotonic()+180
        motion=robot._state(end)
        key=arm+'_arm_joint_state'
        q=robot._joints(arm,q)
        if np.max(np.abs(np.array(motion[key])-q))>.25:raise ValueError('Observed robot diverged from planned trajectory')
        motion[key]=list(q)
        robot.step(motion,deadline=end)
    phase='approach'
    stop='target_not_detected'
    try:
        if point is not None:
            goal=contact_link_goal(point)
            arms=['left','right'] if point[0]<=0 else ['right','left']
            stop='approach_plans_rejected'
            for arm in arms:
                q=np.array([.613,-.3593,.6163,.3392] if arm=='left' else [.3814,-.6197,.3785,.572])
                quat=(q/np.linalg.norm(q)).tolist()
                def move(height):
                    return not robot.approach(arm=arm,position_m=[float(goal[0]),float(goal[1]),float(height)],quaternion_wxyz=quat).get('primitive_error')
                if not move(1.02):continue
                phase='open';robot.gripper(arm=arm,command=1)
                phase='contact'
                if not move(goal[2]):stop='contact_plan_rejected';break
                phase='preclose'
                ok=preclose(arm,goal,quat,read,correct,lambda record:write('preclose.json',record))
                if not ok:stop='preclose_not_reached';break
                phase='close';robot.gripper(arm=arm,command=0)
                phase='lift';stop='program_complete' if move(1.06) else 'lift_plan_rejected'
                break
    except NativeTerminal:
        write('policy-stop.json',{'reason':'native_terminal','sequence':sequence,'phase':phase})
        return
    except ValueError as e:
        if str(e)!='Observed robot diverged from planned trajectory':raise
        stop='observed_trajectory_divergence'
    write('policy-stop.json',{'reason':stop,'sequence':sequence,'phase':phase})
    write(f'cmd-{sequence}.json',{'hold':True,'phase':phase})
try:
    run()
except BaseException:
    write('policy-error.json',{'traceback':traceback.format_exc()})
    raise
