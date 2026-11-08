import collections,datetime,json,statistics
from pathlib import Path
L=Path('/mnt/data/joey_tr/physical-RSI/result/34_system2_trajectory_contract/20261106_v1');N=L/'native-validation'
def read(p):return json.loads(p.read_text())
s=read(L/'FINAL_SUMMARY.json');ts=read(L/'trajectory-events.json');groups=[]
for name in ['dense','released_waypoint_thinning']:
 rs=[t for t in ts if t['condition']==name];complete=[r for r in rs if r['execution_complete_without_error']];errs=[r['final_observed_joint_error_rad'] for r in complete if r['final_observed_joint_error_rad'] is not None]
 raw=[read(N/r['trace']) for r in rs]
 groups.append(dict(condition=name,approach_trace_count=len(rs),completed_approaches=len(complete),planned_dense_waypoints=sum(r['dense_waypoints'] or 0 for r in rs),planned_selected_waypoints=sum(r['selected_waypoints'] or 0 for r in rs),completed_approach_steps=sum(r['completed_action_steps'] or 0 for r in complete),completed_joint_error_rad=dict(n=len(errs),median=statistics.median(errs) if errs else None,maximum=max(errs) if errs else None),backend_rejections=dict(collections.Counter(r.get('error_type','unknown')+':'+r.get('error','unknown') for r in raw if r['state']=='planning_or_selection_rejected')),execution_exceptions=dict(collections.Counter(r['execution_exception']['type']+':'+r['execution_exception']['message'] for r in raw if r.get('execution_exception')))))
out=dict(state='completed',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),groups=groups,limitations=['Planned points can include later-cancelled paths; completed steps omit partial cancelled commands.','Tracking errors are per completed approach and differ by visited trajectory; no matched-trajectory causal precision estimate.','Joint error is not object grasp or Cartesian pose error.','Backend PlanningRejected projects multiple possible solver failures into one error, not proven collision failure.'])
p=L/'trajectory-diagnostics.json';assert not p.exists();p.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
