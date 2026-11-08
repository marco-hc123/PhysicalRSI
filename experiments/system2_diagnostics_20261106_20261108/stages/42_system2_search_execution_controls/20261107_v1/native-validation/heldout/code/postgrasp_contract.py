"""Unchanged action contract with planner and primitive side-channel logging."""
import time,functools
from pathlib import Path
from diagnostic_common import append,safe
from trajectory_contract import DiagnosticBackend,DiagnosticPrimitives,ObservedObstacles

class Backend(DiagnosticBackend):
    def __init__(self,configuration,output):
        super().__init__(configuration,output)
        for arm,planner in self.planners.items():
            self.wrap_planner(arm,planner.motion_planner)
    def wrap_planner(self,arm,planner):
        original=planner.plan_pose
        @functools.wraps(original)
        def plan(*args,**kwargs):
            start=time.monotonic_ns();record=dict(arm=arm,index=self.counter,started_ns=start)
            try:
                result=original(*args,**kwargs)
                attributes=dict(vars(result)) if hasattr(result,'__dict__') else {}
                for name in ['success','status','valid_query','ik_error','position_error','rotation_error','solve_time','total_time','attempts','debug_info']:
                    if hasattr(result,name):attributes[name]=getattr(result,name)
                record.update(result_type=type(result).__name__,available_attributes=sorted(attributes),result=safe(attributes))
                return result
            except BaseException as e:
                record.update(exception=type(e).__name__+': '+str(e));raise
            finally:
                record['returned_ns']=time.monotonic_ns()
                append(self.output/'raw-planner-results.jsonl',record)
        planner.plan_pose=plan

class Primitives(DiagnosticPrimitives):
    def _record(self,method,fn,kwargs):
        out=self.diagnostic_backend.output/'primitive-events.jsonl'
        start=time.monotonic_ns();append(out,dict(event='begin',method=method,kwargs=kwargs,started_ns=start,index=self.diagnostic_backend.counter))
        try:
            result=fn(**kwargs);append(out,dict(event='return',method=method,kwargs=kwargs,started_ns=start,index=self.diagnostic_backend.counter,result=result));return result
        except BaseException as e:
            append(out,dict(event='exception',method=method,kwargs=kwargs,started_ns=start,index=self.diagnostic_backend.counter,error=type(e).__name__+': '+str(e)));raise
    def approach(self,*,arm,position_m,quaternion_wxyz):
        return self._record('approach',super().approach,dict(arm=arm,position_m=position_m,quaternion_wxyz=quaternion_wxyz))
    def gripper(self,*,arm,command):
        return self._record('gripper',super().gripper,dict(arm=arm,command=command))

def assemble(channel,*,configuration,identity,own,pool=None):
    backend=own(Backend(configuration,Path(configuration['output'])/identity['episode']/identity['actor']))
    perception=ObservedObstacles(channel=channel,estimate=backend.estimate,max_age_s=180)
    return Primitives(diagnostic_backend=backend,observe=channel.observe,plan=backend.plan,step=channel.step,
        perceive=perception.observe,dimensions=configuration['dimensions'],joint_limits=configuration['joint_limits'],
        max_joint_step=.25,timeout_s=180,max_waypoints=500,gripper_steps=6)
