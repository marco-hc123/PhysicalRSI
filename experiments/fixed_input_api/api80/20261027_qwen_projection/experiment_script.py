"""Bounded paired API experiment on synthetic observations, not robot rollouts."""
from __future__ import annotations

import argparse
import base64
from collections import Counter, defaultdict
from contextlib import nullcontext
from copy import deepcopy
import csv
from datetime import datetime, timezone
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path
import random
import re
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.request
from unittest.mock import patch

ROOT = Path('/mnt/data/joey_tr/physical-RSI')
REPO = ROOT / 'repos/PhysicalRSI'
COMMIT = '90b322a3a362aad14125f36d8ed080ca31daaea6'
MAX_ATTEMPTS = 80
RESERVE_RMB = 1.0
RUN_BUDGET_RMB = 90.0
PRIOR_SMOKE_ESTIMATE_RMB = 0.00055
MODEL = 'qwen3-vl-plus'
ENDPOINT = 'https://ws-lckd7q7bpskdc5qj.cn-beijing.maas.aliyuncs.com/compatible-mode/v1/chat/completions'
TASKS = [
    ('align', 'Use the visible straightedge to align the scattered blocks along one common edge.', 'align-blocks'),
    ('cover', 'Place each colored block over the matching outlined footprint on the tabletop.', 'cover-blocks'),
    ('coin', 'Pick up the thin coin and insert it into the narrow receiving slot.', 'deposit-coin'),
    ('classify', 'Group the visible objects by category into separate baskets. You may choose which basket holds each category.', 'classify-objects'),
    ('pickup', 'Pick up the red block and lift it above the tabletop.', 'general-pickup'),
]


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(value):
    data = value if isinstance(value, bytes) else json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    path = Path(path)
    text = json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    key = os.environ.get('PHYSICALRSI_AGENT_API_KEY')
    if key and key in text:
        raise RuntimeError('Refusing to persist a credential')
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(text, encoding='utf-8')
    tmp.replace(path)


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def append(path, value):
    with Path(path).open('a', encoding='utf-8') as f:
        f.write(json.dumps(value, ensure_ascii=False) + '\n')
        f.flush()
        os.fsync(f.fileno())


def source_modules():
    sys.path.insert(0, str(REPO))
    from PhysicalRSI_baselines.robodojo import agent_planner as planner
    from PhysicalRSI_baselines.robodojo.capability_memory import attach_capability_memory
    return planner, attach_capability_memory


def image_for(task):
    from PIL import Image, ImageDraw
    im = Image.new('RGB', (640, 480), '#ddd4bc')
    d = ImageDraw.Draw(im)
    d.rectangle((12, 12, 628, 468), outline='#746a56', width=5)
    if task == 'align':
        d.rectangle((70, 340, 565, 365), fill='#777777', outline='black', width=2)
        for x, y, color in [(120, 160, '#dc3030'), (280, 240, '#2077cc'), (440, 180, '#20aa55')]:
            d.rectangle((x, y, x + 55, y + 55), fill=color, outline='black', width=2)
    elif task == 'cover':
        for x, color in [(130, '#dc3030'), (400, '#2077cc')]:
            d.rectangle((x, 100, x + 70, 170), fill=color, outline='black', width=2)
            d.rectangle((x, 290, x + 70, 360), outline=color, width=5)
    elif task == 'coin':
        d.ellipse((110, 190, 190, 235), fill='#e6b338', outline='#795719', width=3)
        d.rectangle((370, 150, 540, 300), fill='#9ba4b3', outline='black', width=3)
        d.rectangle((410, 210, 500, 220), fill='black')
    elif task == 'classify':
        d.rectangle((60, 60, 245, 180), fill='#eee7dd', outline='#777777', width=8)
        d.rectangle((365, 60, 550, 180), fill='#eee7dd', outline='#777777', width=8)
        for x, y in [(110, 270), (380, 330)]:
            d.rectangle((x, y, x + 45, y + 45), fill='#dc3030', outline='black', width=2)
        for x, y in [(260, 290), (510, 260)]:
            d.ellipse((x, y, x + 45, y + 45), fill='#2077cc', outline='black', width=2)
    else:
        d.rectangle((175, 190, 255, 270), fill='#dc3030', outline='black', width=3)
        d.ellipse((405, 205, 465, 265), fill='#2077cc', outline='black', width=2)
    return im


def capture(planner, catalogue, memory, observation, program, projected):
    recorded = []
    reply = {'composition': next(iter(catalogue)), 'rationale': 'Offline capture only.'}
    if program is not None:
        reply['operations'] = [next(iter(program['operations']))]
    def transport(request, **kwargs):
        recorded.append(json.loads(request.data))
        return io.BytesIO(json.dumps({'choices': [{'message': {'content': json.dumps(reply)}}]}).encode())
    agent = planner.AgentPlanner.__new__(planner.AgentPlanner)
    agent.api_key, agent.endpoint, agent.model = 'offline-no-secret', 'https://invalid.example', MODEL
    projection = nullcontext() if projected else patch.object(planner, '_planner_catalogue', lambda x: x)
    with projection, patch('urllib.request.urlopen', transport):
        agent.plan(instruction=observation['instruction'], observation=observation,
                   memory=memory, previous_plan=None, compositions=catalogue, operation_program=program)
    assert len(recorded) == 1
    body = recorded[0]
    body.update(model=MODEL, stream=False, enable_thinking=False, max_tokens=512)
    return body


def pair_diff(a, b, suite):
    aa, bb = deepcopy(a), deepcopy(b)
    ca = json.loads(aa['messages'][1]['content'][0]['text'])
    cb = json.loads(bb['messages'][1]['content'][0]['text'])
    changed = [k for k in ca if ca[k] != cb[k]]
    expected = ['available_compositions'] if suite == 'example_2_compositions' else ['operation_program']
    assert changed == expected, (changed, expected)
    for key in changed:
        ca.pop(key); cb.pop(key)
    assert ca == cb
    aa['messages'][1]['content'][0]['text'] = ''
    bb['messages'][1]['content'][0]['text'] = ''
    assert aa == bb, 'Non-catalogue request difference'
    return changed


def prepare(out):
    import numpy as np
    assert subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], text=True).strip() == COMMIT
    if (out / 'manifest.json').exists():
        raise RuntimeError('Refusing to overwrite a prepared experiment')
    planner, attach = source_modules()
    cfg = REPO / 'PhysicalRSI_baselines/robodojo/configs'
    example = load(cfg / 'skill_library.example.json')
    definitions = load(cfg / 'skill_compositions.json')['compositions']
    cat = {name: attach(definitions[name], definitions[name]['steps'][-1]) for name in example['compositions']}
    memory = {'task_specific_policy_memory': {'library': load(cfg / 'policy_memory.json'), 'run_context': example.get('memory', {})}}
    operations = {}
    for cap in load(cfg / 'skill_capabilities.json')['entries']:
        if cap['implementation']['kind'] == 'code-policy':
            entry = {'input': 'robodojo.observation-batch/v1', 'output': 'robodojo.action-chunks/v1',
                     'description': 'Request-only capability fixture', 'memory_primitives': []}
            operations[cap['skill_name']] = attach(entry, cap['skill_name'])
    program = {'input': 'robodojo.observation-batch/v1', 'output': 'robodojo.action-chunks/v1', 'operations': operations}
    program_cat = {'memory-guided-program-library': {'description': 'Request-only registered operation fixture', 'steps': ['memory.snapshot', 'memory-program-library']}}
    out.mkdir(parents=True, exist_ok=True)
    (out / 'images').mkdir()
    tasks, payloads, validations = [], {}, {}
    for task, instruction, label in TASKS:
        im = image_for(task)
        im.save(out / 'images' / (task + '.png'))
        obs = {'instruction': instruction, 'env_idx': 0, 'task_name': 'hidden_label_never_transmitted',
               'state': {'left_arm_joint_state': [0.0] * 6, 'right_arm_joint_state': [0.0] * 6},
               'vision': {'cam_head': {'color': np.asarray(im), 'shape': [480, 640, 3]}}}
        tasks.append({'id': task, 'instruction': instruction, 'image_sha256': digest((out / 'images' / (task + '.png')).read_bytes()),
                      'expected_operation': label, 'label_scope': 'Predeclared text/capability matching on synthetic illustration; not geometric feasibility or robot success.'})
        for suite, catalogue, prog in [('example_2_compositions', cat, None), ('registry_22_operations', program_cat, program)]:
            pair = {}
            for cond in ('projected', 'unprojected'):
                body = capture(planner, catalogue, memory, obs, prog, cond == 'projected')
                request_id = suite + '__' + task + '__' + cond
                save(out / 'requests' / (request_id + '.json'), body)
                payloads[request_id] = digest(body)
                pair[cond] = body
            validations[suite + '__' + task] = pair_diff(pair['projected'], pair['unprojected'], suite)
    schedule = []
    for repeat in range(4):
        groups = [(suite, task) for suite in ('example_2_compositions', 'registry_22_operations') for task, _, _ in TASKS]
        random.Random(20261027 + repeat).shuffle(groups)
        for suite, task in groups:
            task_index = [x[0] for x in TASKS].index(task)
            conditions = ['projected', 'unprojected'] if (task_index + repeat) % 2 == 0 else ['unprojected', 'projected']
            for cond in conditions:
                req_id = suite + '__' + task + '__' + cond
                schedule.append({'sequence': len(schedule) + 1, 'suite': suite, 'task': task, 'repeat': repeat,
                                 'condition': cond, 'pair_order': '/'.join(conditions), 'request_id': req_id,
                                 'id': req_id + '__r' + str(repeat)})
    source_files = [REPO / 'PhysicalRSI_baselines/robodojo/agent_planner.py', REPO / 'PhysicalRSI_baselines/robodojo/capability_memory.py'] + [cfg / x for x in ('skill_library.example.json', 'skill_compositions.json', 'skill_capabilities.json', 'policy_memory.json')]
    sources = {}
    for src in source_files:
        relative = src.relative_to(REPO)
        dest = out / 'source_evidence' / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(src.read_bytes())
        sources[str(relative)] = digest(src.read_bytes())
    save(out / 'validation_registry.json', {'composition_catalogue': cat, 'operation_catalogue': program_cat, 'program': program})
    save(out / 'manifest.json', {
        'created_at_utc': now(), 'source_commit': COMMIT, 'source_hashes': sources, 'request_hashes': payloads,
        'tasks': tasks, 'pair_invariants': validations, 'schedule': schedule, 'model': MODEL,
        'model_version_limit': 'Alias requested; provider-reported model logged. No immutable snapshot version asserted.',
        'sampling': {'temperature': 0, 'max_tokens': 512, 'enable_thinking': False, 'stream': False},
        'automatic_retries': 0, 'max_attempts': MAX_ATTEMPTS, 'request_reservation_rmb': RESERVE_RMB,
        'run_budget_rmb': RUN_BUDGET_RMB, 'user_total_budget_rmb': 100, 'prior_smoke_estimate_rmb': PRIOR_SMOKE_ESTIMATE_RMB,
        'budget_basis': 'At most 262144 input tokens at 3 RMB/M plus 512 output tokens at 30 RMB/M is below 1 RMB. Reserve 1 RMB per attempt, including missing usage. 80 attempts < 90 RMB run ceiling < 100 RMB authorization.',
        'pricing_checked_date': '2026-10-27', 'pricing_source': 'https://help.aliyun.com/zh/model-studio/qwen3-vl-plus',
        'scope': 'Synthetic request replay of official planner constructor; no native simulation, learned policy execution, robot success, System 2 improvement, or whole-system speed comparison.',
        'registry_scope': '22 public capability records wired into a request-only registry; not an installed executable skill library.',
        'semantic_quality_scope': 'Example composition choice has no unique correctness label. Registry score measures agreement with predeclared capability-matching labels, not physical success.',
        'timing_scope': 'Non-streaming HTTP wall time including network, queue, input processing and output; TTFT and pure inference time unmeasured.',
        'order': 'Per input, AB/BA balanced over four repetitions; pair groups shuffled using fixed seed. Cache left to provider, measured, never assumed cold.'})
    (out / 'experiment_script.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps({'prepared': str(out), 'requests': len(schedule), 'unique_payloads': len(payloads), 'pair_checks': len(validations), 'maximum_reserved_rmb': MAX_ATTEMPTS * RESERVE_RMB}))


def eligible(n_started, budget=RUN_BUDGET_RMB):
    return n_started < MAX_ATTEMPTS and (n_started + 1) * RESERVE_RMB + PRIOR_SMOKE_ESTIMATE_RMB < budget


def validate_reply(reply, item, registry, planner):
    # Reuse the actual official response validator with offline mocked transport.
    agent = planner.AgentPlanner.__new__(planner.AgentPlanner)
    agent.api_key, agent.endpoint, agent.model = 'offline-no-secret', 'https://invalid.example', MODEL
    operation = item['suite'] == 'registry_22_operations'
    catalogue = registry['operation_catalogue'] if operation else registry['composition_catalogue']
    program = registry['program'] if operation else None
    def response(*args, **kwargs):
        return io.BytesIO(json.dumps(reply).encode())
    try:
        with patch('urllib.request.urlopen', response):
            plan = agent.plan(instruction='Offline validation only.', observation={}, memory={}, previous_plan=None,
                              compositions=catalogue, operation_program=program)
        return True, plan, None
    except Exception as exc:
        return False, None, type(exc).__name__


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def run(out, until):
    manifest = load(out / 'manifest.json')
    assert digest(Path(__file__).read_bytes()) == digest((out / 'experiment_script.py').read_bytes()), 'Experiment source changed'
    for relative, sha in manifest['source_hashes'].items():
        assert digest((REPO / relative).read_bytes()) == sha, 'Official source changed'
    assert os.environ.get('PHYSICALRSI_AGENT_ENDPOINT') == ENDPOINT
    assert os.environ.get('PHYSICALRSI_AGENT_MODEL') == MODEL
    key = os.environ['PHYSICALRSI_AGENT_API_KEY']
    registry = load(out / 'validation_registry.json')
    planner, _ = source_modules()
    labels = {x['id']: x['expected_operation'] for x in manifest['tasks']}
    journal = out / 'events.jsonl'
    events = [json.loads(line) for line in journal.read_text().splitlines()] if journal.exists() else []
    started = {x['id'] for x in events if x['event'] == 'started'}
    done = {x['id'] for x in events if x['event'] == 'completed'}
    if started - done:
        raise RuntimeError('Unresolved previous request; stop to reconcile billing before resume')
    rows = [load(p) for p in sorted((out / 'responses').glob('*.json'))] if (out / 'responses').exists() else []
    opener = urllib.request.build_opener(NoRedirect())
    for item in manifest['schedule'][:until]:
        if item['id'] in done:
            continue
        if not eligible(len(started)):
            raise RuntimeError('Hard request/reserved-budget cap reached')
        body = load(out / 'requests' / (item['request_id'] + '.json'))
        assert digest(body) == manifest['request_hashes'][item['request_id']]
        assert body['max_tokens'] == 512 and body['enable_thinking'] is False
        request = urllib.request.Request(ENDPOINT, data=json.dumps(body).encode(), method='POST',
                                         headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key})
        row = {**item, 'started_at_utc': now(), 'http_status': None, 'input_tokens': None, 'output_tokens': None,
               'total_tokens': None, 'cached_input_tokens': None, 'image_tokens': None, 'reasoning_output_tokens': None,
               'raw_usage': None, 'json_valid': False, 'contract_valid': False, 'label_agreement': None,
               'native_success': None, 'estimated_uncached_list_cost_rmb': None, 'usage_source': 'unavailable'}
        append(journal, {'event': 'started', 'id': item['id'], 'time': now(), 'reserved_rmb': RESERVE_RMB})
        started.add(item['id'])
        t0 = time.perf_counter()
        fatal = False
        try:
            with opener.open(request, timeout=60) as response:
                row['http_status'] = response.status
                raw = response.read(2_000_000)
            row['elapsed_seconds'] = time.perf_counter() - t0
            reply = json.loads(raw)
            row['response_sha256'] = digest(raw)
            row['provider_id'] = reply.get('id')
            row['model_reported'] = reply.get('model')
            row['raw_usage'] = usage = reply.get('usage') or {}
            for target, origin in [('input_tokens', 'prompt_tokens'), ('output_tokens', 'completion_tokens'), ('total_tokens', 'total_tokens')]:
                value = usage.get(origin)
                row[target] = value if isinstance(value, int) and value >= 0 else None
            details = usage.get('prompt_tokens_details') or {}
            row['cached_input_tokens'] = details.get('cached_tokens')
            row['image_tokens'] = details.get('image_tokens')
            row['reasoning_output_tokens'] = (usage.get('completion_tokens_details') or {}).get('reasoning_tokens')
            if row['input_tokens'] is not None and row['output_tokens'] is not None:
                row['usage_source'] = 'provider'
                n, m = row['input_tokens'], row['output_tokens']
                rate = 1 if n <= 32000 else 1.5 if n <= 128000 else 3
                row['estimated_uncached_list_cost_rmb'] = (n * rate + m * 10 * rate) / 1_000_000
                if row['estimated_uncached_list_cost_rmb'] > RESERVE_RMB:
                    fatal = True
            else:
                fatal = True
            choice = reply.get('choices', [{}])[0]
            row['finish_reason'] = choice.get('finish_reason')
            row['output_text'] = choice.get('message', {}).get('content')
            try:
                parsed = json.loads(row['output_text'])
                row['json_valid'] = isinstance(parsed, dict)
            except (TypeError, ValueError):
                pass
            row['contract_valid'], plan, row['validation_error'] = validate_reply(reply, item, registry, planner)
            if item['suite'] == 'registry_22_operations':
                row['label_agreement'] = row['contract_valid'] and plan['operations'] == [labels[item['task']]]
        except urllib.error.HTTPError as exc:
            row['http_status'] = exc.code
            row['error_type'] = type(exc).__name__
            try:
                error = json.loads(exc.read(65536)).get('error', {})
                code = str(error.get('code', 'unknown'))
                row['provider_error_code'] = code if re.fullmatch(r'[A-Za-z0-9_.-]{1,100}', code) else 'redacted'
            except Exception:
                pass
            fatal = True
        except Exception as exc:
            row['error_type'] = type(exc).__name__
            fatal = True
        row.setdefault('elapsed_seconds', time.perf_counter() - t0)
        row['finished_at_utc'] = now()
        save(out / 'responses' / (item['id'] + '.json'), row)
        append(journal, {'event': 'completed', 'id': item['id'], 'time': now()})
        done.add(item['id']); rows.append(row)
        print(json.dumps({k: row.get(k) for k in ('sequence', 'suite', 'task', 'condition', 'http_status', 'input_tokens', 'output_tokens', 'cached_input_tokens', 'elapsed_seconds', 'contract_valid', 'label_agreement', 'error_type', 'provider_error_code')}, ensure_ascii=False), flush=True)
        if fatal:
            print('Stopped after transport, unknown-usage, or reservation anomaly; no automatic retry.', flush=True)
            break
    analyze(out)


def bootstrap(values):
    if not values:
        return None
    rng = random.Random(7721)
    draws = sorted(statistics.mean(rng.choices(values, k=len(values))) for _ in range(4000))
    return [draws[100], draws[3899]]


def analyze(out):
    rows = [load(p) for p in (out / 'responses').glob('*.json')]
    rows.sort(key=lambda x: x['sequence'])
    if not rows:
        return
    fields = ['sequence', 'id', 'suite', 'task', 'repeat', 'condition', 'pair_order', 'http_status', 'input_tokens', 'output_tokens', 'total_tokens', 'cached_input_tokens', 'image_tokens', 'elapsed_seconds', 'json_valid', 'contract_valid', 'label_agreement', 'finish_reason', 'estimated_uncached_list_cost_rmb']
    with (out / 'calls.csv').open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore'); writer.writeheader(); writer.writerows(rows)
    groups, pair_map = defaultdict(list), defaultdict(dict)
    for row in rows:
        groups[(row['suite'], row['condition'])].append(row)
        pair_map[(row['suite'], row['task'], row['repeat'])][row['condition']] = row
    summaries = []
    for (suite, condition), values in sorted(groups.items()):
        item = {'suite': suite, 'condition': condition, 'calls': len(values),
                'http_ok': sum(x['http_status'] == 200 for x in values),
                'json_valid': sum(x['json_valid'] for x in values), 'contract_valid': sum(x['contract_valid'] for x in values),
                'label_agreement': sum(x['label_agreement'] is True for x in values) if suite == 'registry_22_operations' else None,
                'cache_hit_calls': sum((x['cached_input_tokens'] or 0) > 0 for x in values)}
        for metric in ['input_tokens', 'output_tokens', 'total_tokens', 'elapsed_seconds', 'cached_input_tokens', 'image_tokens']:
            data = [x[metric] for x in values if x[metric] is not None]
            item[metric + '_mean'] = statistics.mean(data) if data else None
            item[metric + '_median'] = statistics.median(data) if data else None
        summaries.append(item)
    pairs, comparisons = [], []
    for (suite, task, repeat), pair in pair_map.items():
        if set(pair) != {'projected', 'unprojected'}:
            continue
        p, u = pair['projected'], pair['unprojected']
        if p['input_tokens'] is None or u['input_tokens'] is None:
            continue
        values = {'suite': suite, 'task': task, 'repeat': repeat}
        for metric in ['input_tokens', 'total_tokens', 'elapsed_seconds']:
            values[metric + '_reduction_pct'] = 100 * (u[metric] - p[metric]) / u[metric]
            values[metric + '_saved'] = u[metric] - p[metric]
        pairs.append(values)
    for suite in sorted({x['suite'] for x in rows}):
        available = [x for x in pairs if x['suite'] == suite]
        comparison = {'suite': suite, 'complete_pairs': len(available)}
        for metric in ['input_tokens', 'total_tokens', 'elapsed_seconds']:
            by_task = defaultdict(list)
            for x in available:
                by_task[x['task']].append(x[metric + '_reduction_pct'])
            task_means = [statistics.mean(v) for v in by_task.values()]
            comparison[metric + '_reduction_pct_task_mean'] = statistics.mean(task_means) if task_means else None
            comparison[metric + '_reduction_pct_task_bootstrap95'] = bootstrap(task_means)
        comparisons.append(comparison)
    save(out / 'paired_comparisons.json', pairs)
    completed = len(rows)
    cost = sum(x['estimated_uncached_list_cost_rmb'] or 0 for x in rows)
    summary = {'updated_utc': now(), 'completed_attempts': completed, 'planned_attempts': MAX_ATTEMPTS,
               'provider_usage_calls': sum(x['usage_source'] == 'provider' for x in rows),
               'known_uncached_list_cost_rmb': cost, 'unknown_cost_attempts': sum(x['estimated_uncached_list_cost_rmb'] is None for x in rows),
               'reserved_cost_upper_bound_rmb': completed * RESERVE_RMB,
               'including_prior_smoke_list_estimate_rmb': cost + PRIOR_SMOKE_ESTIMATE_RMB,
               'groups': summaries, 'comparisons': comparisons,
               'uncertainty': 'Exploratory percentile bootstrap over five synthetic task-level means, not population or robot-task confidence intervals.',
               'cost_note': 'Undiscounted list-price estimate from provider usage, not the billing console. Cache/free-credit discounts not subtracted.'}
    save(out / 'summary.json', summary)
    print(json.dumps({'completed_attempts': completed, 'known_uncached_list_cost_rmb': cost, 'comparisons': comparisons}, ensure_ascii=False), flush=True)


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'run', 'analyze', 'self-check'])
    parser.add_argument('--output', type=Path)
    parser.add_argument('--until', type=int, default=20)
    args = parser.parse_args()
    if args.action == 'self-check':
        assert eligible(0) and eligible(79) and not eligible(80)
        assert not eligible(0, budget=1)
        a = {'messages': [{'content': 'same'}, {'content': [{'text': json.dumps({'available_compositions': {'a': 1}, 'instruction': 'same'})}]}]}
        b = deepcopy(a); b['messages'][1]['content'][0]['text'] = json.dumps({'available_compositions': {'a': 2}, 'instruction': 'same'})
        assert pair_diff(a, b, 'example_2_compositions') == ['available_compositions']
        b['messages'][0]['content'] = 'unexpected'
        try:
            pair_diff(a, b, 'example_2_compositions')
            raise RuntimeError('Pair contamination was not detected')
        except AssertionError:
            pass
        print('Budget boundary and paired-input contamination checks passed; no API calls.')
        return
    if not args.output or not 1 <= args.until <= MAX_ATTEMPTS:
        parser.error('Output path and bounded --until required')
    if args.action == 'prepare':
        prepare(args.output)
    elif args.action == 'analyze':
        analyze(args.output)
    else:
        with (args.output / '.run.lock').open('w') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            run(args.output, args.until)


if __name__ == '__main__':
    main()

