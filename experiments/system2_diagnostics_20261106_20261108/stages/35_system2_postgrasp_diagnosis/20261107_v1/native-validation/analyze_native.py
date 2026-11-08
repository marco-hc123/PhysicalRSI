"""Read completed native cohorts; never modify experiment artifacts or policy code."""
import collections
import csv
import datetime
import hashlib
import json
import math
from pathlib import Path

R = Path('/mnt/data/physical-RSI')
O = R / 'result/36_postgrasp_diagnosis_20261107'
C = O / 'native-campaign'
D = O / 'analysis'
D.mkdir(exist_ok=True)

def read(p):
    return json.loads(Path(p).read_text())

def dump(p, value):
    p = Path(p)
    tmp = p.with_suffix(p.suffix + '.tmp')
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')
    tmp.replace(p)

def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def relative(p):
    return str(Path(p).relative_to(O))

def table(name, rows):
    if not rows:
        return
    fields = list(dict.fromkeys(k for row in rows for k in row))
    p = D / name
    with p.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v for k, v in row.items()})

campaign = read(C / 'campaign.json')
cases = campaign['cases']
layouts = [read(Path(campaign['layout_root']) / case['file']) for case in cases]
summaries, episode_rows, actors, videos = [], [], [], []
layout_rows = []
for i, (case, layout) in enumerate(zip(cases, layouts)):
    layout_rows.append(dict(layout_id=i, source_layout_id=int(Path(case["file"]).parent.name), layout_sha256=case['layout_sha256'],
                            task=case['task'], research_role='reused diagnostic/development layout',
                            categories={k: len(v) for k, v in layout['Rigid'].items()},
                            objects=sum(len(v) for v in layout['Rigid'].values()),
                            source=str(Path(campaign['layout_root']) / case['file'])))

def initial_geometry_distance(objects, layout):
    expected = [(k, row['default_pos']) for k, rows in layout['Rigid'].items() for row in rows]
    distances = []
    for name, obj in objects.items():
        cat = name.rsplit('_', 1)[0]
        if cat == 'basket':
            continue
        cat = {'camera': 'action_camera'}.get(cat, cat)
        matching = [p for k, p in expected if k == cat]
        if not matching:
            distances.append(1.0)
        else:
            xy = obj['pose'][:2]
            distances.append(min(math.hypot(xy[0]-p[0], xy[1]-p[1]) for p in matching))
    return sum(distances)/len(distances) if distances else None

for entry in campaign['entries']:
    name = entry['name']
    base = C / 'runs' / name
    if not (base / 'completed.json').exists():
        continue
    completed = read(base / 'completed.json')
    run = Path(completed['output'])
    observed = read(run / 'native/run/observed.json')
    assert not observed['failures'] and len(observed['outcomes']) == len(cases)
    raw_files = list(run.rglob('_result.json'))
    assert len(raw_files) == 1
    raw = read(raw_files[0])
    assert raw['eval_time'] == len(cases)
    cohort_videos = sorted(run.rglob('*.mp4'))
    assert len(cohort_videos) == 3*len(cases)
    timing = read(base / 'timing.json')
    service_calls = collections.Counter()
    for p in (run / 'model/expert/calls').glob('*.json'):
        record = read(p)
        service_calls[record.get('method', 'unknown')] += 1
    for i, case in enumerate(cases):
        receipt = read(run / 'episodes' / (str(i) + '.json'))
        assert receipt['layout_sha256'] == case['layout_sha256']
        assert receipt['native_exit_code'] == 0 and receipt['natural_terminal']
        assert receipt['success'] == raw['details'][str(i)]['success']
        assert abs(receipt['episode_score'] - raw['details'][str(i)]['score']) < 1e-9
        episode_rows.append(dict(condition=name, layout_id=i, source_layout_id=int(Path(case["file"]).parent.name), success=receipt['success'],
                                 normalized_score=receipt['episode_score'],
                                 native_action_count=receipt['diagnostics']['action_count'],
                                 step_limit=receipt['diagnostics']['step_limit'],
                                 layout_sha256=case['layout_sha256'],
                                 receipt=relative(run / 'episodes' / (str(i) + '.json')),
                                 result_file=relative(raw_files[0]), paid_api_calls=0))
    for p in cohort_videos:
        videos.append(dict(condition=name, file=relative(p), bytes=p.stat().st_size,
                           layout_id=int(p.name.split('_')[1]),
                           camera=p.name.split('_cam_', 1)[1].rsplit('_', 1)[0],
                           sha256=sha(p)))
    local_actors = []
    for p in (run / 'model/expert').glob('*/0/policy/processes/isolated/process.json'):
        process = read(p)
        calls = sorted(process['calls'], key=lambda x: x['request']['id'])
        assert [x['request']['id'] for x in calls] == list(range(len(calls)))
        assert all(x['request']['id'] == x['response']['id'] for x in calls if 'response' in x)
        actor_root = p.parents[3]
        episode_id = actor_root.parent.name
        first_scene = next((x['response']['value'] for x in calls if x['request']['method'] in ['scene', 'reobserve'] and 'response' in x), {})
        geometry = [initial_geometry_distance(first_scene.get('objects', {}), layout) for layout in layouts]
        available = [(distance, i) for i, distance in enumerate(geometry) if distance is not None]
        available.sort()
        mapped_layout = available[0][1] if available else None
        mapping_margin = available[1][0] - available[0][0] if len(available) > 1 else None
        mapping_qualified = bool(available and available[0][0] < 0.08 and mapping_margin > 0.03)
        approaches = [x for x in calls if x['request']['method'] == 'approach']
        errors = [x for x in approaches if x.get('response',{}).get('value',{}).get('primitive_error')]
        accepted = [x for x in approaches if x['state']=='completed' and 'response' in x and not x['response']['value'].get('primitive_error')]
        incomplete = [x for x in approaches if x not in errors and x not in accepted]
        grippers = [x for x in calls if x['request']['method'] == 'gripper']
        rpc_records = [read(q) for q in (actor_root / 'execution/rpc').glob('*.json')]
        trusted = [read(actor_root / 'primitive-service/requests' / (x['request_id']+'.json')) for x in rpc_records]
        trusted_steps = sum(x.get('result', {}).get('action_steps', 0) for x in trusted)
        per_operation = collections.Counter()
        for rpc, req in zip(rpc_records, trusted):
            per_operation[rpc['method']] += req.get('result', {}).get('action_steps', 0)
        first_error_id = errors[0]['request']['id'] if errors else None
        method_sequence = [x['request']['method'] for x in calls]
        actor_final = read(actor_root/'actor.json')
        native_limit_cancel = bool(actor_final.get('state')=='cancelled' and 'Actor channel closed: actor stopping' in actor_final.get('error','') and mapping_qualified and observed['outcomes'][mapped_layout]['natural_terminal'] and observed['outcomes'][mapped_layout]['action_count']==observed['outcomes'][mapped_layout]['step_limit'])
        row = dict(condition=name, actor_episode_id=episode_id, actor_index=0,
                   mapped_layout_id=mapped_layout if mapping_qualified else None,
                   mapping_method='unique nearest initial RGB scene to recorded layout categories/XY, camera alias to action_camera; offline diagnostic only',
                   mapping_qualified=mapping_qualified, geometry_distance_by_layout=geometry,
                   geometry_mapping_margin_m=mapping_margin, isolated_pid=process['pid'],
                   process_record_mtime_utc=datetime.datetime.fromtimestamp(p.stat().st_mtime, datetime.timezone.utc).isoformat(),
                   call_ids=[x['request']['id'] for x in calls], method_sequence=method_sequence,
                   rpc_calls=len(calls), scene_calls=method_sequence.count('scene'),
                   reobserve_calls=method_sequence.count('reobserve'),
                   approach_calls=len(approaches), accepted_approach_calls=len(accepted),
                   incomplete_approach_calls=len(incomplete),
                   rejected_approach_calls=len(errors), first_error_call_id=first_error_id,
                   first_error=errors[0]['response']['value']['primitive_error'] if errors else None,
                   first_approach_rejected=bool(approaches and approaches[0].get('response',{}).get('value',{}).get('primitive_error')),
                   calls_after_first_error=sum(x['request']['id'] > first_error_id for x in calls) if errors else None,
                   approach_targets=[x['request']['kwargs'] for x in approaches],
                   gripper_commands=[x['request']['kwargs'] for x in grippers],
                   trusted_primitive_action_steps=trusted_steps,
                   primitive_step_scope='Completed trusted RPCs only; unfinished call may have executed additional steps',
                   partial_action_steps_unknown=bool(incomplete),
                   trusted_steps_by_operation=dict(per_operation),
                   returned_value=read(actor_root/'policy/result.json') if (actor_root/'policy/result.json').exists() else None,
                   return_record_exists=(actor_root/'policy/result.json').exists(),
                   isolated_returncode=process.get('returncode'), isolated_state=process['state'],
                   actor_final_state=actor_final.get('state'), actor_error=actor_final.get('error'),
                   native_step_limit_cancelled=native_limit_cancel,
                   first_scene_categories=dict(collections.Counter(k.rsplit('_',1)[0] for k in first_scene.get('objects',{}))),
                   scene_sequences=[x['response']['value'].get('observation',{}).get('sequence') for x in calls if x['request']['method'] in ['scene','reobserve'] and 'response' in x],
                   process_record=relative(p), binding_record=relative(actor_root/'binding.json'))
        local_actors.append(row)
    if name != 'pi05':
        assert len(local_actors) == len(cases)
        mapped=[x['mapped_layout_id'] for x in local_actors if x['mapping_qualified']]
        assert len(mapped)==len(set(mapped)), 'Ambiguous actor-layout mapping'
    actors.extend(local_actors)
    q=[x for x in episode_rows if x['condition']==name]
    summaries.append(dict(condition=name, cases=len(q), successes=sum(x['success'] for x in q),
                          mean_normalized_score=sum(x['normalized_score'] for x in q)/len(q),
                          cohort_wall_seconds=timing['start_to_valid_receipts_s'],
                          videos=len(cohort_videos), api_calls=0, paid_cost_usd=0,
                          internal_service_calls_by_method=dict(service_calls),
                          candidate_actors=len(local_actors),
                          first_approach_rejections=sum(x['first_approach_rejected'] for x in local_actors) if local_actors else None,
                          total_approach_calls=sum(x['approach_calls'] for x in local_actors) if local_actors else None,
                          accepted_approach_calls=sum(x['accepted_approach_calls'] for x in local_actors) if local_actors else None,
                          incomplete_approach_calls=sum(x['incomplete_approach_calls'] for x in local_actors) if local_actors else None,
                          native_step_limit_cancellations=sum(x['native_step_limit_cancelled'] for x in local_actors) if local_actors else None,
                          actors_with_post_error_calls=sum(bool(x['calls_after_first_error']) for x in local_actors) if local_actors else None,
                          total_trusted_primitive_action_steps=sum(x['trusted_primitive_action_steps'] for x in local_actors) if local_actors else None,
                          scope='Reused diagnostic layouts; no policy promotion',
                          completed_record=relative(base/'completed.json')))

result=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            qualified_cases=len(episode_rows), planned_cases=campaign['planned_cases'], complete=len(episode_rows)==campaign['planned_cases'],
            cohorts=summaries, episodes=episode_rows, actors=actors, layouts=layout_rows, videos=videos,
            limitations=[
                'Three previously exposed layouts; descriptive diagnostics, not independent generalization.',
                'One fixed saved candidate and exact proposed memory; logging-only post-grasp diagnosis. No fresh generation.',
                'Completed RPC and gripper closure do not establish lift or task success.',
                'Native action_count includes hold steps after candidate return; trusted primitive action_steps are reported separately.',
                'Completed primitive step totals omit any partially executed call cancelled when the native step limit is reached.',
                'Actor-layout joins are separately qualified from original evidence; uncertain matches remain null.',
                'All candidates use the same execution host; fixed balanced cohort order and caches limit timing attribution.',
                'Candidate generation is historical stage33 evidence, not repeated here. Native execution has no API calls or automatic selection; pi05 remains retained.',
            ])
dump(D/'matrix-analysis.json',result)
table('cohort-summary.csv',summaries)
table('episode-results.csv',episode_rows)
table('actor-diagnostics.csv',actors)
table('layout-inventory.csv',layout_rows)
table('video-index.csv',videos)
print(json.dumps(dict(qualified_cases=len(episode_rows),cohorts=summaries),ensure_ascii=False))
