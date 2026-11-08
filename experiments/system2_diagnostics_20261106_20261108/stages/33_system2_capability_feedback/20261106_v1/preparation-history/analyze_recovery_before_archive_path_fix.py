"""Describe actual error branches after verified native archive; no policy changes."""
import collections
import csv
import hashlib
import json
from pathlib import Path

L = Path('/mnt/data/joey_tr/physical-RSI/result/33_system2_capability_feedback/20261106_v1')
N = L / 'native-validation'
O = L / 'execution-analysis'


def read(path):
    return json.loads(path.read_text())


def write(name, value):
    (O / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def table(name, rows):
    if not rows:
        return
    with (O / name).open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v
                             for k, v in row.items()})


def value(call):
    return call.get('response', {}).get('value', {})


def completed(call):
    return call['state'] == 'completed' and 'response' in call and not value(call).get('primitive_error')


assert read(N / 'migration/ARCHIVE_VERIFIED.json')['state'] == 'verified'
d = read(N / 'analysis/matrix-analysis.json')
assert d['complete'] and d['qualified_cases'] == 30
assert not O.exists(), 'Do not overwrite completed analysis'
O.mkdir()
events, sequences, per_actor = [], [], []
for actor in sorted(d['actors'], key=lambda x: (x['condition'], x['mapped_layout_id'])):
    assert actor['mapping_qualified']
    process_path = N / actor['process_record']
    process = read(process_path)
    calls = sorted(process['calls'], key=lambda x: x['request']['id'])
    root = process_path.parents[3]
    rpc = [read(p) for p in (root / 'execution/rpc').glob('*.json')]
    candidate = actor['condition']
    group = candidate.rsplit('_', 1)[0]
    ever_closed = False
    last_command = None
    actor_events = []
    for i, call in enumerate(calls):
        request = call['request']
        method = request['method']
        kwargs = request['kwargs']
        command_context = ('before_first_completed_close_command' if not ever_closed else
                           'after_close_before_open_command' if last_command == 0 else
                           'after_open_following_close_command')
        error = value(call).get('primitive_error')
        matches = [r for r in rpc if r['method'] == method and r.get('input') == kwargs
                   and r.get('output') == value(call)] if 'response' in call else []
        trusted = [read(root / 'primitive-service/requests' / (r['request_id'] + '.json'))
                   for r in matches]
        steps = [r.get('result', {}).get('action_steps') for r in trusted]
        row = dict(candidate=candidate, arm=group, layout=actor['mapped_layout_id'],
                   call_id=request['id'], method=method, kwargs=kwargs,
                   isolated_call_state=call['state'], completed_without_primitive_error=completed(call),
                   primitive_error=error, command_context_before_call=command_context,
                   exact_trusted_rpc_match_count=len(matches),
                   matched_completed_action_steps=steps,
                   process_record=actor['process_record'])
        sequences.append(row)
        if method == 'approach' and error:
            later = calls[i + 1:]
            next_approach = next((c for c in later if c['request']['method'] == 'approach'), None)
            next_kwargs = next_approach['request']['kwargs'] if next_approach else None
            e = dict(candidate=candidate, arm=group, layout=actor['mapped_layout_id'],
                     call_id=request['id'], error=error, command_context=command_context,
                     failed_target=kwargs, exact_trusted_rpc_match_count=len(matches),
                     matched_completed_action_steps=steps,
                     zero_execution_supported_by_all_exact_matches=bool(steps) and all(s == 0 for s in steps),
                     calls_after_error=len(later),
                     next_approach_id=next_approach['request']['id'] if next_approach else None,
                     next_approach_target=next_kwargs,
                     next_approach_changes_arm=bool(next_kwargs and next_kwargs['arm'] != kwargs['arm']),
                     next_approach_completed=completed(next_approach) if next_approach else None,
                     next_approach_error=value(next_approach).get('primitive_error') if next_approach else None,
                     next_approach_state=next_approach['state'] if next_approach else None,
                     process_record=actor['process_record'])
            events.append(e)
            actor_events.append(e)
        if method == 'gripper' and completed(call):
            last_command = kwargs['command']
            ever_closed = ever_closed or last_command == 0
    per_actor.append(dict(candidate=candidate, arm=group, layout=actor['mapped_layout_id'],
                          error_events=len(actor_events),
                          errors_before_first_close=sum(e['command_context'] == 'before_first_completed_close_command' for e in actor_events),
                          errors_after_close_before_open=sum(e['command_context'] == 'after_close_before_open_command' for e in actor_events),
                          errors_after_open_following_close=sum(e['command_context'] == 'after_open_following_close_command' for e in actor_events),
                          errors_followed_by_approach=sum(e['next_approach_id'] is not None for e in actor_events),
                          alternate_arm_followups=sum(e['next_approach_changes_arm'] for e in actor_events),
                          completed_next_approaches=sum(e['next_approach_completed'] is True for e in actor_events),
                          native_step_limit_cancelled=actor['native_step_limit_cancelled']))
groups = []
for group in ['legacy_feedback', 'capability_feedback']:
    es = [e for e in events if e['arm'] == group]
    ars = [a for a in per_actor if a['arm'] == group]
    groups.append(dict(arm=group, native_cases=len(ars), error_events=len(es),
                       cases_with_error=sum(a['error_events'] > 0 for a in ars),
                       command_contexts=dict(collections.Counter(e['command_context'] for e in es)),
                       errors_followed_by_approach=sum(e['next_approach_id'] is not None for e in es),
                       alternate_arm_followups=sum(e['next_approach_changes_arm'] for e in es),
                       completed_next_approaches=sum(e['next_approach_completed'] is True for e in es),
                       native_step_limit_cancellations=sum(a['native_step_limit_cancelled'] for a in ars)))
summary = dict(state='completed', groups=groups, actor_count=len(per_actor),
               limitations=[
                   'Command context is an observed gripper-command sequence, not ground-truth contact, grasp or release.',
                   'A completed approach response is not proof of object transport or task success.',
                   'Multiple exact RPC matches are reported explicitly; no unverified chronological pairing is invented.',
                   'Incomplete calls can have executed partial actions; no action-step zero is inferred from a missing response.',
                   'No-path followup counts are descriptive; candidates differ in other generated code choices.',
               ])
write('summary.json', summary)
write('error-events.json', events)
write('command-sequences.json', sequences)
write('actor-summary.json', per_actor)
table('error-events.csv', events)
table('command-sequences.csv', sequences)
table('actor-summary.csv', per_actor)
write('provenance.json', dict(script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                             analysis_sha256=hashlib.sha256((N / 'analysis/matrix-analysis.json').read_bytes()).hexdigest(),
                             native_cases=30, policies_modified=False))
print(json.dumps(summary, ensure_ascii=False))
