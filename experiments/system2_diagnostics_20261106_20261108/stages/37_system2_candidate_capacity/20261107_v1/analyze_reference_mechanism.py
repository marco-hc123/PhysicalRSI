"""Expose the reference controller's stopping stage, without changing its score."""
from pathlib import Path
import json,csv,statistics,os
L=Path(__file__).resolve().parent;N=L/'native-validation'
def read(p):return json.loads(p.read_text())
a=read(N/'analysis/independent-validation.json');assert a['state']=='passed'
rows=[];series=[]
for ep in a['episodes']:
 events=[]
 for rel in ep['source_traces']:events += [json.loads(x) for x in (N/rel).read_text().splitlines()]
 groups=[];group=[]
 for e in events:
  if 'endpoint_wait' not in e:continue
  if e['endpoint_wait']==0:
   if group:groups.append(group)
   group=[]
  group.append(e)
 if group:groups.append(group)
 terminal=[g for g in groups if g[-1]['endpoint_wait']==40];last=terminal[-1] if terminal else []
 for gidx,g in enumerate(groups):
  for e in g:series.append(dict(layout=ep['layout_id'],segment=gidx,stage=e['stage'],wait=e['endpoint_wait'],action=e['action_index'],position_error_m=e['position_error_m'],rotation_error_rad=e['rotation_error_rad'],joint_error_rad=e['joint_error_rad'],terminal_wait_exhausted=g[-1]['endpoint_wait']==40))
 stop='native_success' if ep['success'] else 'model_reported_failure' if ep['last_model_failure'] else 'native_budget_end_while_active' if ep['last_model_stage']!='complete_hold' else 'complete_hold_without_native_success'
 tail=[x['position_error_m'] for x in last[-10:]]
 rows.append(dict(layout=ep['layout_id'],score_100=ep['episode_score']*100,success=ep['success'],stop_class=stop,last_stage=ep['last_model_stage'],failure=ep['last_model_failure'],reported_basket_transfers=ep['completed_basket_transfers'],last_exhausted_endpoint_stage=last[-1]['stage'] if last else None,last_position_error_m=tail[-1] if tail else None,last10_position_error_range_m=max(tail)-min(tail) if tail else None,last_rotation_error_rad=last[-1]['rotation_error_rad'] if last else None,last_joint_error_rad=last[-1]['joint_error_rad'] if last else None,source_traces=ep['source_traces']))
for name,data in [('reference-stop-details.csv',rows),('endpoint-error-series.csv',series)]:
 if data:
  with (L/name).open('w',newline='') as f:
   w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows({k:json.dumps(v) if isinstance(v,(dict,list)) else v for k,v in row.items()} for row in data)
report=dict(state='completed',rows=rows,limits=['A completed_transfer event is a controller report, not proof of object placement.','Endpoint rejection after40waits is different from no trajectory returned before any action.','A short-tail plateau does not identify contact versus actuator versus model error by itself.','No endpoint tolerance, score threshold or step budget was changed.'])
(L/'reference-mechanism.json').write_text(json.dumps(report,indent=2)+'\n')
os.environ['MPLCONFIGDIR']=str(L/'analysis-cache/matplotlib')
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
F=L/'figures';F.mkdir(exist_ok=True)
fig,axes=plt.subplots(1,2,figsize=(11,4));g=read(L.parent.parent/'36_system2_gripper_command_contract/20261107_v1/FINAL_SUMMARY.json')['groups'][-1]
axes[0].bar([i-.18 for i in range(5)],g['scores_by_layout_100'],width=.35,label='Generated candidate + command latch')
axes[0].bar([i+.18 for i in range(5)],[x['score_100'] for x in rows],width=.35,label='Complete released controller reference')
axes[0].set(xticks=range(5),ylim=(0,100),xlabel='Previously exposed layout',ylabel='Native score /100',title='Descriptive reference; multiple mechanisms differ');axes[0].legend(fontsize=6)
for ep in rows:
 s=[x for x in series if x['layout']==ep['layout'] and x['terminal_wait_exhausted']]
 if s:
  seg=max(x['segment'] for x in s);s=[x for x in s if x['segment']==seg];axes[1].plot([x['wait'] for x in s],[1000*x['position_error_m'] for x in s],label='Layout '+str(ep['layout']))
axes[1].axhline(10,color='black',linestyle='--',label='Original10mm gate');axes[1].set(xlabel='Endpoint hold iteration',ylabel='Translation error (mm)',title='Last exhausted endpoint wait');axes[1].legend(fontsize=6);fig.tight_layout()
for ext in ['png','svg']:fig.savefig(F/('reference_scores_and_stops.'+ext),dpi=150)
plt.close(fig);print(json.dumps(rows))
