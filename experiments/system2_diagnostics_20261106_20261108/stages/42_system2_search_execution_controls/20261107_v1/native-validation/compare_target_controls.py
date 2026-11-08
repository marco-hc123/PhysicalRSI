"""Paired layout accounting and treatment-adherence audit, no native reruns."""
import csv,datetime,hashlib,json,math
from pathlib import Path
O=Path(__file__).resolve().parent;P=O/'repair';read=lambda p:json.loads(p.read_text())
assert read(P/'analysis/independent-validation.json')['state']=='passed'
m=read(P/'analysis/matrix-analysis.json');physical=read(P/'analysis/mechanism-diagnostics.json');replay=read(P/'analysis/source-stop-replay-v2.json');campaign=read(P/'native-campaign/campaign.json')
entries={x['name']:x for x in campaign['entries']};sources=[];memories=[];configs=[]
for name in ['target_control','target_offset']:
 e=entries[name];h=Path(e['harness']['root']);sources.append((h/'code/classify_objects.py').read_bytes());memories.append(read(h/'memory_rules.json')['classify_objects']);configs.append(read(Path(e['runtime'])))
assert sources[0]==sources[1]
memory_changes=[k for k in set(memories[0])|set(memories[1]) if memories[0].get(k)!=memories[1].get(k)]
assert memory_changes==['experiment_target_rule']
assert [x['experiment_target_rule'] for x in memories]==['generated','incumbent_offset']
assert configs[0]['policy_spec']['entrypoint']==configs[1]['policy_spec']['entrypoint']=='structured_feedback:assemble'
assert {k:v for k,v in configs[0]['policy_spec']['configuration'].items() if k!='output'}=={k:v for k,v in configs[1]['policy_spec']['configuration'].items() if k!='output'}
rows=[]
for layout in range(5):
 row=dict(layout_id=layout);firsts=[]
 for name in ['target_control','target_offset']:
  e=next(x for x in m['episodes'] if x['condition']==name and x['layout_id']==layout)
  a=next((x for x in m['actors'] if x['condition']==name and x['mapped_layout_id']==layout),None)
  d=next((x for x in physical['cases'] if x['condition']==name and x['layout_id']==layout),{})
  row[name+'_score_100']=e['normalized_score']*100;row[name+'_full_success']=e['success'];row[name+'_first_release_observed']=d.get('release_observed');row[name+'_first_object_delivery_proxy']=d.get('selected_object_delivered_proxy');row[name+'_first_cycle_physical_diagnosis']=d.get('physical_diagnosis')
  if a:
   trace=read(P/a['process_record']);initial=next((x['request']['kwargs'] for x in trace['calls'] if x['request']['method']=='approach'),None);firsts.append(initial)
   stop=next(x for x in replay['cases'] if x['actor_episode_id']==a['actor_episode_id'])
   row[name+'_rpc_calls']=a['rpc_calls'];row[name+'_accepted_approaches']=a['accepted_approach_calls'];row[name+'_rejected_approaches']=a['rejected_approach_calls'];row[name+'_stop_line']=stop.get('policy_exit_line') if stop['qualified_return_location'] else None;row[name+'_native_budget_cancelled']=a['native_step_limit_cancelled']
  else:firsts.append(None)
 row['score_delta_100']=row['target_offset_score_100']-row['target_control_score_100']
 row['initial_approach_same_arm']=firsts[0]['arm']==firsts[1]['arm'] if all(firsts) else None
 row['initial_target_position_difference_m']=math.dist(firsts[0]['position_m'],firsts[1]['position_m']) if all(firsts) else None
 rows.append(row)
out=dict(state='completed',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_identical_across_groups=True,source_sha256=hashlib.sha256(sources[0]).hexdigest(),memory_only_changed_key=memory_changes,executor_unchanged=True,pairs=rows,mean_score_delta_100=sum(x['score_delta_100'] for x in rows)/5,positive_score_pairs=sum(x['score_delta_100']>0 for x in rows),negative_score_pairs=sum(x['score_delta_100']<0 for x in rows),zero_score_pairs=sum(x['score_delta_100']==0 for x in rows),scope='One categorical targetXY intervention in a fixed manually instrumented sample_01 source. Small paired-layout control, control-first cohort order; perception/execution remain stochastic. Source rule for arm choice is unchanged; observed initial arm/target equality is separately measured. Later action differences are downstream effects, not separately manipulated factors.')
p=P/'analysis/target-control-comparison.json';assert not p.exists();p.write_text(json.dumps(out,indent=2)+'\n')
with (P/'analysis/target-control-pairs.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for x in rows for k in x)));w.writeheader();w.writerows(rows)
print(json.dumps({k:out[k] for k in ['state','mean_score_delta_100','positive_score_pairs','negative_score_pairs','zero_score_pairs']}))
