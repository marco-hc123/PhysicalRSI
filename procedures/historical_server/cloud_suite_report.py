"""Audit native outputs and summarize a completed preregistered cloud suite."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import statistics
import numpy as np

root = Path('/mnt/data/physical-RSI/result')
suite = Path(json.loads((root/'CURRENT_EXPERIMENT_SUITE.json').read_text())['directory'])
protocol = json.loads((suite/'protocol.json').read_text())
controller = json.loads((suite/'controller-status.json').read_text())
assert controller.get('finished') and controller.get('complete'), 'Suite is not complete'
amendment = json.loads((suite/'protocol-amendment-thinking-native.json').read_text())
extension = json.loads((suite/'extension-status.json').read_text())
continuation = json.loads((suite/'thinking-continuation-status.json').read_text())
assert continuation.get('finished'), 'Remaining thinking-mode layouts are not finished'
partial_job = dict(amendment['additional_job'], layouts=[1,2,3,4], partial_native=True)
jobs = controller['jobs'] + [partial_job] + continuation['jobs']
expected_total = amendment['total_native_episodes']
episodes, runs, videos = [], [], []
observation_count = decision_count = 0
failed_observation = suite/'new_layouts_agent_thinking/observation-004.npz'
with np.load(failed_observation, allow_pickle=False) as observation:
    failed_instruction = str(observation['instruction'])
episodes.append(dict(run='new_layouts_agent_thinking',phase='new_layouts',route='agent-thinking',
    repeat=None,layout_id=5,success=False,score=None,native_completed=False,
    status='planner_contract_failure',instruction=failed_instruction,
    error='Unknown composition operation_program; not remapped or retried',
    observation_artifact=str(failed_observation.relative_to(suite)),
    response_artifact='new_layouts_agent_thinking/api/call-005-response.json'))
for job in jobs:
    directory = suite/job['name']
    state = json.loads((directory/'status.json').read_text())
    partial = job.get('partial_native',False)
    failed_case = job.get('native_complete') is False
    if partial:
        native = json.loads((directory/'partial-native-result.json').read_text())
    elif failed_case:
        native = dict(details={},eval_time=0)
    else:
        native = json.loads((directory/'native-result.json').read_text())
        assert state['completed'] and state['client_exit_code'] == 0
    details = list(native['details'].values())
    if not failed_case:
        assert sorted(int(d['layout_id']) for d in details) == sorted(job['layouts'])
        assert native['eval_time'] == len(job['layouts'])
    observations = sorted(directory.glob('observation-*.npz'))
    assert len(observations) == len(job['layouts'])+int(partial), (directory, len(observations))
    observation_count += len(observations)
    choices = []
    for f in sorted((directory/'runtime').glob('*/episodes/*/agent-decision.json')):
        decision = json.loads(f.read_text())
        choices.append(dict(instruction=decision['instruction'], plan=decision['plan'],
                            evidence=str(f.relative_to(suite))))
    if not failed_case:
        assert len(choices) == len(job['layouts']), (directory, len(choices))
    decision_count += len(choices)
    timing_file = directory/'action-timing.jsonl'
    timings = [json.loads(line) for line in timing_file.read_text().splitlines()] if timing_file.exists() else []
    assert (timings or failed_case) and all(t['seconds'] >= 0 for t in timings)
    usage = json.loads((directory/'usage-summary.json').read_text())
    if job['route'] != 'agent':
        assert usage['api_attempts'] == 0
    api_metadata = [json.loads(p.read_text()) for p in sorted((directory/'api').glob('*-metadata.json'))]
    requests = [json.loads(p.read_text()) for p in sorted((directory/'api').glob('*-request.json'))]
    assert all(r['enable_thinking'] == bool(job.get('thinking')) for r in requests)
    reasoning_tokens = sum((m.get('usage') or {}).get('completion_tokens_details',{}).get('reasoning_tokens',0)
                           for m in api_metadata)
    run = dict(job=job, elapsed_seconds=state['elapsed_seconds'], usage=usage,
               provider_reported_reasoning_tokens=reasoning_tokens,
               decisions=choices, get_action_batch_calls=len(timings),
               get_action_batch_seconds=sum(t['seconds'] for t in timings),
               returned_actions=sum(sum(t['action_counts']) for t in timings),
               observation_evidence=[str(p.relative_to(suite)) for p in observations])
    runs.append(run)
    if failed_case:
        with np.load(observations[0],allow_pickle=False) as observation:
            instruction = str(observation['instruction'])
        episodes.append(dict(run=job['name'],phase='new_layouts',route='agent-thinking',
            repeat=None,layout_id=job['layouts'][0],success=False,score=None,native_completed=False,
            status=job['failure_kind'],instruction=instruction,error=job.get('error'),
            observation_artifact=str(observations[0].relative_to(suite))))
        continue
    native_dir = Path(continuation['original_native_path'] if partial else state['native_result_path']).parent
    for index, detail in enumerate(details):
        analysis_route = 'agent-thinking' if job.get('thinking') else job['route']
        episode = dict(run=job['name'], phase=job['phase'], route=analysis_route,
                        repeat=job.get('repeat'), native_completed=True,status='native_completed', **detail)
        with np.load(observations[index], allow_pickle=False) as observation:
            episode['instruction'] = str(observation['instruction'])
        matched = [c for c in choices if c['instruction'] == episode['instruction']]
        assert len(matched) == 1, ('Ambiguous decision-to-layout mapping', job['name'], index)
        episode['decision'] = matched[0]
        found = sorted(native_dir.glob(f'episode_{index:07d}_cam_head_*.mp4'))
        assert len(found) == 1 and found[0].stat().st_size > 0, (native_dir, index)
        episode['head_video'] = str(found[0])
        video_dir = directory/'videos'
        video_dir.mkdir(exist_ok=True)
        for source in sorted(native_dir.glob(f'episode_{index:07d}_*.mp4')):
            destination = video_dir/source.name
            if not destination.exists():
                try:
                    os.link(source, destination)
                except OSError:
                    shutil.copy2(source, destination)
            assert destination.stat().st_size == source.stat().st_size
            videos.append(str(destination.relative_to(suite)))
        episode['head_video_artifact'] = str((video_dir/found[0].name).relative_to(suite))
        episodes.append(episode)
assert len(episodes) == expected_total
episodes.sort(key=lambda e:(e['phase'],e['route'],e['layout_id'],e.get('repeat') or 0))

scores = []
for phase, routes, expected in [('control', protocol['routes'], 3),
                                ('new_layouts', protocol['new_layout_routes']+['agent-thinking'], 10)]:
    for route in routes:
        subset = [e for e in episodes if e['phase'] == phase and e['route'] == route]
        assert len(subset) == expected
        if phase == 'new_layouts':
            assert sorted(e['layout_id'] for e in subset) == protocol['new_layouts']
        else:
            assert all(e['layout_id'] == protocol['control_layout'] for e in subset)
            assert sorted(e['repeat'] for e in subset) == [1,2,3]
        successes = sum(bool(e['success']) for e in subset)
        native_count = sum(e['native_completed'] for e in subset)
        scores.append(dict(phase=phase, route=route, successes=successes,
                           episodes=len(subset), success_rate=successes/len(subset),
                           native_completed=native_count,precompletion_failures=len(subset)-native_count))

mode_state = json.loads((suite/'api-modes/status.json').read_text())
assert mode_state['done'] and mode_state['completed'] == 6
mode_summary = []
for thinking in (False, True):
    subset = [r for r in mode_state['rows'] if r['thinking'] == thinking]
    assert len(subset) == 3
    mode_summary.append(dict(thinking=thinking, calls=3, robot_executed=False,
        valid_plans=sum(bool(r.get('contract_valid')) for r in subset),
        average_seconds=statistics.mean(r['seconds'] for r in subset),
        prompt_tokens=sum(r['usage']['prompt_tokens'] for r in subset),
        completion_tokens=sum(r['usage']['completion_tokens'] for r in subset),
        total_tokens=sum(r['usage']['total_tokens'] for r in subset),
        cached_tokens=sum(r['usage'].get('prompt_tokens_details',{}).get('cached_tokens',0) for r in subset),
        selections=[r.get('plan') for r in subset]))
attempts = []
for p in suite.glob('*/status.json'):
    s = json.loads(p.read_text())
    if s.get('stage') == 'failed' and s.get('route') and p.parent.name.startswith('control_'):
        attempts.append(dict(run=p.parent.name, error=s.get('error'), counted_in_success_rate=False))

native_count = sum(e['native_completed'] for e in episodes)
assert observation_count == expected_total
report = dict(protocol=protocol, amendment=amendment, continuation=continuation,
    scope=protocol['scope'], evaluated_cases=expected_total,native_episodes=native_count,
    native_summary=scores, episodes=episodes, runs=runs, api_modes=mode_summary,
    excluded_infrastructure_attempts=attempts,
    counted_evaluation_failures=[e for e in episodes if not e['native_completed']],
    total_provider_reported_tokens=sum(r['usage']['provider_reported_usage']['total_tokens'] for r in runs)
        +sum(r['total_tokens'] for r in mode_summary),
    notes=[
        'Repeated layout0 trials use seed0 and measure repeatability, not independent scene generalization.',
        'Layouts1..10 were held out from this debugging, not certified absent from model training.',
        'Native evaluator is the success authority; API-valid planning is not manipulation success.',
        'End-to-end success rates keep planner and execution failures in the planned denominator; null score means no completed native outcome.',
        'Thinking-mode layout5 returned unknown composition operation_program. It was counted as failure without retry or automatic correction. Remaining layouts ran once in fresh processes after the abort.',
        'Matching layouts use the same seed and robot initial state, but rendered RGB is not pixel-identical. The same code program has execution variability; differences from the fixed-code baseline cannot all be attributed to model reasoning.',
        'Both VLA weights and the complete 22-operation catalogue were available for all routes.',
        'The get_action_batch timer excludes update_obs_batch and simulator time; code perception can run in update_obs_batch.',
        'Mode probes replay the same original RGB and prompt and do not execute robots; latency is affected by provider prompt caching.',
        'This is an external-provider native simulation evaluation, not System2 evolution or physical-robot qualification.'
    ])
(suite/'suite-report.json').write_text(json.dumps(report, indent=2)+'\n')
(suite/'video-manifest.json').write_text(json.dumps(videos, indent=2)+'\n')
audit = dict(evaluated_cases_verified=expected_total,native_episodes_verified=native_count,
             initial_observations_verified=observation_count,
             valid_bound_decisions_verified=decision_count,head_videos_verified=native_count,
             robot_video_files=len(videos),
             report_sha256=hashlib.sha256((suite/'suite-report.json').read_bytes()).hexdigest())
(suite/'audit.json').write_text(json.dumps(audit, indent=2)+'\n')
print(json.dumps(dict(scores=scores, api_modes=[{k:v for k,v in m.items() if k!='selections'} for m in mode_summary],
                      audit=audit, total_tokens=report['total_provider_reported_tokens']), indent=2))
