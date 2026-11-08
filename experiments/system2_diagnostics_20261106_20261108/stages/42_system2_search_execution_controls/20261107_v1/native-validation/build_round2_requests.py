"""Freeze one updated development-feedback packet, then produce 3 identical requests."""
import copy,datetime,hashlib,json,subprocess,sys
from pathlib import Path
O=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for phase in ['parent','sampling','repair']:
 assert read(O/phase/'analysis/independent-validation.json')['state']=='passed'
assert not (O/'heldout-layouts').exists()
if not (O/'repair/analysis/target-control-comparison.json').exists():
 subprocess.run([sys.executable,'-B',str(O/'compare_target_controls.py')],check=True)
selection=read(O/'sampling-selection.json');selected=selection['budget5']['selected']
phase='parent' if selected=='fixed_parent' else 'sampling'
campaign=read(O/phase/'native-campaign/campaign.json');entry=next(x for x in campaign['entries'] if x['name']==selected)
cfg=read(Path(entry['runtime']))
assert cfg['policy_spec']['entrypoint']=='structured_feedback:assemble'
for re in read(O/'repair/native-campaign/campaign.json')['entries']:
 rcfg=read(Path(re['runtime']))
 assert rcfg['policy_spec']['entrypoint']==cfg['policy_spec']['entrypoint']
 canonical=lambda c:{k:v for k,v in c['policy_spec']['configuration'].items() if k!='output'}
 assert canonical(rcfg)==canonical(cfg),'Executor changed; require pool revalidation rather than continue this builder'
h=Path(entry['harness']['root']);source=(h/'code/classify_objects.py').read_text();memory=read(h/'memory_rules.json')['classify_objects']
initial=read(O/'requests/sample_01.json');packet=json.loads(initial['messages'][1]['content']);packet['current_code']=source;packet['memory']=memory
api=packet['primitive_api'];api['budget'].update(robot_rpc_calls=100,isolated_timeout_seconds=1500,primitive_deadline_seconds=180)
api['budget']['scope']='All scene/reobserve/approach/gripper RPCs count toward100; this is distinct from1100native action steps. Initial-round prompt omitted100RPCcap; it remains unchanged retrospectively.'
matrix=read(O/phase/'analysis/matrix-analysis.json');replays=read(O/phase/'analysis/source-stop-replay-v2.json')
actors=[]
for a in matrix['actors']:
 if a['condition']!=selected:continue
 proc=read(O/phase/a['process_record']);calls=proc['calls'];s=next(x for x in replays['cases'] if x['actor_episode_id']==a['actor_episode_id'])
 recent=[]
 for c in calls[-6:]:
  req=c['request'];response=c.get('response',{});value=response.get('value',{})
  recent.append(dict(method=req['method'],kwargs=req.get('kwargs',{}),call_id=req['id'],recorded_response='incomplete' if not response else 'exception' if 'error' in response else value.get('primitive_error','returned') if isinstance(value,dict) else 'returned'))
 actors.append(dict(layout_id=a['mapped_layout_id'],rpc_calls=a['rpc_calls'],completed_approaches=a['accepted_approach_calls'],rejected_approaches=a['rejected_approach_calls'],native_budget_cancelled=a['native_step_limit_cancelled'],return_location=s['policy_exit_source'] if s.get('qualified_return_location') else None,return_line=s.get('policy_exit_line') if s.get('qualified_return_location') else None,recorded_recent_calls=recent))
sampling=read(O/'sampling/analysis/matrix-analysis.json');repair=read(O/'repair/analysis/matrix-analysis.json');diagnosis=read(O/'repair/analysis/mechanism-diagnostics.json')
repair_replay=read(O/'repair/analysis/source-stop-replay-v2.json');repair_stops=[]
for a in repair['actors']:
 proc=read(O/'repair'/a['process_record']);s=next(x for x in repair_replay['cases'] if x['actor_episode_id']==a['actor_episode_id']);recent=[]
 for c in proc['calls'][-4:]:
  req=c['request'];response=c.get('response',{});value=response.get('value',{})
  recent.append(dict(method=req['method'],kwargs=req.get('kwargs',{}),call_id=req['id'],recorded_response='incomplete' if not response else 'exception' if 'error' in response else value.get('primitive_error','returned') if isinstance(value,dict) else 'returned'))
 repair_stops.append(dict(condition=a['condition'],layout_id=a['mapped_layout_id'],rpc_calls=a['rpc_calls'],native_budget_cancelled=a['native_step_limit_cancelled'],return_line=s.get('policy_exit_line') if s.get('qualified_return_location') else None,return_source=s.get('policy_exit_source') if s.get('qualified_return_location') else None,recent_recorded_calls=recent))
scores=lambda m,n:[x['normalized_score']*100 for x in sorted([x for x in m['episodes'] if x['condition']==n],key=lambda x:x['layout_id'])]
repair_summary=[]
for c in repair['cohorts']:
 rows=[x for x in diagnosis['cases'] if x['condition']==c['condition']]
 repair_summary.append(dict(condition=c['condition'],native_scores_100=scores(repair,c['condition']),full_successes=c['successes'],accepted_approaches=c['accepted_approach_calls'],rejected_approaches=c['total_approach_calls']-c['accepted_approach_calls']-c['incomplete_approach_calls'],first_manipulation_release_observed=sum(bool(x.get('release_observed')) for x in rows),first_object_stable_delivery_proxy=sum(bool(x.get('selected_object_delivered_proxy')) for x in rows),scope='Aggregate post-hoc execution diagnosis; no hidden object coordinates, contact force, or heldout evidence supplied'))
packet['development_feedback']=dict(selected_parent=selected,selection_rule=selection['rule'],selected_parent_scores_100=scores(matrix,selected),selected_parent_execution=actors,initial_pool=[dict(condition=c['condition'],native_scores_100=scores(sampling,c['condition']),full_successes=c['successes'],accepted_approaches=c['accepted_approach_calls'],incomplete_approaches=c['incomplete_approach_calls']) for c in sampling['cohorts']],manual_target_control=dict(implementation=(O/'manual-target-control/source.diff').read_text(),results=repair_summary,authorship='Researcher-designed single categorical destinationXY intervention on sample_01; all other candidate logic/runtime unchanged. Not a model-generated improvement. The original candidate and this current parent remain unchanged.'),evaluation_contract=dict(partial_levels_100=[15,40,100],semantics='Native transition scoring for completed separated category groups; a moved object alone is not task success. Both grippers must be sufficiently open for relevant transitions. Full success additionally requires both robot end poses near their initial poses.',interface_gap='Four exposed methods do not include an explicit home primitive or a guaranteed initial Cartesian end pose. Do not invent an API or assume returning code returns arms home.'),limitations=['Development layouts already exposed; no new-layout evidence in feedback.','No-path is a zero-execution rejection, not proof of failed grasp or absence of an object.','Program return, physical object delivery, partial score and full success are distinct.','First-cycle diagnostic aggregates cannot certify every later transfer.','This second packet includes new feedback, a clarified budget and manual-control evidence; differences from round1 cannot be attributed solely to more samples or autonomous feedback learning.'])
for row,actor in zip(actors,[x for x in matrix['actors'] if x['condition']==selected]):
 row.update(actor_final_state=actor['actor_final_state'],actor_error=actor['actor_error'])
for row,actor in zip(repair_stops,repair['actors']):
 row.update(actor_final_state=actor['actor_final_state'],actor_error=actor['actor_error'])
for summary in repair_summary:
 relevant=[x for x in diagnosis['cases'] if x['condition']==summary['condition']]
 summary['unknown_first_object_physical_associations']=sum(not x.get('source_association',{}).get('qualified',False) for x in relevant)
 summary['unknown_release_observation_cases']=sum(x.get('release_observed') is None for x in relevant)
packet['instruction']+=' This is round2: use the recorded development feedback. Produce your own complete unchanged proposal for evaluation. Avoid assuming basket-center endpoints or higher clearance are feasible; use only API-visible geometry and bounded alternatives. All three proposals use this identical packet and are retained even if rejected or unsuccessful.'
packet['development_feedback']['manual_target_control']['execution_stops']=repair_stops
packet['development_feedback']['manual_target_control']['controlled_source']=(O/'manual-target-control/candidate.py').read_text()
packet['development_feedback']['manual_target_control']['memory_flags']={'target_control':'generated','target_offset':'incumbent_offset'}
pool_replay=read(O/'sampling/analysis/source-stop-replay-v2.json');representatives=[]
for condition in [f'sample_{i:02}' for i in range(1,6)]:
 a=next(x for x in sampling['actors'] if x['condition']==condition and x['mapped_layout_id']==0)
 proc=read(O/'sampling'/a['process_record']);stop=next(x for x in pool_replay['cases'] if x['actor_episode_id']==a['actor_episode_id']);calls=proc['calls'];brief=[]
 selected_calls={x['request']['id']:x for x in calls[:4]+calls[-4:]}
 for c in selected_calls.values():
  req=c['request'];response=c.get('response',{});value=response.get('value',{})
  brief.append(dict(method=req['method'],kwargs=req.get('kwargs',{}),call_id=req['id'],recorded_response='incomplete' if not response else 'exception' if 'error' in response else value.get('primitive_error','returned') if isinstance(value,dict) else 'returned'))
 lines=(O/'candidates'/condition/'candidate.py').read_text().splitlines();line=stop.get('policy_exit_line') if stop['qualified_return_location'] else None
 representatives.append(dict(condition=condition,development_layout_id=0,selection_scope='Same prespecified representative layout for all proposals, not best/worst outcome selection',accepted_approaches=a['accepted_approach_calls'],rejected_approaches=a['rejected_approach_calls'],gripper_calls=len(a['gripper_commands']),first_and_last_recorded_calls=brief,return_source_context=[dict(line=i+1,text=lines[i]) for i in range(max(0,(line or 1)-4),min(len(lines),(line or 1)+2))] if line else None))
packet['development_feedback']['initial_pool_representative_execution']=representatives
request=copy.deepcopy(initial);request['messages'][1]['content']=json.dumps(packet,sort_keys=True,ensure_ascii=False)
raw=(json.dumps(request,ensure_ascii=False,indent=2)+'\n').encode();assert len(raw)<=read(O/'protocol.json')['max_request_bytes']
requests=[]
for i in range(1,4):
 name=f'round2_{i:02}';p=O/'requests'/(name+'.json');assert not p.exists();p.write_bytes(raw);requests.append(dict(id=name,file=str(p.relative_to(O)),sha256=sha(p)))
assert len({x['sha256'] for x in requests})==1
control=O/'round2-generation.json';assert not control.exists();control.write_text(json.dumps(dict(requests=requests),indent=2)+'\n')
freeze=dict(frozen_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),heldout_seen=False,selected_parent=selected,parent_entry=entry,baseline_executor_preserved=True,manual_target_control_not_promoted=True,scope='Current generated-candidate pool remains under its original executor. Manual target control is separately reported, and only contributes development feedback. This is a feedback-informed second search round, not an isolated estimate of round count.',feedback_sha256=hashlib.sha256(json.dumps(packet,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),request_bytes=len(raw),request_sha256=sha(O/requests[0]['file']),evidence=[dict(path=str(p.relative_to(O)),sha256=sha(p)) for p in [O/'sampling-selection.json',O/'sampling/analysis/matrix-analysis.json',O/'repair/analysis/matrix-analysis.json',O/'manual-target-control/design-final.json']])
(O/'execution-final.json').write_text(json.dumps(freeze,indent=2)+'\n')
(O/'round2-plan.json').write_text(json.dumps(dict(entries=[dict(name=x['id'],source='candidates/'+x['id']+'/candidate.py',proposal='candidates/'+x['id']+'/proposal.json') for x in requests],selection='Strict improvement over selected round1 parent on the same exposed five layouts; incumbent wins ties',research_role='Three unchanged model-generated round2 candidates, same frozen baseline executor; updated fixed development feedback includes separate manual-control evidence'),indent=2)+'\n')
print(json.dumps(dict(state='requests_frozen',selected_parent=selected,requests=3,identical_bytes=len(raw),sha256=requests[0]['sha256'])))
