"""Observable call stops plus separate privileged first-cycle diagnostics."""
import json,math,hashlib,datetime
from pathlib import Path
import physical_metrics as pm
from selected_sidecars import select
O=Path(__file__).resolve().parent
read=pm.read;lines=pm.lines
matrix=read(O/'analysis/matrix-analysis.json');campaign=read(O/'native-campaign/campaign.json')
layouts=[read(Path(campaign['layout_root'])/c['file']) for c in campaign['cases']]
paths,binding=select(O);by_condition={r['condition']:p for r,p in zip(binding['selected'],paths)}
rows=[];motions=[]
for condition,path in by_condition.items():
 snapshots=[x for x in lines(path) if x.get('event')=='snapshot']
 for actor in [x for x in matrix['actors'] if x['condition']==condition]:
  row=dict(condition=condition,actor_episode_id=actor['actor_episode_id'],layout_id=actor['mapped_layout_id'],mapping_qualified=actor['mapping_qualified'],first_error=actor['first_error'],actor_final_state=actor['actor_final_state'],actor_error=actor['actor_error'],step_limit_cancelled=actor['native_step_limit_cancelled'])
  if not actor['mapping_qualified']:
   row.update(physical_diagnosis='unknown actor-layout association');rows.append(row);continue
  i=actor['mapped_layout_id'];episode=next(x for x in matrix['episodes'] if x['condition']==condition and x['layout_id']==i)
  snaps=sorted([x for x in snapshots if x['layout_seed']==i],key=lambda x:x['native_action_count'])
  assert [x['native_action_count'] for x in snaps]==list(range(episode['native_action_count']+1))
  p=O/'backend-traces'/condition/actor['actor_episode_id']/'0/primitive-events.jsonl'
  if not p.exists():
   row.update(physical_diagnosis='no primitive events',native_score_100=episode['normalized_score']*100,full_success=episode['success']);rows.append(row);continue
  events=lines(p);begins=[x for x in events if x['event']=='begin'];ends=[x for x in events if x['event'] in ['return','exception']]
  ps=[]
  for ordinal,b in enumerate(begins):
   e=next((x for x in ends if x['started_ns']==b['started_ns'] and x['method']==b['method']),None)
   d=dict(ordinal=ordinal,method=b['method'],arm=b['kwargs'].get('arm'),kwargs=b['kwargs'],begin_ns=b['started_ns'],end_ns=e['monotonic_ns'] if e else None,accepted=bool(e and e['event']=='return' and not (e.get('result') or {}).get('primitive_error')),error=(e.get('error') or (e.get('result') or {}).get('primitive_error')) if e else 'incomplete')
   if e:
    snap=pm.near(snaps,e['monotonic_ns']);d['end_action']=snap['native_action_count']
    if b['method']=='approach':
     key=next((k for k in snap['robots'] if k.startswith(d['arm'])),None)
     ee=pm.flat(snap['robots'][key]['ee_pose_world']) if key else None
     d['ee_translation_error_m']=math.dist(ee[:3],b['kwargs']['position_m']) if ee else None
   ps.append(d)
   if b['method']=='approach':motions.append(dict(condition=condition,layout_id=i,**d))
  close=next((x for x in ps if x['method']=='gripper' and x['kwargs']['command']==0),None)
  phase={};source_xy=None;arm=None;destination=None
  if close:
   arm=close['arm'];pre=[x for x in ps if x['ordinal']<close['ordinal'] and x['method']=='approach' and x['arm']==arm]
   if pre:source_xy=pre[-1]['kwargs']['position_m'];phase['selection']=pm.near(snaps,pre[-1]['begin_ns'])
   if close['end_ns']:phase['close']=pm.near(snaps,close['end_ns'])
   release=next((x for x in ps if x['ordinal']>close['ordinal'] and x['method']=='gripper' and x['arm']==arm and x['kwargs']['command']==1),None)
   following=[x for x in ps if x['ordinal']>close['ordinal'] and x['method']=='approach' and x['arm']==arm and (release is None or x['ordinal']<release['ordinal'])]
   if following and following[0]['accepted']:phase['lift']=pm.near(snaps,following[0]['end_ns'])
   if len(following)>1:
    destination=following[-1]['kwargs']['position_m']
    if following[-1]['accepted']:phase['transport']=pm.near(snaps,following[-1]['end_ns'])
   if release and release['accepted']:phase['release']=pm.near(snaps,release['end_ns'])
  meta={b['label']:read(O/'scoring-reference'/('basket_'+str(b['category_idx']).zfill(5)+'.json'))['geometry']['oriented_bbox']['vertices'] for b in layouts[i]['Geometry']['basket']}
  row.update(native_score_100=episode['normalized_score']*100,full_success=episode['success'],release_observed='release' in phase,completed_approaches=sum(x['accepted'] for x in ps if x['method']=='approach'),close_calls=sum(x['method']=='gripper' and x['kwargs']['command']==0 for x in ps),segmentation='Heuristic first close, following first move as lift, last move before same-arm open as transport. Inspect source/video before causal interpretation.')
  rows.append(pm.measure(row,snaps,meta,source_xy,arm,phase,destination))
out=dict(state='completed',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),cases=rows,motions=motions,sidecar_binding=binding,scope='Privileged diagnostics only, never policy or generation raw-state input. First-cycle physical proxies are separate from native task scoring. Final stability uses the end of full native episode, so later interactions can affect the object.',unknown_physical_cases=sum(x.get('complete_chain_proxy') is None for x in rows))
(O/'analysis/mechanism-diagnostics.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(dict(cases=len(rows),motions=len(motions),unknown=out['unknown_physical_cases'])))
