"""Combine verified phase accounting without counting reused evidence as new runs."""
import csv,datetime,hashlib,json
from pathlib import Path
O=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
phases=['parent','sampling','repair','round2','heldout'];accounting=[];cohorts=[];episodes=[];phase_data={}
accounting.append(dict(stage='route1_evidence_freeze',actual_native_episodes=0,unique_layouts=0,strategies=0,original_videos=0,paid_api_requests=0,evidence_reused_as_new_episodes=0,note='Previously archived10capability-diagnostic episodes referenced, not rerun or added to this campaign total; environment/source and result references are frozen separately'))
for name in phases:
 validation=read(O/name/'analysis/independent-validation.json');assert validation['state']=='passed'
 m=read(O/name/'analysis/matrix-analysis.json');assert m['complete'] and m['qualified_cases']==validation['valid_native_cases']
 phase_data[name]=m
 accounting.append(dict(stage=name,actual_native_episodes=m['qualified_cases'],unique_layouts=len(m['layouts']),strategies=len(m['cohorts']),original_videos=validation['decoded_videos'],paid_api_requests=0,evidence_reused_as_new_episodes=0,note='Fresh native evaluations; phase-specific rows and receipts are authoritative'))
 for row in m['cohorts']:cohorts.append(dict(stage=name,**row))
 for row in m['episodes']:episodes.append(dict(stage=name,**row))
ledger=read(O/'ledger.json');assert len(ledger)<=8
assert all(x.get('state') in ['received','failed'] for x in ledger)
api=[]
for b in ['sampling','round2']:
 rows=[x for x in ledger if x['batch']==b];usage={k:sum(x.get('usage',{}).get(k,0) for x in rows) for k in ['prompt_tokens','completion_tokens','total_tokens']}
 cached=sum((x.get('usage',{}).get('prompt_tokens_details') or {}).get('cached_tokens',0) for x in rows)
 cache_write=sum((x.get('usage',{}).get('prompt_tokens_details') or {}).get('cache_write_tokens',0) for x in rows)
 reasoning=sum((x.get('usage',{}).get('completion_tokens_details') or {}).get('reasoning_tokens',0) for x in rows)
 api.append(dict(batch=b,requests=len(rows),http200=sum(x.get('http_status')==200 for x in rows),parsed_candidates=sum(bool(x.get('syntax_valid')) for x in rows),**usage,cached_input_subset=cached,cache_write_input_subset=cache_write,reasoning_output_subset=reasoning,reported_models=sorted({x.get('returned_model','unknown') for x in rows}),estimated_usd=sum(x.get('estimated_standard_usd',0) for x in rows)))
 accounting.append(dict(stage=b+'_generation',actual_native_episodes=0,unique_layouts=0,strategies=0,original_videos=0,paid_api_requests=len(rows),evidence_reused_as_new_episodes=0,note='API-only candidate generation; cache subset of input, reasoning subset of output'))
eligibility=read(O/'heldout-eligibility.json');assert eligibility['state']=='passed'
accounting.append(dict(stage='heldout_layout_qualification',actual_native_episodes=0,unique_layouts=5,strategies=0,original_videos=0,paid_api_requests=0,evidence_reused_as_new_episodes=0,note='Five native reset checks with zero policy actions; not scored task episodes'))
selection=read(O/'selection-final.json');test=phase_data['heldout'];strategies=[]
for a in selection['strategies']:
 c=next(x for x in test['cohorts'] if x['condition']==a['evaluated_as']);q=[x for x in test['episodes'] if x['condition']==a['evaluated_as']]
 strategies.append(dict(**a,heldout_cases=len(q),heldout_scores_100=[x['normalized_score']*100 for x in sorted(q,key=lambda x:x['layout_id'])],heldout_successes=c['successes'],heldout_mean_score_100=c['mean_normalized_score']*100,evidence_group=a['evaluated_as']))
summary=dict(state='completed',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),completed_native_phases=phases,actual_native_episodes=sum(x['actual_native_episodes'] for x in accounting),original_videos=sum(x['original_videos'] for x in accounting),native_layout_initializations=5,paid_api_requests=len(ledger),api_usage=api,estimated_new_api_usd=sum(x['estimated_usd'] for x in api),cost_note='Provider usage and posted standard rates; invoice authoritative. Cumulative reserved exposure including prior allowance remains below10USD.',lab_gpu_used=False,development_layouts=5,independent_heldout_layouts=5,heldout_unique_strategies=len(test['cohorts']),heldout_logical_strategy_views=len(strategies),heldout_evidence_reuse_views=len(strategies)-len(test['cohorts']),search_selection=selection,heldout_strategies=strategies,global_policy_registry_modified=False,scope='Study-specific code candidates under frozen RGB/CuRobo execution. Current fixed parent is a code candidate, not pi05. Manual target repair is separately labeled. No model training, no cross-project speed or token-reduction claim.',limits=['One candidate pool and five development layouts; small descriptive study, not population inference.','Historical Qwen/medium and current GPT/high are not matched sampling-only conditions.','Round2 changes feedback and adds candidates; it does not separately identify the causal effects of more samples, feedback or rounds.','Manual target-control evidence in round2 is researcher assistance, not autonomous discovery.','Program return, object delivery, category partial score and full success are distinct.','Heldout strategy aliases share physical evidence and must not be treated as independent replications.','No explicit home primitive in the exposed interface; full native success includes a return-to-origin condition.','Original full model weights/environments remain external pinned dependencies, not duplicated experiment output.'])
def table(name,rows):
 fields=list(dict.fromkeys(k for r in rows for k in r))
 with (O/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
  for row in rows:w.writerow({k:json.dumps(v) if isinstance(v,(list,dict)) else v for k,v in row.items()})
for n,rows in [('stage-accounting.csv',accounting),('all-cohorts.csv',cohorts),('all-episodes.csv',episodes),('api-usage.csv',api),('heldout-strategy-views.csv',strategies)]:table(n,rows)
p=O/'FINAL_SUMMARY.json';assert not p.exists();p.write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:summary[k] for k in ['state','actual_native_episodes','original_videos','paid_api_requests','estimated_new_api_usd','heldout_unique_strategies']}))
