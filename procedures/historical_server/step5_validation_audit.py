"""Audit both formal rounds and their explicit interface-inspection policy bridge."""
from pathlib import Path
from datetime import datetime,timezone
from statistics import mean
import csv,fcntl,inspect,json,os,subprocess,sys
R=Path('/mnt/data/physical-RSI');O=Path(sys.argv[1]).resolve();Z=O/'final-audit';Z.mkdir(exist_ok=True)
lock=(Z/'audit.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
def read(p):return json.loads(Path(p).read_text())
cfg=read(O/'runtime.json');os.environ.update(cfg['policy_environment']);sys.path[:0]=cfg['policy_environment']['PYTHONPATH'].split(':')
from PhysicalRSI_core.infra.storage import atomic_json,file_digest,digest
from PhysicalRSI_core.infra.isolation import execute
from PhysicalRSI_core.self_harness.artifacts import verify_harness
from PhysicalRSI_core.lineage import HarnessState
from PhysicalRSI_baselines.robodojo import evidence
from PhysicalRSI_baselines.robodojo.workflow import Selector
p=read(O/'protocol.json');P=Path(p['reuse_development']['directory']);Q=Path(p['prior_attempt']);M=R/'result/28_system2_interface_20261030T102000Z'
assert len(read(O/'iteration-result.json')['rounds'])==1
assert read(O/'native-budget.json')['requested']==read(O/'native-budget.json')['completed']==10
assert read(P/'native-budget.json')['requested']==read(P/'native-budget.json')['completed']==20
assert not list((O/'proposal-api').glob('call-*'))
assert inspect.signature(execute).parameters['max_calls'].default==100
for root in (P,O):
 pr=read(root/'protocol.json')
 assert file_digest(root/'runtime.json')==pr['configuration_sha256']
 assert file_digest(root/'workflow-configuration.json')==pr['workflow_configuration_sha256']
 for f,h in pr['sources'].items():assert file_digest(Path(f))==h,f
for group in ('reuse_development','completed_proposal'):
 for f,h in p[group]['files'].items():assert file_digest(Path(f))==h,f
assert file_digest(Path(p['selected_parent_commit']))==p['selected_parent_commit_sha256']
seen=set(read(P/'historical-exclusions.json')['hashes']);rounds=[];phase_times=[];commits=[]
workspaces=[P/'workspace/rounds/round-000000',O/'workspace/rounds/round-000000']
for logical,w in enumerate(workspaces):
 def completed(name):
  row=read(w/(name+'.json'));assert row['state']=='completed' and digest(row['output'])==row['output_sha256'];return row['output']
 parent=read(w/'parent.json');assert verify_harness(parent['harness'])==parent['freeze_sha256']
 dev=read(w/'development-cases.json');assert len(dev)==5
 if logical==0:assert dev==read(Q/'workspace/rounds/round-000000/development-cases.json')
 else:
  assert dev==read(P/'workspace/rounds/round-000001/development-cases.json')
  for case in dev:assert case['layout_sha256'] not in seen;seen.add(case['layout_sha256'])
 for case in dev:evidence.verify_case(case,w/'development-layouts')
 feedback=read(w/'development-results.json');assert len(feedback)==10
 children=completed('propose');assert len(children)==1;child=children[0]
 for key in ('foundation','weights'):assert child['components'][key]==parent['harness']['components'][key]
 comparison=completed('freeze');cohort=completed('validation');val=read(w/'validation-cases.json');assert len(val)==5 and cohort['generated_at']>comparison['frozen_at']
 for case in val:
  assert case['layout_sha256'] not in seen;seen.add(case['layout_sha256']);evidence.verify_case(case,w/'validation-layouts')
 harnesses={parent['harness']['id']:parent['harness'],child['id']:child}
 assert comparison['candidates']=={name:verify_harness(h) for name,h in harnesses.items()}
 reports=[completed('evaluate_'+name) for name in comparison['candidates']]
 assert all(row['evaluator_revision']==read(w/'config.json')['protocol']['identity'] for row in reports)
 decision=Selector().select(comparison,cohort,reports,evidence_root=w);assert decision==completed('selection')
 commit=read(w/'commit.json');assert commit['previous']==parent['revision'] and commit['decision']==decision and commit['harness']['id']==decision['survivor_id']
 for f,h in commit['evidence'].items():assert file_digest(Path(f))==h
 assert HarnessState(w.parent.parent/'state').resolve()['revision']==commit['revision'];commits.append(commit)
 prop=read(w/'proposals/classify_objects/skill-proposal.json');gate=read(w/'proposals/classify_objects/cpu-contract-gate/gate-result.json')
 assert gate['passed'] and len(gate['cases'])==3 and not gate['physical_qualification']
 if logical==1:assert all(row['contract_prefix_valid'] and row['native_call_budget_unchanged']==100 for row in gate['cases'].values())
 src=read(Path(child['root'])/'skills.json')['code.classify_objects']['source']
 assert (Path(child['root'])/src).read_text()==prop['source']
 assert read(Path(child['root'])/'memory_rules.json')['classify_objects']==prop['memory']
 assert prop['development_feedback_sha256']==digest(feedback)
 model_root=M if logical==0 else P
 actual=json.loads(read(model_root/'proposal-api/call-0001/response.json')['choices'][0]['message']['content'])
 assert actual['source']==prop['source'] and actual['memory']==prop['memory']
 reuse=read(w/'proposals/classify_objects/completed-proposal-reuse.json');assert reuse['new_http_attempts']==0 and reuse['source_sha256']==digest(prop['source'])
 original_w=model_root/('workspace/rounds/round-%06d/proposals/classify_objects'%logical)
 request=read(w/'proposals/classify_objects/request.json');assert request==read(original_w/'request.json')
 strip=lambda rows:[{k:v for k,v in r.items() if k not in ('evidence','evidence_receipt')} for r in rows]
 assert strip(request['development_feedback'])==strip(feedback)
 for f in w.glob('*.json'):
  row=read(f)
  if isinstance(row,dict) and row.get('state')=='completed' and 'started_at' in row and 'finished_at' in row:
   phase_times.append(dict(logical_round=logical,phase=f.stem,elapsed_s=(datetime.fromisoformat(row['finished_at'])-datetime.fromisoformat(row['started_at'])).total_seconds(),receipt=str(f)))
 rounds.append(dict(index=logical,development={name:dict(episodes=len(a:=[r for r in feedback if r['expert']==name]),successes=sum(r['success'] for r in a),mean_native_score=mean(r['episode_score'] for r in a)) for name in sorted({r['expert'] for r in feedback})},
  paired_validation={row['candidate_id']:dict(episodes=len(row['episodes']),successes=sum(r['success'] for r in row['episodes']),mean_native_score=mean(r['score'] for r in row['episodes']),scores=[r['score'] for r in row['episodes']]) for row in reports},decision=decision,revision=commit['revision'],survivor_id=commit['harness']['id'],directory=str(w)))
new_parent=read(workspaces[1]/'parent.json');bridge=read(O/'policy-bridge-registration.json')
assert new_parent['action']=='bootstrap' and new_parent['previous'] is None
assert new_parent['freeze_sha256']==commits[0]['freeze_sha256']==bridge['harness_freeze_sha256']==p['selected_parent_freeze_sha256']
assert new_parent['harness']['components']==commits[0]['harness']['components']
assert bridge['previous_revision']==commits[0]['revision'] and new_parent['policy']!=commits[0]['policy']
atomic_json(Z/'verified-policy-bridge.json',dict(verified=True,previous_revision=commits[0]['revision'],new_bootstrap_revision=new_parent['revision'],harness_freeze_sha256=new_parent['freeze_sha256'],reason='Bounded static interface inspection correction; native contract/model source unchanged',single_unchanged_policy_hash_chain=False))
episodes=[];videos=[];batches=[]
# Count original completed native evidence once; ported copies are aliases.
batches.extend(read(Q/'native-budget.json')['batches'][:10])
batches.extend(read(P/'native-budget.json')['batches']);batches.extend(read(O/'native-budget.json')['batches'])
assert len(batches)==40
for batch in batches:
 assert batch['state']=='completed' and batch['count']==1;leaf=Path(batch['output']);receipts=list((leaf/'episodes').glob('*.json'));assert len(receipts)==1
 v=read(receipts[0]);checked=evidence.episode_receipt(receipts[0],directory=leaf,task=v['task'],split=v['split'],layout_sha256=v['layout_sha256'],expert=dict(name=v['expert'],revision=v['revision']),harness_sha256=v['harness_sha256'])
 steps=v['diagnostics']['action_count'];assert 0<=steps<=1100
 films=list(leaf.rglob('*.mp4'));assert len(films)==3
 for f in films:
  info=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-count_frames','-show_entries','stream=nb_read_frames','-of','json',str(f)],text=True))['streams'][0]
  frames=int(info['nb_read_frames']);assert frames==steps+1
  videos.append(dict(path=str(f),frames=frames,bytes=f.stat().st_size))
 elapsed=(datetime.fromisoformat(batch['finished_utc'])-datetime.fromisoformat(batch['requested_utc'])).total_seconds()
 episodes.append(dict(receipt=str(receipts[0]),split=v['split'],expert=v['expert'],score=v['episode_score'],success=v['success'],steps=steps,layout_sha256=v['layout_sha256'],native_batch_elapsed_s=elapsed))
calls=[]
for logical,root in enumerate((M,P)):
 d=root/'proposal-api/call-0001';response=read(d/'response.json');done=read(d/'completed.json');start=read(d/'started.json');u=response['usage']
 assert u==done['usage'] and done['http_attempts']==1 and not start['retry'] and u['total_tokens']==u['prompt_tokens']+u['completion_tokens']
 calls.append(dict(logical_round=logical,model=read(d/'request.json')['model'],input_tokens=u['prompt_tokens'],output_tokens=u['completion_tokens'],total_tokens=u['total_tokens'],reasoning_tokens_subset_output=u['completion_tokens_details']['reasoning_tokens'],cached_tokens_subset_input=u['prompt_tokens_details']['cached_tokens'],elapsed_s=done['elapsed_s'],directory=str(d)))
prior=read(Q/'proposal-api/call-0001/completed.json')
freeze=read(R/'result/23_protocol_freeze_20261029T132917Z/source-freeze.json')
for row in freeze['deployment_files']:assert file_digest(Path(row['path']))==row['sha256']
for f,h in freeze['recorded_protocol_and_framework_hashes'].items():assert file_digest(Path(f))==h
secret=read('/home/ecs-user/.config/physicalrsi/agent.json')['api_key'].encode();text_files=0
for root in (P,O):
 for f in root.rglob('*'):
  if f.is_file() and f.suffix in ('.json','.jsonl','.log','.py','.txt','.csv'):
   assert secret not in f.read_bytes();text_files+=1
assert not subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip()
samples=[]
for root in (P,O):samples.extend(csv.DictReader((root/'gpu-telemetry.csv').open()))
utc=datetime.now(timezone.utc).isoformat();token=sum(v['total_tokens'] for v in calls)
result=dict(complete=True,utc=utc,step=5,task='classify_objects',rounds=rounds,logical_rounds=2,registered_policy_bridge=True,
 selected_revision=commits[-1]['revision'],native_episodes=40,new_native_episodes_in_final_continuation=10,reused_native_episodes=30,video_count=len(videos),video_frames=sum(v['frames'] for v in videos),
 proposal_http_attempts=2,new_http_attempts_in_final_continuation=0,proposal_input_tokens=sum(v['input_tokens'] for v in calls),proposal_output_tokens=sum(v['output_tokens'] for v in calls),proposal_total_tokens=token,proposal_http_elapsed_s=sum(v['elapsed_s'] for v in calls),
 cumulative_with_prior_failed_proposal=dict(proposal_http_attempts=3,proposal_total_tokens=token+prior['usage']['total_tokens'],proposal_http_elapsed_s=sum(v['elapsed_s'] for v in calls)+prior['elapsed_s']),
 native_batch_elapsed_s=sum(v['native_batch_elapsed_s'] for v in episodes),raw_retention='cloud_only',final_test_started=False,steps6_to8_started=False,
 qualifications=['Two bounded selected-task System2 rounds with an explicit registered inspection-policy bridge; no claim of one unchanged-policy hash chain.',
 'All actual generated source/memory unchanged. Static CPU inspection does not establish task success; original native 100-call limit retained.',
 'Small selected-task cohorts do not establish paper-level performance or generalization.',
 'Proposal/development costs are System2 costs; separate them from System1 online costs and cross-project comparisons.',
 'Native batch elapsed times include startup/execution/evidence/cleanup but exclude separate cohort reset stages; per-phase records retained.'])
atomic_json(Z/'native-episodes-and-videos.json',dict(episodes=episodes,videos=videos))
atomic_json(Z/'phase-timing.json',dict(phases=phase_times,continuation_elapsed_s=read(O/'iteration-result.json')['elapsed_s']))
atomic_json(Z/'model-usage.json',dict(calls=calls,new_http_attempts=0,unknown_usage=0))
atomic_json(Z/'verification.json',dict(complete=True,utc=utc,official_selection_verified=True,registered_policy_bridge_verified=True,candidates_match_actual_model_response=True,native_evidence_verified=40,video_count=len(videos),video_frames_verified=sum(v['frames'] for v in videos),original_deployment_pins=len(freeze['deployment_files']),original_framework_pins=len(freeze['recorded_protocol_and_framework_hashes']),credential_matches=0,text_files_checked=text_files,gpu_compute_processes=0,gpu_samples=len(samples),gpu_peak_memory_MiB=max(float(r['gpu_memory_MiB']) for r in samples),gpu_peak_util_percent=max(float(r['gpu_util_percent']) for r in samples)))
atomic_json(O/'step5-results.json',result);atomic_json(O/'step5-completion.json',dict(complete=True,utc=utc,result=str(O/'step5-results.json'),result_sha256=file_digest(O/'step5-results.json'),verification=str(Z/'verification.json')))
plan=read(R/'result/CURRENT_REPRODUCTION_PLAN.json');plan.update(updated_utc=utc,step5_complete=True,current_controller_running=False,active_controller_pid=None,active_tmux_session=None,last_completed_directory=str(O),completion_receipt=str(O/'step5-completion.json'),next_step=6,next_action='Step5 verified; next version inheritance/restart check, then independent final layouts and reproduction entry/export')
plan['steps'][4]['state']='complete; two bounded native System2 rounds, explicit registered inspection-policy bridge, official selection and source/evidence audit verified'
atomic_json(R/'result/CURRENT_REPRODUCTION_PLAN.json',plan)
status=dict(complete=True,stage='complete_verified',utc=utc,pid=None,rounds_finished=2,completion=str(O/'step5-completion.json'))
atomic_json(O/'controller-status.json',status);atomic_json(R/'result/CURRENT_STEP5.json',dict(directory=str(O),**status))
print(json.dumps(dict(complete=True,rounds=rounds,tokens=token,native_episodes=40,video_count=len(videos)),ensure_ascii=False))
