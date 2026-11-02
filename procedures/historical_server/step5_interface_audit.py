"""Verify fifth-step results without launching any model, policy or simulator."""
from pathlib import Path
from datetime import datetime,timezone
from statistics import mean
from collections import Counter
import csv,fcntl,json,os,subprocess,sys
R=Path('/mnt/data/physical-RSI');O=Path(sys.argv[1]).resolve();Z=O/'final-audit'
assert (O/'iteration-result.json').exists(), 'Wait for scientific iterations; never replay them for audit'
Z.mkdir(exist_ok=True)
audit_lock=(Z/'audit.lock').open('a');fcntl.flock(audit_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
cfg=json.loads((O/'runtime.json').read_text());os.environ.update(cfg['policy_environment']);sys.path[:0]=cfg['policy_environment']['PYTHONPATH'].split(':')
from PhysicalRSI_core.infra.storage import atomic_json,read_json,file_digest,digest
from PhysicalRSI_core.self_harness.artifacts import verify_harness
from PhysicalRSI_core.lineage import HarnessState
from PhysicalRSI_baselines.robodojo import evidence
from PhysicalRSI_baselines.robodojo.workflow import Selector
from importlib.util import spec_from_file_location,module_from_spec
spec=spec_from_file_location('fifth_step_projection',O/'procedure-sources/step5_feedback.py');projection=module_from_spec(spec);spec.loader.exec_module(projection)
protocol=read_json(O/'protocol.json');total=read_json(O/'iteration-result.json');budget=read_json(O/'native-budget.json')
assert len(total['rounds'])==2 and budget['requested']==budget['completed']<=protocol['maximum_native_evaluations']
assert file_digest(O/'runtime.json')==protocol['configuration_sha256']
assert file_digest(O/'workflow-configuration.json')==protocol['workflow_configuration_sha256']
for name,sha in protocol['sources'].items():assert file_digest(Path(name))==sha,name
seen=set(read_json(O/'historical-exclusions.json')['hashes']);rounds=[];timings=[];previous=None;source_pins={}
for round_row in total['rounds']:
    W=Path(round_row['result']['round'])
    def completed(name):
        obj=read_json(W/(name+'.json'));assert obj['state']=='completed' and digest(obj['output'])==obj['output_sha256'];return obj['output']
    parent=read_json(W/'parent.json');parent_harness=parent['harness'];dev=read_json(W/'development-cases.json')
    if previous:assert parent['revision']==previous['revision'] and verify_harness(parent_harness)==verify_harness(previous['harness'])
    assert len(dev)==5
    if round_row['index'] == 0:
        original_cases=read_json(Path(protocol['reuse_development']['directory'])/'workspace/rounds/round-000000/development-cases.json')
        assert dev == original_cases
        for case in dev:evidence.verify_case(case,W/'development-layouts')
        for route in ['pi05','pi05-sparse-memory']:
            reuse=read_json(O/'reused-development'/(route+'.json'))
            assert reuse['verified'] and reuse['episodes']==5 and reuse['new_native_episodes']==0
    else:
        for case in dev:
            assert case['layout_sha256'] not in seen;seen.add(case['layout_sha256']);evidence.verify_case(case,W/'development-layouts')
    raw_feedback=read_json(W/'development-results.json');children=completed('propose');assert len(children)<=1
    for child in children:
        assert child['components']['foundation']==parent_harness['components']['foundation']
        assert child['components']['weights']==parent_harness['components']['weights']
        for task,skill in read_json(Path(child['root'])/'skills.json').items():source_pins[str(Path(child['root'])/skill['source'])]=skill['revision']
    cohorts=None;decision=None;by_candidate={}
    if children:
        comparison=completed('freeze');cohort=completed('validation');val=read_json(W/'validation-cases.json');assert len(val)==5
        assert cohort['generated_at']>comparison['frozen_at']
        for case in val:
            assert case['layout_sha256'] not in seen;seen.add(case['layout_sha256']);evidence.verify_case(case,W/'validation-layouts')
        harnesses={parent_harness['id']:parent_harness,**{c['id']:c for c in children}}
        assert {name:verify_harness(h) for name,h in harnesses.items()}==comparison['candidates']
        results=[completed('evaluate_'+name) for name in comparison['candidates']]
        assert all(r['evaluator_revision']==read_json(W/'config.json')['protocol']['identity'] for r in results)
        decision=Selector().select(comparison,cohort,results,evidence_root=W);assert decision==completed('selection')
        previous=read_json(W/'commit.json');assert previous['previous']==parent['revision'] and previous['decision']==decision
        assert previous['harness']['id']==decision['survivor_id']
        for p,sha in previous['evidence'].items():assert file_digest(Path(p))==sha,p
        for report in results:
            values=report['episodes'];assert len(values)==5
            by_candidate[report['candidate_id']]=dict(successes=sum(r['success'] for r in values),episodes=5,
                mean_native_score=mean(r['score'] for r in values),scores=[r['score'] for r in values])
        if (W/'proposals/classify_objects/skill-proposal.json').exists():
            gate=read_json(W/'proposals/classify_objects/cpu-contract-gate/gate-result.json')
            assert gate['passed'] and len(gate['cases'])==3 and not gate['physical_qualification']
            proposal=read_json(W/'proposals/classify_objects/skill-proposal.json')
            child=children[0];src=read_json(Path(child['root'])/'skills.json')['code.classify_objects']['source']
            assert proposal['source']==(Path(child['root'])/src).read_text()
            assert proposal['memory']==read_json(Path(child['root'])/'memory_rules.json')['classify_objects']
            request=read_json(W/'proposals/classify_objects/request.json');projected=projection.project_feedback(raw_feedback)
            assert request['development_feedback']==projected
            projection_receipt=read_json(W/'proposals/classify_objects/feedback-projection.json')
            assert projection_receipt['raw_feedback_sha256']==digest(raw_feedback)
            assert proposal['development_feedback_sha256']==digest(raw_feedback)
    else:
        assert (W/'retained.json').exists();previous=parent
    dev_routes={}
    for route in sorted({row['expert'] for row in raw_feedback}):
        rows=[r for r in raw_feedback if r['expert']==route]
        dev_routes[route]=dict(episodes=len(rows),successes=sum(r['success'] for r in rows),mean_native_score=mean(r['episode_score'] for r in rows))
    for p in W.glob('*.json'):
        value=read_json(p)
        if isinstance(value,dict) and value.get('state')=='completed' and 'started_at' in value and 'finished_at' in value:
            seconds=(datetime.fromisoformat(value['finished_at'])-datetime.fromisoformat(value['started_at'])).total_seconds()
            timings.append(dict(round_index=round_row['index'],phase=p.stem,elapsed_s=seconds,receipt=str(p)))
    rounds.append(dict(index=round_row['index'],development=dev_routes,paired_validation=by_candidate,
        decision=decision,revision=previous['revision'],survivor_id=previous['harness']['id'],elapsed_s=round_row['elapsed_s']))

state=HarnessState(O/'workspace/state');current=state.resolve();assert current['revision']==previous['revision']
episodes=[];videos=[]
for batch in budget['batches']:
    assert batch['state']=='completed';leaf=Path(batch['output']);receipts=sorted((leaf/'episodes').glob('*.json'));assert len(receipts)==batch['count']
    for path in receipts:
        v=read_json(path);checked=evidence.episode_receipt(path,directory=leaf,task=v['task'],split=v['split'],layout_sha256=v['layout_sha256'],
            expert=dict(name=v['expert'],revision=v['revision']),harness_sha256=v['harness_sha256'])
        steps=v['diagnostics']['action_count'];assert 0<=steps<=1100
        mp4=sorted(leaf.rglob('*.mp4'));assert len(mp4)==3 # Predeclared batch size one.
        for p in mp4:
            frame_info=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-count_frames',
                '-show_entries','stream=nb_read_frames','-of','json',str(p)],text=True))['streams'][0]
            frames=int(frame_info['nb_read_frames']);assert frames==steps+1,(str(p),frames,steps)
            videos.append(dict(path=str(p),frames=frames,bytes=p.stat().st_size))
        episodes.append(dict(receipt=str(path),split=v['split'],expert=v['expert'],revision=v['revision'],score=v['episode_score'],success=v['success'],
            steps=steps,layout_sha256=v['layout_sha256'],native_exit_code=v['native_exit_code'],natural_terminal=v['natural_terminal']))
assert len(episodes)==budget['completed']
api=[]
for p in sorted((O/'proposal-api').glob('call-*/started.json')):
    d=p.parent;request=read_json(d/'request.json');response=read_json(d/'response.json');done=read_json(d/'completed.json');started=read_json(p)
    usage=response['usage'];assert usage==done['usage'] and usage['total_tokens']==usage['prompt_tokens']+usage['completion_tokens']
    assert done['http_attempts']==1 and not started['retry'];assert not (d/'failed.json').exists()
    generated=json.loads(response['choices'][0]['message']['content'])
    proposal=read_json(O/('workspace/rounds/round-%06d/proposals/classify_objects/skill-proposal.json'%started['round_index']))
    assert generated['source']==proposal['source'] and generated['memory']==proposal['memory']
    api.append(dict(round_index=started['round_index'],model=request['model'],http_attempts=1,input_tokens=usage['prompt_tokens'],output_tokens=usage['completion_tokens'],
        total_tokens=usage['total_tokens'],reasoning_tokens_subset_output=usage.get('completion_tokens_details',{}).get('reasoning_tokens'),
        cached_tokens_subset_input=usage.get('prompt_tokens_details',{}).get('cached_tokens'),elapsed_s=done['elapsed_s'],finish_reason=done['finish_reason']))
assert len(api)<=2
prior=Path(protocol['prior_attempt'])
prior_result=read_json(prior/'step5-stopped-results.json')
prior_calls=[]
for p in sorted((prior/'proposal-api').glob('call-*/completed.json')):
    done=read_json(p);prior_calls.append(dict(usage=done['usage'],elapsed_s=done['elapsed_s']))
for p,sha in protocol['reuse_development']['files'].items():assert file_digest(Path(p))==sha,p
reused_rows=read_json(prior/'workspace/rounds/round-000000/development-results.json')
for route in ['pi05','pi05-sparse-memory']:
    rows=[r for r in reused_rows if r['expert']==route]
    assert digest(rows)==read_json(O/'reused-development'/(route+'.json'))['original_rows_sha256']
    for i,row in enumerate(rows):
        leaf=prior/'workspace/rounds/round-000000/development'/route/('batch-%06d'%i)
        v=read_json(leaf/'episodes/0.json')
        assert evidence.episode_receipt(leaf/'episodes/0.json',directory=leaf,task=v['task'],split='development',
            layout_sha256=v['layout_sha256'],expert=dict(name=v['expert'],revision=v['revision']),harness_sha256=v['harness_sha256'])==row
freeze=read_json(R/'result/23_protocol_freeze_20261029T132917Z/source-freeze.json')
for row in freeze['deployment_files']:assert file_digest(Path(row['path']))==row['sha256'],row['path']
for name,sha in freeze['recorded_protocol_and_framework_hashes'].items():assert file_digest(Path(name))==sha,name
for name,sha in source_pins.items():assert file_digest(Path(name))==sha,name
secret=read_json(Path('/home/ecs-user/.config/physicalrsi/agent.json'))['api_key'].encode();files_checked=0
for p in O.rglob('*'):
    if p.is_file() and p.suffix in {'.json','.jsonl','.log','.py','.txt','.csv'}:
        assert secret not in p.read_bytes(),'Credential present in retained evidence';files_checked+=1
gpu=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip();assert not gpu
telemetry=list(csv.DictReader((O/'gpu-telemetry.csv').open()))
utc=datetime.now(timezone.utc).isoformat()
result=dict(complete=True,utc=utc,step=5,rounds=rounds,selected_revision=current['revision'],native_episodes=len(episodes), reused_development_episodes=10, logical_completed_evaluations=len(episodes)+10,
    video_count=len(videos),video_frames=sum(v['frames'] for v in videos),proposal_http_attempts=len(api),
    proposal_input_tokens=sum(v['input_tokens'] for v in api),proposal_output_tokens=sum(v['output_tokens'] for v in api),
    proposal_total_tokens=sum(v['total_tokens'] for v in api),proposal_http_elapsed_s=sum(v['elapsed_s'] for v in api),
    cumulative_with_prior_attempt=dict(proposal_http_attempts=len(api)+len(prior_calls),
        proposal_total_tokens=sum(v['total_tokens'] for v in api)+sum(v['usage']['total_tokens'] for v in prior_calls),
        proposal_http_elapsed_s=sum(v['elapsed_s'] for v in api)+sum(v['elapsed_s'] for v in prior_calls),
        note='Prior interrupted attempt remains separate; reused native development is counted once'),
    iteration_elapsed_s=total['elapsed_s'],raw_retention='cloud_only',original_source_pins_verified=True,
    credentials_found=0,gpu_compute_processes=0,task='classify_objects',final_test_started=False,steps6_to8_started=False,
    model_feedback_profile='Verified development metrics with full-row evidence digest; raw artifact inventory retained off-prompt',
    qualifications=['First-round completed native development evidence reused with original identities; only interface documentation/output destination changed.',
        'Two bounded selected-task iterations; small validation cohorts do not establish generalization or paper performance equivalence.',
        'Score-based selector is preregistered; an adopted survivor is not proof of statistically significant improvement.',
        'These proposal/development costs are System2 costs, not System1 online task costs or a direct cross-project Token/speed ratio.',
        'Only selected parent source/memory inherit between rounds; a rejected candidate is preserved, not silently adopted.',
        'No ungenerated independent final test has been counted as success.'])
atomic_json(Z/'native-episodes-and-videos.json',dict(episodes=episodes,videos=videos))
atomic_json(Z/'phase-timing.json',dict(phases=timings,scope='Checkpoint wall time includes stage-specific startup/reset/execution/evidence/cleanup; operator preparation excluded'))
atomic_json(Z/'model-usage.json',dict(calls=api,phase='System2 formal development/proposal',http_attempts=len(api),unknown_usage=0))
atomic_json(Z/'verification.json',dict(complete=True,utc=utc,lineage_verified=True,candidates_match_actual_model_response=True,
    original_deployment_pins=len(freeze['deployment_files']),original_framework_pins=len(freeze['recorded_protocol_and_framework_hashes']),
    native_evidence_verified=len(episodes),video_frames_verified=sum(v['frames'] for v in videos),credential_matches=0,text_files_checked=files_checked,
    gpu_compute_processes=0,gpu_samples=len(telemetry),gpu_peak_memory_MiB=max(float(r['gpu_memory_MiB']) for r in telemetry),
    gpu_peak_util_percent=max(float(r['gpu_util_percent']) for r in telemetry),audit_source_sha256=file_digest(Path(__file__))))
atomic_json(O/'step5-results.json',result)
atomic_json(O/'step5-completion.json',dict(complete=True,utc=utc,result=str(O/'step5-results.json'),result_sha256=file_digest(O/'step5-results.json'),verification=str(Z/'verification.json')))
plan=read_json(R/'result/CURRENT_REPRODUCTION_PLAN.json');plan.update(updated_utc=utc,step5_complete=True,step5_verified_utc=utc,
    current_controller_running=False,active_controller_pid=None,active_tmux_session=None,
    last_completed_directory=str(O),completion_receipt=str(O/'step5-completion.json'),next_step=6,
    next_action='Step5 complete. Next is version inheritance/restart check (step6); independent final test remains ungenerated.')
plan['steps'][4]['state']='complete; two bounded native System2 rounds, official survivor selection and lineage verified'
atomic_json(R/'result/CURRENT_REPRODUCTION_PLAN.json',plan)
atomic_json(O/'controller-status.json',dict(complete=True,stage='complete_verified',utc=utc,pid=None,rounds_finished=2,completion=str(O/'step5-completion.json')))
atomic_json(R/'result/CURRENT_STEP5.json',dict(complete=True,stage='complete_verified',directory=str(O),utc=utc,pid=None,completion=str(O/'step5-completion.json')))
print(json.dumps(dict(complete=True,rounds=rounds,native_episodes=len(episodes),tokens=result['proposal_total_tokens'],video_count=len(videos)),ensure_ascii=False))
