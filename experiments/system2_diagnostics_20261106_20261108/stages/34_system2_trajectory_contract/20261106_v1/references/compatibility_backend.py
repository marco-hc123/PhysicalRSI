"""Pinned cloud compatibility assembly: released RGB reader and CuRobo planner.

No task controller or generated Python is imported here. Generated programs see
only RoboDojoPrimitives RPC. RGB-derived geometry is approximate; collision
checking is the released robot/table model, not ground-truth object geometry.
"""
from pathlib import Path
import time
import numpy as np
from PhysicalRSI_baselines.robodojo.primitives import RoboDojoPrimitives
from PhysicalRSI_baselines.robodojo.perception import ObservedObstacles

class PlanningRejected(RuntimeError):
    pass

class Backend:
    def __init__(self, configuration, output):
        from rdj_v1_classify_objects.perception import Reader
        import rdj_v1_classify_objects.perception as rgb_geometry
        import rdj_v1_classify_objects.robot_mask as robot_geometry
        from PhysicalRSI_baselines.robodojo.camera_geometry import PinholeCamera
        camera=PinholeCamera(**configuration['camera'])
        def calibrated_ray(pixel,z):
            pixels=np.asarray([pixel],dtype=float)
            return camera.unproject(pixels,camera.plane_depth(pixels,world_z=float(z)))[0]
        rgb_geometry.ray=calibrated_ray
        robot_geometry.project=lambda points: camera.project(np.asarray(points,dtype=float))[0]
        from rdj_v1_classify_objects.curobo_planner import CuroboPlanner
        self.configuration=configuration;self.output=Path(output)
        self.output.mkdir(parents=True,exist_ok=True)
        self.reader=Reader()
        self.planners={a:CuroboPlanner(robot_origin_pose=[0,0,0,1,0,0,0],
            active_joints_name=['joint'+str(i) for i in range(1,7)],
            all_joints=['joint'+str(i) for i in range(1,7)],dt=.004,
            yml_path=configuration['robot_yml'],table_height=-.025)
            for a in ('left','right')}
    def close(self):
        for p in self.planners.values():
            p.__del__()
        self.planners.clear()
    def estimate(self, *, snapshot, deadline):
        from PhysicalRSI_core.infra.storage import atomic_json
        raw=self.reader.read_batch([snapshot['vision']['cam_head']['color']],
                                   [snapshot['state']])[0]
        if time.monotonic()>=deadline:raise TimeoutError('RGB perception deadline')
        result={};counts={}
        for row in sorted(raw,key=lambda r:(r['category'],float(r['xyz'][0]))):
            category=row['category'];counts[category]=counts.get(category,0)+1
            name=category+'_'+str(counts[category]);size=self.configuration['object_sizes'].get(category,[.06,.04,.04])
            result[name]=dict(pose=[*map(float,row['xyz']),1.,0.,0.,0.],dims=size)
        atomic_json(self.output/('scene-'+str(snapshot['sequence'])+'.json'),dict(
            observation_sequence=snapshot['sequence'],objects=result,
            source='released RGB DINO/CLIP and head-ray calibration; no simulator state'))
        return result
    def plan(self, *, arm,start,position_m,quaternion_wxyz,state,deadline):
        if time.monotonic()>=deadline:raise TimeoutError('Planning deadline')
        result=self.planners[arm].plan_path(curr_joint_pos=start,
            target_ee_pose=[*position_m,*quaternion_wxyz],
            real_robot_pose=self.configuration['arm_bases'][arm])
        if result.get('status')!='Success':raise PlanningRejected('Released CuRobo found no path')
        path=np.asarray(result['position'],dtype=float)
        # Keep the collision-checked native samples. No interpolation fallback.
        if path.ndim!=2 or path.shape[1]!=6 or not np.isfinite(path).all():raise ValueError('Invalid native CuRobo trajectory')
        if len(path)>500:raise ValueError('Native CuRobo path exceeds primitive bound')
        if time.monotonic()>=deadline:raise TimeoutError('Planning deadline')
        return path.tolist()

class ContractPrimitives(RoboDojoPrimitives):
    def approach(self, *, arm, position_m, quaternion_wxyz):
        try:
            return super().approach(arm=arm, position_m=position_m, quaternion_wxyz=quaternion_wxyz)
        except PlanningRejected:
            # Raised exclusively by Backend.plan before a trajectory is returned,
            # so the parent approach has not issued a channel.step for this call.
            return dict(state=self._state(time.monotonic()+self.timeout_s),
                        action_steps=0, primitive_error='no_collision_free_path')
    def bindings(self, *, revision, actor):
        bindings=super().bindings(revision=revision, actor=actor)
        base=bindings['approach']['project_output']
        def project(result):
            value=base(result)
            if result.get('primitive_error') == 'no_collision_free_path':
                if result.get('action_steps') != 0:
                    raise ValueError('A partial action cannot be a recoverable planner rejection')
                value['primitive_error']='no_collision_free_path'
            return value
        bindings['approach']['project_output']=project
        return bindings

def assemble(channel, *, configuration,identity,own,pool=None):
    backend=own(Backend(configuration,Path(configuration['output'])/identity['episode']/identity['actor']))
    perception=ObservedObstacles(channel=channel,estimate=backend.estimate,max_age_s=180)
    return ContractPrimitives(observe=channel.observe,plan=backend.plan,step=channel.step,
        perceive=perception.observe,dimensions=configuration['dimensions'],
        joint_limits=configuration['joint_limits'],max_joint_step=.25,
        timeout_s=180,max_waypoints=500,gripper_steps=6)
