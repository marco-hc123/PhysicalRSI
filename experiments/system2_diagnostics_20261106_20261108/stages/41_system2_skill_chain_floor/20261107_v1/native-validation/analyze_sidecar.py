"""Join analysis-only privileged state to monotonic primitive events, never policy."""
import json,math,statistics,csv
from pathlib import Path
R=Path(__file__).resolve().parent
if (R/'native-validation').exists():R=R/'native-validation'
A=R/'analysis';A.mkdir(exist_ok=True)
def read(p):return json.loads(p.read_text())
def lines(p):return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def xyz(obj):
 x=obj.get('position_world');return x if isinstance(x,list) and len(x)==3 and all(isinstance(i,(int,float)) for i in x) else None
def flatten(x):
 if isinstance(x,list) and len(x)==1 and isinstance(x[0],list):return flatten(x[0])
 return x
campaign=read(R/'native-campaign/campaign.json');matrix=read(A/'matrix-analysis.json')
records=[];errors=[]
from selected_sidecars import select
selected,binding=select(R);(A/'sidecar-selection.json').write_text(json.dumps(binding,indent=2)+'\n')
for p in selected:
 for x in lines(p):
  x['source_file']=str(p.relative_to(R))
  if x['event']=='snapshot':records.append(x)
  elif x['event']=='logging_error':errors.append(x)
records.sort(key=lambda x:x['monotonic_ns'])
assert records,'No simulator sidecar snapshots'
rows=[];actors=[]
for entry in campaign['entries']:
 condition=entry['name']
 for p in (R/('backend-traces-v2' if (R/'backend-traces-v2').exists() else 'backend-traces')/condition).rglob('primitive-events.jsonl'):
  events=lines(p);begin=[x for x in events if x['event']=='begin'];end=[x for x in events if x['event'] in ('return','exception')]
  if not begin:continue
  a=next((x for x in matrix['actors'] if x['condition']==condition and x['actor_episode_id']==p.parent.parent.name),None)
  assert a is not None and a['mapping_qualified'], 'Unqualified actor-layout mapping'
  idx=a['mapped_layout_id'];source_id=int(Path(campaign['cases'][idx]['file']).parent.name)
  sim=[x for x in records if int(x['layout_seed'])==idx and condition in x['source_file']]
  assert sim, (idx,p)
  assert [x['native_action_count'] for x in sim]==list(range(1101)),(idx,'Unexpected sidecar frame sequence')
  initial=sim[0];poses={k:xyz(v) for k,v in initial['objects'].items() if xyz(v) is not None}
  actor=dict(condition=condition,layout_id=idx,source_layout_id=source_id,actor_episode_id=a['actor_episode_id'],snapshots=len(sim),logging_errors=errors,score=next(x['normalized_score'] for x in matrix['episodes'] if x['condition']==condition and x['layout_id']==idx),objects={})
  for label,start in poses.items():
   vals=[xyz(x['objects'].get(label,{})) for x in sim];vals=[v for v in vals if v is not None]
   actor['objects'][label]=dict(initial_xyz=start,final_xyz=vals[-1],max_dz_m=max(v[2]-start[2] for v in vals),min_dz_m=min(v[2]-start[2] for v in vals),max_xy_displacement_m=max(math.dist(v[:2],start[:2]) for v in vals))
  for ordinal,b in enumerate(begin):
   e=next((x for x in end if x['started_ns']==b['started_ns'] and x['method']==b['method']),None)
   if not e:continue
   within=[x for x in sim if b['started_ns']<=x['monotonic_ns']<=e['monotonic_ns']]
   pre=[x for x in sim if x['monotonic_ns']<=b['started_ns']];s=pre[-1] if pre else sim[0]
   f=within[-1] if within else s
   arm=b['kwargs'].get('arm');robotkey=arm+'_arm' if arm else None
   # Record actual simulator keys; arm names may include suffixes.
   robotkey=next((k for k in f['robots'] if arm and k.startswith(arm)),robotkey)
   ep=flatten(f['robots'].get(robotkey,{}).get('ee_pose_world'))
   target=b['kwargs'].get('position_m')
   row=dict(condition=condition,layout_id=idx,source_layout_id=source_id,actor_episode_id=a['actor_episode_id'],ordinal=ordinal,method=b['method'],arm=arm,kwargs=b['kwargs'],planner_index=e.get('index'),begin_ns=b['started_ns'],end_ns=e['monotonic_ns'],start_action=s['native_action_count'],end_action=f['native_action_count'],logged_snapshots=len(within),alignment_pre_gap_ms=(b['started_ns']-s['monotonic_ns'])/1e6,return_event=e['event'],result=e.get('result'),error=e.get('error'),actual_ee_pose_world=ep,commanded_target=target,ee_translation_error_m=math.dist(ep[:3],target) if isinstance(ep,list) and len(ep)==7 and target else None,objects={})
   for label,v in poses.items():
    start=xyz(s['objects'].get(label,{}));finish=xyz(f['objects'].get(label,{}))
    if start and finish:row['objects'][label]=dict(start_xyz=start,end_xyz=finish,dz_from_initial_m=finish[2]-v[2],dz_during_primitive_m=finish[2]-start[2],xy_from_initial_m=math.dist(finish[:2],v[:2]))
   rows.append(row)
  raw=lines(p.parent/'raw-planner-results.jsonl')
  actor['raw_planner_results']=raw
  actor['first_error']=a['first_error'];actor['native_step_limit_cancelled']=a['native_step_limit_cancelled'];actors.append(actor)
assert len(actors)==campaign['planned_cases'],(len(actors),campaign['planned_cases'])
result=dict(state='passed' if not errors else 'logging_errors',actors=actors,primitives=rows,snapshot_count=len(records),logging_errors=errors,logging_ms=dict(median=statistics.median(x['logging_elapsed_ms'] for x in records),max=max(x['logging_elapsed_ms'] for x in records)),scope='Privileged side-channel analysis only; original observations and decision inputs unchanged. Native video frame index corresponds to action count; source_layout_id is original layout, layout_id is this subset runtime index.')
(A/'postgrasp-analysis.json').write_text(json.dumps(result,indent=2)+'\n')
with (A/'primitive-alignment.csv').open('w',newline='') as f:
 fields=[k for k in rows[0] if k!='objects'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
 for x in rows:w.writerow({k:json.dumps(x[k]) if isinstance(x[k],(dict,list)) else x[k] for k in fields})
print(json.dumps(dict(actors=len(actors),primitives=len(rows),snapshots=len(records),logging_errors=len(errors),scores=[x['score'] for x in actors])))
