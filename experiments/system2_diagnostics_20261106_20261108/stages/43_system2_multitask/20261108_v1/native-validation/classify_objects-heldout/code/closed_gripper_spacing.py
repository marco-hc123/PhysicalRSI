"""Single-factor control: native waypoint spacing while gripper is commanded closed.

This selects a denser subset of the SAME native planned path. It is not a
velocity controller or evidence of grasp retention. All deadline, step-budget,
collision-planner and endpoint constraints remain in the inherited runtime.
"""
import hashlib,json
import numpy as np
from structured_feedback import assemble as base_assemble
from released_waypoints import thin_native_path
from diagnostic_common import append
from trajectory_contract import write

def select_closed_path(dense,start):
 indices,diagnostic=thin_native_path(dense,start,max_joint_step=.06,chord_tolerance=.01)
 if diagnostic['native_adjacent_over_bound'] or diagnostic['max_selected_joint_delta_rad']>.0600001:
  raise ValueError('Native samples exceed closed-gripper .06rad spacing; no invented interpolated path')
 assert indices[-1]==len(dense)-1
 path=np.asarray(dense)[indices].tolist()
 assert path[-1]==list(dense[-1])
 return path,indices,diagnostic

def assemble(channel,*,configuration,identity,own,pool=None):
 primitive=base_assemble(channel,configuration=configuration,identity=identity,own=own,pool=pool)
 enabled=configuration['closed_gripper_dense_spacing'];assert type(enabled) is bool
 original=primitive.plan;backend=primitive.diagnostic_backend
 def plan(**kwargs):
  selected=original(**kwargs)
  path,record=backend.last_record
  closed=primitive.gripper_commands.get(kwargs['arm'])==0
  record['closed_gripper_spacing']=dict(enabled=enabled,closed_command=closed,baseline_bound_rad=.12,treatment_bound_rad=.06,physical_speed_or_grasp_claim=False)
  if enabled and closed:
   dense=record['dense_path'];result,indices,diagnostic=select_closed_path(dense,kwargs['start'])
   record['closed_gripper_spacing'].update(original_executed_waypoints=len(selected),new_executed_waypoints=len(result),diagnostic=diagnostic)
   record.update(selected_path=result,indices=indices,executed_waypoints=len(result),selection_diagnostic=diagnostic)
   selected=result
  write(path,record);backend.last_record=(path,record)
  return selected
 primitive.plan=plan
 append(backend.output/'spacing-contract.jsonl',dict(enabled=enabled,source_sha256=hashlib.sha256(open(__file__,'rb').read()).hexdigest(),scope='Dense original native samples only when moving arm command is closed; no candidate/API/reward change'))
 return primitive
