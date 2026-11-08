"""Explicit gripper-command retention; observations remain measured values."""
import math,time
from pathlib import Path
from postgrasp_contract import Backend,Primitives,ObservedObstacles
from diagnostic_common import append

class GripperContract(Primitives):
    def __init__(self,*,latch_gripper_commands,**kwargs):
        super().__init__(**kwargs)
        self.latch_gripper_commands=bool(latch_gripper_commands)
        self.gripper_commands={};self.step_index=0
        original_step=self.step
        def recorded_step(action,*,deadline):
            self.step_index+=1
            # Copy only for action construction; never mutate observed data.
            applied={k:list(v) for k,v in action.items()}
            if self.latch_gripper_commands:
                for arm,value in self.gripper_commands.items():
                    key=arm+'_ee_joint_state';applied[key]=[value]*self.dimensions[key]
            record=dict(index=self.step_index,monotonic_ns=time.monotonic_ns(),latched=self.latch_gripper_commands,last_explicit_commands=dict(self.gripper_commands),input_action=action,applied_action=applied)
            result=original_step(applied,deadline=deadline)
            record['returned_ns']=time.monotonic_ns();append(self.diagnostic_backend.output/'applied-actions.jsonl',record)
            return result
        self.step=recorded_step
    def gripper(self,*,arm,command):
        if arm not in ('left','right') or type(command) not in (int,float) or not math.isfinite(command) or not 0<=command<=1:
            raise ValueError('Expected an arm and normalized gripper command in [0, 1]')
        self.gripper_commands[arm]=float(command)
        return super().gripper(arm=arm,command=command)

def assemble(channel,*,configuration,identity,own,pool=None):
    backend=own(Backend(configuration,Path(configuration['output'])/identity['episode']/identity['actor']))
    perception=ObservedObstacles(channel=channel,estimate=backend.estimate,max_age_s=180)
    return GripperContract(latch_gripper_commands=configuration['latch_gripper_commands'],diagnostic_backend=backend,
        observe=channel.observe,plan=backend.plan,step=channel.step,perceive=perception.observe,
        dimensions=configuration['dimensions'],joint_limits=configuration['joint_limits'],max_joint_step=.25,timeout_s=180,max_waypoints=500,gripper_steps=6)
