"""Read-only campaign analysis; write only a separately specified report folder.

Actor mapping uses same-host monotonic intervals. No UUID sort inference.
Terminal cancellation is interpreted together with the native outcome.
"""
import collections,csv,hashlib,json,sys
from pathlib import Path
O=Path(sys.argv[1]).resolve();D=Path(sys.argv[2]).resolve();D.mkdir(parents=True,exist_ok=True)
assert D!=O and not D.is_relative_to(O),'Keep posthoc analysis outside sealed original archive'
def read(p):return json.loads(p.read_text())
def jsonl(p):return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
s=read(O/'FINAL_SUMMARY.json');assert s['state']=='completed'
sources=[];actors=[];physics=[];issues=[]
def record_source(p):sources.append(dict(path=str(p.relative_to(O)),sha256=digest(p)))
record_source(O/'FINAL_SUMMARY.json')
for stage in s['stage_accounting']:
 phase=stage['phase'];root=O/phase;campaign=read(root/'native-campaign/campaign.json');record_source(root/'native-campaign/campaign.json')
 for entry in campaign['entries']:
  cond=entry['name'];runs=list((root/'native-campaign/runs'/cond).glob('attempt-*'))
  partial=read(root/'analysis/summary.json')['state']=='verified_partial'
  runs=[r for r in runs if (r/'native/run/observed.json').exists() and (partial or not read(r/'native/run/observed.json').get('failures'))]
  assert len(runs)==1,(phase,cond,'ambiguous completed run')
  run=runs[0];obs=read(run/'native/run/observed.json');record_source(run/'native/run/observed.json')
  outcomes={int(r['layout_id']):r for r in obs['outcomes']};snapgroups=collections.defaultdict(list)
  for p in sorted((root/'sim-diagnostics'/cond).glob('*.jsonl')):
   record_source(p)
   for r in jsonl(p):
    if r.get('event')=='snapshot':snapgroups[int(r['layout_seed'])].append(r)
    elif r.get('event')=='logging_error':issues.append(dict(phase=phase,condition=cond,error=r))
  windows={k:(min(x['monotonic_ns'] for x in rs),max(x['monotonic_ns'] for x in rs)) for k,rs in snapgroups.items()}
  assert all(k in outcomes or (partial and k in range(len(campaign['cases']))) for k in snapgroups),(phase,cond,'unexplained sidecar layout')
  for k,rs in snapgroups.items():
   rs.sort(key=lambda x:x['monotonic_ns']);out=outcomes.get(k,dict(episode_score=None,success=None,action_count=None,step_limit=None))
   targets=[x['objects'].get('target',{}).get('position_world') for x in rs]
   targets=[x for x in targets if isinstance(x,list) and len(x)==3]
   physics.append(dict(phase=phase,condition=cond,task=stage['task'],layout_id=k,score=out['episode_score'],success=out['success'],native_action_count=out['action_count'],step_limit=out['step_limit'],sidecar_snapshots=len(rs),snapshot_first_action=rs[0]['native_action_count'],snapshot_last_action=rs[-1]['native_action_count'],initial_target_z=targets[0][2] if targets else None,max_target_root_lift_m=max(x[2] for x in targets)-targets[0][2] if targets else None,final_target_root_lift_m=targets[-1][2]-targets[0][2] if targets else None,metric_scope='Analysis-only object-root delta; native scoring remains authoritative. No hidden state was supplied to the policy.'))
  for p in sorted((run/'model/expert').glob('*/0/policy/processes/isolated/process.json')):
   record_source(p);r=read(p);actor=p.parents[4].name;calls=r.get('calls',[])
   assert [x['request']['id'] for x in calls]==list(range(len(calls)))
   q=root/'backend-traces'/cond/actor/'0/primitive-events.jsonl';events=jsonl(q) if q.exists() else []
   if q.exists():record_source(q)
   begins=[e for e in events if e.get('event')=='begin'];t=begins[0].get('monotonic_ns') if begins else None
   candidates=[k for k,(a,b) in windows.items() if t is not None and a<=t<=b]
   assert len(candidates)<=1,(phase,cond,actor,'ambiguous actor-to-layout interval')
   layout=candidates[0] if candidates else None;native=outcomes.get(layout)
   last=calls[-1] if calls else {};value=(last.get('response') or {}).get('value');rejected=isinstance(value,dict) and bool(value.get('primitive_error'))
   errors=[e.get('error','') for e in events if e.get('event')=='exception'];closed=any('Actor channel closed' in e for e in errors)
   if r.get('state')=='failed' and closed and native and native['success']:kind='native_success_terminated_active_call'
   elif r.get('state')=='failed' and closed and native and native['action_count']==native['step_limit']:kind='native_limit_terminated_active_call'
   elif r.get('state')=='failed' and 'Observed robot diverged from planned trajectory' in str(r.get('error')):kind='execution_tracking_divergence_missing_terminal_score'
   elif r.get('state')=='failed':kind='process_failure_unclassified'
   elif rejected:kind='program_returned_after_explicit_rejection'
   elif last.get('request',{}).get('method') in ['scene','reobserve']:kind='program_returned_after_observation'
   else:kind='program_returned_other'
   method_counts=collections.Counter(x['request']['method'] for x in calls)
   rejectcalls=[x for x in calls if isinstance((x.get('response') or {}).get('value'),dict) and (x['response']['value'].get('primitive_error'))]
   actors.append(dict(phase=phase,condition=cond,task=stage['task'],actor_uuid=actor,layout_id=layout,mapping='same-host first-primitive monotonic timestamp within native snapshot interval' if layout is not None else 'unmapped: no unique primitive-time evidence; no score assigned',native_score=native['episode_score'] if native else None,native_success=native['success'] if native else None,process_state=r.get('state'),process_returncode=r.get('returncode'),observed_stop_class=kind,calls=len(calls),approach_requests=method_counts['approach'],gripper_requests=method_counts['gripper'],scene_requests=method_counts['scene'],explicit_rejections=len(rejectcalls),last_method=last.get('request',{}).get('method'),last_call_state=last.get('state'),last_rejection=value.get('primitive_error') if rejected else None,primitive_exceptions=errors,source=str(p.relative_to(O)),first_primitive_monotonic_ns=t,scope='Observed termination pattern, not a complete causal attribution or a physical success classifier'))
groups=[]
for phase,cond in sorted({(r['phase'],r['condition']) for r in actors}):
 rs=[r for r in actors if r['phase']==phase and r['condition']==cond]
 groups.append(dict(phase=phase,condition=cond,actors=len(rs),mapped_actors=sum(r['layout_id'] is not None for r in rs),stop_counts=dict(collections.Counter(r['observed_stop_class'] for r in rs)),approach_requests=sum(r['approach_requests'] for r in rs),explicit_rejections=sum(r['explicit_rejections'] for r in rs)))
out=dict(state='completed',scope='Posthoc CPU audit of completed, archived campaign. Read-only original evidence; no new rollouts or API requests.',actors=actors,physics=physics,groups=groups,logging_issues=issues,source_hashes=sources,important='Success-triggered actor shutdown is not a strategy failure. Actor-to-layout mapping is unknown when no unique monotonic interval is available. Process completion does not imply native task success.')
(D/'mechanism-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
for name,rows in [('actor-stop-patterns.csv',actors),('native-physical-proxies.csv',physics),('stop-pattern-summary.csv',groups)]:
 if not rows:continue
 with (D/name).open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows([{k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in r.items()} for r in rows])
print(json.dumps(dict(state='completed',actors=len(actors),mapped=sum(r['layout_id'] is not None for r in actors),native_sidecar_episodes=len(physics),logging_issues=len(issues),groups=groups)))
