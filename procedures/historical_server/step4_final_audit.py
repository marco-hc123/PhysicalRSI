"""Cloud-only post-run audit. Never invokes a model or simulator."""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import json, os, subprocess, sys

R=Path('/mnt/data/physical-RSI');O=R/'result/25_system2_integration_20261030T050100Z'
A=O/'attempt-05-planning-contract';P=O/'attempt-03/workspace/rounds/round-000000'
W=A/'workspace/rounds/round-000000';Z=O/'final-audit';Z.mkdir(exist_ok=True)
cfg=json.loads((A/'runtime.json').read_text());os.environ.update(cfg['policy_environment']);sys.path[:0]=cfg['policy_environment']['PYTHONPATH'].split(':')
from PhysicalRSI_core.infra.storage import atomic_json, read_json, file_digest, digest
from PhysicalRSI_core.self_harness.artifacts import verify_harness
from PhysicalRSI_core.lineage import HarnessState
from PhysicalRSI_baselines.robodojo import evidence
from PhysicalRSI_baselines.robodojo.workflow import Selector

assert (A/'iteration-result.json').exists(), 'Wait for native integration, do not repeat episodes'
assert read_json(O/'isolation-boundary-verification.json')['passed'] is True
assert read_json(A/'no-path-contract-verification.json')['passed'] is True
def completed(name):
    v=read_json(W/(name+'.json'));assert v['state']=='completed' and digest(v['output'])==v['output_sha256'];return v['output']

comparison=completed('freeze');cohort=completed('validation');results=[completed('evaluate_'+name) for name in comparison['candidates']]
parent=read_json(W/'parent.json');child,=completed('propose');harnesses={parent['harness']['id']:parent['harness'],child['id']:child}
assert {name:verify_harness(h) for name,h in harnesses.items()}==comparison['candidates']
decision=Selector().select(comparison,cohort,results,evidence_root=W);assert decision==completed('selection')
state=HarnessState(A/'workspace/state');current=state.resolve();assert current==read_json(W/'commit.json')
assert current['decision']==decision and current['previous']==parent['revision']
for path,sha in current['evidence'].items():assert file_digest(Path(path))==sha,path
assert current['harness']['id']==decision['survivor_id']
cfg_round=read_json(W/'config.json')
assert all(v['evaluator_revision']==cfg_round['protocol']['identity'] for v in results)
for component in ['foundation','weights']:
    assert child['components'][component]==parent['harness']['components'][component]

api_starts=sorted(O.glob('**/proposal-api/call-*/started.json'));assert len(api_starts)==1
api=api_starts[0].parent;answer=read_json(api/'response.json');body=json.loads(answer['choices'][0]['message']['content'])
original_child=read_json(P/'propose.json')['output'][0]
original_root=Path(original_child['root']);candidate_root=Path(child['root'])
assert body['source']==(original_root/'code/classify_objects.py').read_text()
assert (original_root/'code/classify_objects.py').read_bytes()==(candidate_root/'code/classify_objects.py').read_bytes()
assert (original_root/'memory_rules.json').read_bytes()==(candidate_root/'memory_rules.json').read_bytes()
assert read_json(candidate_root/'memory_rules.json')['classify_objects']==body['memory']
usage=answer['usage'];assert usage['total_tokens']==usage['prompt_tokens']+usage['completion_tokens']
api_done=read_json(api/'completed.json');assert api_done['http_attempts']==1 and api_done['usage']==usage
timings=[]
for directory,name,phase in [(P,'develop','actual_two_VLA_development_episodes'),
    (P,'propose','actual_model_proposal'),(W,'validation','final_fresh_validation_initialization'),
    (W,'evaluate_initial','final_parent_validation'),(W,'evaluate_candidate_recovered','final_candidate_validation')]:
    receipt=read_json(directory/(name+'.json'));assert receipt['state']=='completed'
    elapsed=(datetime.fromisoformat(receipt['finished_at'])-datetime.fromisoformat(receipt['started_at'])).total_seconds()
    assert elapsed>=0
    timings.append(dict(phase=phase,elapsed_s=elapsed,receipt=str(directory/(name+'.json'))))
atomic_json(Z/'phase-timing.json',dict(phases=timings,actual_http_elapsed_s=api_done['elapsed_s'],
    scope='Checkpoint wall time includes native startup, reset, execution, evidence publication and cleanup as applicable.',
    qualifications=['Compatibility setup, failed attempts and operator gaps are separate, not included in these phase totals.',
        'This integration is not a cold-versus-warm speed comparison or a cross-project speed ratio.']))
atomic_json(Z/'model-usage-and-candidate-preservation.json',dict(http_attempts=1,logical_proposals=1,
    model=read_json(api/'request.json')['model'],input_tokens=usage['prompt_tokens'],output_tokens=usage['completion_tokens'],
    total_tokens=usage['total_tokens'],reasoning_tokens_subset_of_output=usage.get('completion_tokens_details',{}).get('reasoning_tokens'),
    cached_tokens_subset_of_input=usage.get('prompt_tokens_details',{}).get('cached_tokens'),elapsed_s=api_done['elapsed_s'],
    exact_actual_response_source_preserved=True,exact_actual_response_memory_preserved=True,
    source_sha256=file_digest(candidate_root/'code/classify_objects.py'),
    phase='System2 development/proposal; keep separate from System1 online inference',new_http_in_recoveries=0))

dev=read_json(P/'development-cases.json');val=read_json(W/'validation-cases.json')
assert len(dev)==len(val)==1 and dev[0]['layout_sha256']!=val[0]['layout_sha256']
oldval=read_json(O/'attempt-04-validation-recovery/workspace/rounds/round-000000/validation-cases.json')
assert val[0]['layout_sha256']!=oldval[0]['layout_sha256']
assert cohort['generated_at']>comparison['frozen_at']
episodes=[];videos=[]
paths=[('development',P/'development'/expert/'batch-000000',None) for expert in ['pi05','pi05-sparse-memory']]
paths += [('validation',W/'evaluation'/name/'batch-000000',comparison['candidates'][name]) for name in comparison['candidates']]
for split,leaf,frozen in paths:
    receipt=leaf/'episodes/0.json';v=read_json(receipt)
    outcome=evidence.episode_receipt(receipt,directory=leaf,task=v['task'],split=split,
        layout_sha256=v['layout_sha256'],expert=dict(name=v['expert'],revision=v['revision']),
        harness_sha256=frozen or v['harness_sha256'])
    expected=(dev if split=='development' else val)[0]['layout_sha256'];assert v['layout_sha256']==expected
    steps=v['diagnostics']['action_count'];mp4=sorted(leaf.rglob('*.mp4'));assert len(mp4)==3
    for p in mp4:
        stream=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-count_frames',
            '-show_entries','stream=nb_read_frames','-of','json',str(p)],text=True))['streams'][0]
        frames=int(stream['nb_read_frames']);assert frames==steps+1,(str(p),frames,steps)
        videos.append(dict(path=str(p),frames=frames,bytes=p.stat().st_size))
    episodes.append(dict(split=split,expert=v['expert'],revision=v['revision'],score=v['episode_score'],
        success=v['success'],action_count=steps,layout_sha256=v['layout_sha256'],receipt=str(receipt),
        native_exit_code=v['native_exit_code'],natural_terminal=v['natural_terminal'],artifacts=len(outcome['evidence'])))
atomic_json(Z/'native-episodes-and-videos.json',dict(complete=True,episodes=episodes,videos=videos,
    native_episode_count=4,video_count=len(videos),total_frames=sum(v['frames'] for v in videos),
    excluded_auxiliary_evidence=['A4 completed parent remains valid but separate from final F3 paired comparison.',
        'A4 candidate interrupted at planner rejection; not a completed native failure or a zero score.',
        'Initialization and boundary probes have no task episodes.']))

leaf=W/'evaluation/candidate_recovered/batch-000000'
actor=next(leaf.glob('model/expert/*/0'))
calls=[read_json(p) for p in (actor/'execution/rpc').glob('*.json')]
counts=Counter((v['method'],v['state']) for v in calls)
rejected=[v for v in calls if v.get('output',{}).get('primitive_error')=='no_collision_free_path']
cleanup=read_json(actor/'cleanup.json');assert cleanup['state']=='stopped'
isolation=read_json(actor/'policy/processes/isolated/process.json')
atomic_json(Z/'candidate-native-primitive-execution.json',dict(
    rpc_counts=[dict(method=m,state=s,count=n) for (m,s),n in sorted(counts.items())],
    completed_no_path_rejections=len(rejected),actor_status=read_json(actor/'actor.json'),cleanup=cleanup,
    isolation_process_state=isolation['state'],isolated_calls=len(isolation['calls']),
    qualification='Real RGB perception and collision-checked robot/table CuRobo calls. No full dynamic-object collision model or physical robot qualification.'))

f=read_json(R/'result/23_protocol_freeze_20261029T132917Z/source-freeze.json')
for row in f['deployment_files']:assert file_digest(Path(row['path']))==row['sha256'],row['path']
for path,sha in f['recorded_protocol_and_framework_hashes'].items():assert file_digest(Path(path))==sha,path
atomic_json(Z/'original-source-verification.json',dict(passed=True,deployment_files=len(f['deployment_files']),
    framework_dependencies=len(f['recorded_protocol_and_framework_hashes']),original_files_changed=0))
secret=read_json(Path('/home/ecs-user/.config/physicalrsi/agent.json'))['api_key'].encode()
checked=0
for p in O.rglob('*'):
    if p.is_file() and p.suffix in {'.json','.jsonl','.log','.py','.txt','.csv'}:
        assert secret not in p.read_bytes(),'Credential found in '+str(p)
        checked+=1
gpu=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip()
assert not gpu,'Owned native processes require reconciliation before completion'
utc=datetime.now(timezone.utc).isoformat()
summary=dict(complete=True,utc=utc,step=4,scope='One-candidate native System2 integration with recorded compatibility recoveries',
    development=episodes[:2],paired_validation=episodes[2:],decision=decision,committed_revision=current['revision'],
    source_and_memory_from_actual_model_response=True,proposal_tokens=usage['total_tokens'],proposal_http_attempts=1,
    native_pipeline_complete=True,formal_step5_started=False,improvement_established=False,
    unknown_or_interrupted_evaluations_scored_zero=False,credential_matches=0,text_files_checked=checked,
    gpu_compute_processes=0,raw_retention='cloud_only',raw_artifacts_downloaded_to_local=False,
    limitations=['One development scene and one fresh paired validation scene cannot establish improvement or generalization.',
        'Previous interrupted candidate and compatibility repair overhead are kept separately.',
        'The large proposal includes verbose evidence inventories; this is not the authors reported online cost.',
        'No numerical projectA/projectB speed or Token ratio without matching official measurement scope.'])
atomic_json(O/'step4-results.json',summary)
atomic_json(Z/'verification.json',dict(complete=True,utc=utc,native_episodes=4,video_count=len(videos),
    candidate_preserved=True,lineage_verified=True,source_pins_match=True,credential_matches=0,gpu_compute_processes=0,
    audit_script=str(Path(__file__)),audit_script_sha256=file_digest(Path(__file__))))
print(json.dumps(dict(complete=True,utc=utc,development=[(v['expert'],v['score'],v['success']) for v in episodes[:2]],
    validation=[(v['expert'],v['score'],v['success']) for v in episodes[2:]],decision=decision,
    proposal_tokens=usage['total_tokens'],video_count=len(videos),frames=sum(v['frames'] for v in videos)),ensure_ascii=False))
