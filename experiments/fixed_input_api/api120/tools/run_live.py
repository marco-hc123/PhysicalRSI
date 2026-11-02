"""Run the frozen 120-request study; monetary ceiling removed by user instruction."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import csv
import fcntl
import getpass
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import socket
import statistics
import sys
import time
import types
import urllib.error
import urllib.request
from unittest.mock import patch

BASE_URL = 'https://ws-lckd7q7bpskdc5qj.cn-beijing.maas.aliyuncs.com/compatible-mode/v1'
MODEL = 'qwen3-vl-plus'
_SECRET = None


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def canonical(value):
    return sha(json.dumps(value, ensure_ascii=False, sort_keys=True).encode())


def safe_bytes(data):
    if _SECRET and _SECRET.encode() in data:
        data = data.replace(_SECRET.encode(), b'[REDACTED]')
    return data


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = safe_bytes((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode())
    tmp = path.with_suffix(path.suffix + '.tmp')
    with tmp.open('wb') as file:
        file.write(data); file.flush(); os.fsync(file.fileno())
    tmp.replace(path)


def event(root, value):
    with (root / 'events.jsonl').open('ab') as file:
        file.write(safe_bytes((json.dumps(value, ensure_ascii=False) + '\n').encode()))
        file.flush(); os.fsync(file.fileno())


def load_official(root):
    folder = root / 'inputs/source_evidence/PhysicalRSI_baselines/robodojo'
    package = types.ModuleType('frozen_planner')
    package.__path__ = [str(folder)]
    sys.modules['frozen_planner'] = package
    for name in ('capability_memory', 'agent_planner'):
        spec = importlib.util.spec_from_file_location('frozen_planner.' + name, folder / (name + '.py'))
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
    return sys.modules['frozen_planner.agent_planner']


def validate_response(planner, registry, result):
    agent = planner.AgentPlanner.__new__(planner.AgentPlanner)
    agent.api_key, agent.endpoint, agent.model = 'offline-placeholder', 'https://invalid.example', MODEL
    data = json.dumps(result).encode()
    try:
        with patch('urllib.request.urlopen', lambda *a, **k: io.BytesIO(data)):
            plan = agent.plan(instruction='Offline output validation', observation={}, memory={}, previous_plan=None,
                              compositions=registry['operation_catalogue'], operation_program=registry['program'])
        return True, plan, None
    except Exception as exc:
        return False, None, type(exc).__name__


def verify_inputs(root):
    manifest = read(root / 'execution_manifest.json')
    assert sha(Path(__file__).read_bytes()) == manifest['runner_sha256'], 'Runner changed after freeze'
    for entry in manifest['input_files']:
        assert sha((root / 'inputs' / entry['path']).read_bytes()) == entry['sha256'], entry['path']
    schedule = read(root / 'inputs/schedule.json')
    assert len(schedule) == manifest['planned_attempts'] == 120
    assert len({x['id'] for x in schedule}) == 120
    requests = read(root / 'inputs/request_manifest.json')
    assert len(requests) == 40
    for entry in requests.values():
        body = read(root / 'inputs' / entry['path'])
        assert canonical(body) == entry['canonical_sha256']
        assert body['model'] == MODEL and body['temperature'] == 0
        assert body['max_tokens'] == 512 and not body['stream'] and not body['enable_thinking']
    return manifest, schedule, requests


def initialise(root, prepared):
    assert not (root / 'execution_manifest.json').exists(), 'Refusing to overwrite a frozen run'
    root.mkdir(parents=True, exist_ok=True)
    os.chmod(root, 0o700)
    prepared_manifest = read(prepared / 'file_manifest.json')
    for entry in prepared_manifest:
        assert sha((prepared / entry['path']).read_bytes()) == entry['sha256'], entry['path']
    destination = root / 'inputs'
    destination.mkdir()
    for directory in ('requests', 'images', 'source_evidence'):
        shutil.copytree(prepared / directory, destination / directory)
    for name in ('scenes.json', 'labels_not_sent_to_model.json', 'schedule.json', 'request_manifest.json', 'protocol.json', 'offline_validation.json'):
        shutil.copyfile(prepared / name, destination / name)
    (destination / 'basis').mkdir()
    shutil.copyfile(prepared / 'basis/validation_registry.json', destination / 'basis/validation_registry.json')
    input_files = [dict(path=str(p.relative_to(destination)), sha256=sha(p.read_bytes()), bytes=p.stat().st_size)
                   for p in sorted(destination.rglob('*')) if p.is_file()]
    manifest = dict(created_utc=now(), source_commit='90b322a3a362aad14125f36d8ed080ca31daaea6',
                    source_preparation=str(prepared), preparation_manifest_sha256=sha((prepared / 'file_manifest.json').read_bytes()),
                    planned_attempts=120, model=MODEL, endpoint=BASE_URL + '/chat/completions',
                    monetary_limit_rmb=None, budget_limit_enforced=False,
                    authorization='User requested immediate execution with the supplied personal API key and URL, no monetary ceiling, and raw records plus concise summaries only.',
                    amendment='Overrides preparation execution_enabled=false and proposed 10/100 RMB limits. Request payloads, labels, schedule and model settings are unchanged.',
                    credentials_persisted=False, automatic_retries=0, checkpoints=[40,80,120],
                    transport_timeout_seconds=120, maximum_response_bytes=2000000,
                    stopping_rule='Stop at 120 attempts or on transport, unknown-usage, truncated-output or model mismatch anomalies; no retry without review.',
                    input_files=input_files, runner_sha256=sha(Path(__file__).read_bytes()),
                    runtime=dict(python=platform.python_version(), hostname=socket.gethostname(), platform=platform.platform()),
                    scope='Synthetic fixed-input API study, not native robot evaluation. No GPU or shared model endpoint.',
                    report_policy='Machine-readable evidence and brief English status only. Detailed Chinese analysis deferred until requested.')
    save(root / 'execution_manifest.json', manifest)
    (root / 'README.txt').write_text(
        'Frozen 20-scene API execution (120 attempts planned).\n'
        'inputs/ is a byte-verified copy of the relevant prepared inputs.\n'
        'execution_manifest.json overrides the old proposed monetary ceiling; there is no monetary ceiling.\n'
        'events.jsonl records every started/completed request. raw_responses/ preserves API replies.\n'
        'responses/ contains per-attempt records. calls.csv and summary.json are concise derived records.\n'
        'status.json records completion or interruption. No automatic retries.\n'
        'No detailed Chinese analysis is generated. This is a synthetic input study, not a robot rollout.\n'
        'API credentials are read interactively into process memory and are not saved.\n', encoding='utf-8')
    verify_inputs(root)
    print(json.dumps(dict(initialised=str(root), requests=120, monetary_limit=None, api_calls=0)), flush=True)


def valid_count(value):
    return value if type(value) is int and value >= 0 else None


def summarize(root, state, stopped_reason=None):
    rows = sorted([read(p) for p in (root / 'responses').glob('*.json')], key=lambda x:x['sequence'])
    starts = [json.loads(x) for x in (root / 'events.jsonl').read_text().splitlines()] if (root / 'events.jsonl').exists() else []
    started_ids = {x['id'] for x in starts if x['event'] == 'started'}
    completed_ids = {x['id'] for x in starts if x['event'] == 'completed'}
    fields = ['sequence','id','scene_id','family','family_seen_in_stage1','repeat','condition','pair_id','pair_order',
              'started_at_utc','finished_at_utc','http_status','provider_id','model_reported','input_tokens','output_tokens',
              'total_tokens','cached_input_tokens','image_tokens','elapsed_seconds','json_valid','contract_valid',
              'label_agreement','finish_reason','validation_error','error_type','request_sha256','response_sha256']
    buffer = io.StringIO(); writer = csv.DictWriter(buffer, fieldnames=fields, extrasaction='ignore')
    writer.writeheader(); writer.writerows(rows)
    tmp = root / 'calls.csv.tmp'; tmp.write_bytes(b'\xef\xbb\xbf' + safe_bytes(buffer.getvalue().encode())); tmp.replace(root / 'calls.csv')
    groups = []
    for condition in ('unprojected','projected'):
        selected = [x for x in rows if x['condition'] == condition]
        group = dict(condition=condition, calls=len(selected), http_ok=sum(x['http_status']==200 for x in selected),
                     contract_valid=sum(x['contract_valid'] for x in selected), label_agreement=sum(x['label_agreement'] is True for x in selected))
        for metric in ('input_tokens','output_tokens','total_tokens','elapsed_seconds'):
            values = [x[metric] for x in selected if x.get(metric) is not None]
            group[metric + '_mean'] = statistics.mean(values) if values else None
        groups.append(group)
    summary = dict(updated_utc=now(), status=state, planned_attempts=120, started_attempts=len(started_ids),
                   recorded_responses=len(rows), completed_events=len(completed_ids), unresolved_attempts=sorted(started_ids-completed_ids),
                   http_successes=sum(x['http_status']==200 for x in rows), json_valid=sum(x['json_valid'] for x in rows),
                   contract_valid=sum(x['contract_valid'] for x in rows), label_agreement=sum(x['label_agreement'] is True for x in rows),
                   usage_coverage=sum(x['usage_source']=='provider' for x in rows),
                   input_tokens_total=sum(x['input_tokens'] or 0 for x in rows), output_tokens_total=sum(x['output_tokens'] or 0 for x in rows),
                   total_tokens=sum(x['total_tokens'] or 0 for x in rows),
                   unknown_usage_attempts=sum(x['usage_source']!='provider' for x in rows),
                   cache_hit_calls=sum((x['cached_input_tokens'] or 0)>0 for x in rows),
                   truncated_outputs=sum(x.get('finish_reason')=='length' for x in rows),
                   groups=groups, monetary_limit_rmb=None, automatic_retries=0, actual_invoice_verified=False,
                   monetary_cost_estimated=False, stopped_reason=stopped_reason,
                   analysis_status='Detailed interpretation deferred by user request; nominal token sums exclude unknown usage rather than asserting it is zero.')
    save(root / 'summary.json', summary)
    save(root / 'status.json', {k:summary[k] for k in ('updated_utc','status','planned_attempts','started_attempts','recorded_responses','unresolved_attempts','stopped_reason')})
    return summary


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def run(root, until):
    global _SECRET
    manifest, schedule, requests = verify_inputs(root)
    assert 1 <= until <= 120
    events = [json.loads(x) for x in (root / 'events.jsonl').read_text().splitlines()] if (root / 'events.jsonl').exists() else []
    start_ids = [x['id'] for x in events if x['event']=='started']
    done_ids = [x['id'] for x in events if x['event']=='completed']
    assert len(start_ids)==len(set(start_ids)) and len(done_ids)==len(set(done_ids))
    assert set(start_ids)==set(done_ids), 'Unresolved prior request: reconcile before resuming'
    rows = [read(p) for p in (root / 'responses').glob('*.json')]
    assert {x['id'] for x in rows} == set(done_ids), 'Journal/response mismatch'
    assert all(x['usage_source']=='provider' and x['http_status']==200 for x in rows), 'Review failed attempts before resuming'
    assert all(x.get('finish_reason')!='length' and x.get('model_reported')==MODEL for x in rows)
    done = set(done_ids)
    registry = read(root / 'inputs/basis/validation_registry.json')
    scenes = {x['id']:x for x in read(root / 'inputs/scenes.json')}
    labels = {x['scene_id']:x['expected_operations'] for x in read(root / 'inputs/labels_not_sent_to_model.json')}
    planner = load_official(root)
    opener = urllib.request.build_opener(NoRedirect())
    assert manifest['endpoint']==BASE_URL+'/chat/completions'
    if all(x['id'] in done for x in schedule[:until]):
        return summarize(root,'completed' if len(done)==120 else 'checkpoint')
    _SECRET = getpass.getpass('Personal API key (hidden, not saved): ').strip()
    if not _SECRET:
        raise ValueError('API key is empty')
    # Continue writing durable records if the terminal connection drops.
    signal.signal(signal.SIGHUP, signal.SIG_IGN)
    stopped_reason = None
    try:
        for item in schedule[:until]:
            if item['id'] in done:
                continue
            assert len(start_ids) < 120
            body = read(root / 'inputs' / requests[item['request_id']]['path'])
            assert canonical(body)==requests[item['request_id']]['canonical_sha256']
            body_bytes = json.dumps(body).encode()
            request = urllib.request.Request(manifest['endpoint'], data=body_bytes, method='POST',
                      headers={'Content-Type':'application/json','Authorization':'Bearer '+_SECRET})
            scene = scenes[item['scene_id']]
            row = {**item, 'family':scene['family'], 'family_seen_in_stage1':scene['family_seen_in_stage1'],
                   'started_at_utc':now(), 'http_status':None, 'input_tokens':None,'output_tokens':None,'total_tokens':None,
                   'cached_input_tokens':None,'image_tokens':None, 'raw_usage':None, 'usage_source':'unavailable',
                   'json_valid':False,'contract_valid':False,'label_agreement':False,'native_success':None,
                   'request_sha256':sha(body_bytes),'request_canonical_sha256':canonical(body),
                   'provider_id':None,'model_reported':None,'output_text':None,'validation_error':None,'error_type':None}
            event(root, dict(event='started',id=item['id'],sequence=item['sequence'],time=now(),request_sha256=sha(body_bytes)))
            start_ids.append(item['id'])
            begin = time.perf_counter()
            raw = None
            fatal = None
            try:
                with opener.open(request, timeout=120) as response:
                    row['http_status'] = response.status
                    raw = response.read(2000001)
                row['elapsed_seconds'] = time.perf_counter()-begin
                if len(raw)>2000000:
                    raise ValueError('Response body too large')
                result = json.loads(raw)
                row['provider_id'] = result.get('id')
                row['model_reported'] = result.get('model')
                usage = result.get('usage') or {}
                row['raw_usage'] = usage
                for target, source in [('input_tokens','prompt_tokens'),('output_tokens','completion_tokens'),('total_tokens','total_tokens')]:
                    row[target] = valid_count(usage.get(source))
                details = usage.get('prompt_tokens_details') or {}
                row['cached_input_tokens'] = valid_count(details.get('cached_tokens'))
                row['image_tokens'] = valid_count(details.get('image_tokens'))
                row['reasoning_tokens'] = (usage.get('completion_tokens_details') or {}).get('reasoning_tokens')
                if all(row[k] is not None for k in ('input_tokens','output_tokens','total_tokens')):
                    row['usage_source']='provider'
                    if row['input_tokens']+row['output_tokens']!=row['total_tokens']:
                        fatal='inconsistent_usage'
                else:
                    fatal='unknown_usage'
                choice = result.get('choices',[{}])[0]
                row['finish_reason'] = choice.get('finish_reason')
                row['output_text'] = choice.get('message',{}).get('content')
                try:
                    row['json_valid']=isinstance(json.loads(row['output_text']),dict)
                except (ValueError,TypeError):
                    pass
                row['contract_valid'], plan, row['validation_error'] = validate_response(planner, registry, result)
                row['label_agreement']=row['contract_valid'] and plan['operations']==labels[item['scene_id']]
                if row['finish_reason']=='length':
                    fatal='truncated_output'
                if row['model_reported']!=MODEL:
                    fatal='model_mismatch'
            except urllib.error.HTTPError as exc:
                row['http_status']=exc.code
                row['error_type']=type(exc).__name__
                raw=exc.read(2000000)
                fatal='http_error'
            except Exception as exc:
                row['error_type']=type(exc).__name__
                fatal='transport_or_parse_error'
            row.setdefault('elapsed_seconds',time.perf_counter()-begin)
            row['finished_at_utc']=now()
            if raw is not None:
                clean = safe_bytes(raw)
                raw_path=root/'raw_responses'/(item['id']+'.json')
                raw_path.parent.mkdir(exist_ok=True)
                with raw_path.open('wb') as file:
                    file.write(clean);file.flush();os.fsync(file.fileno())
                row['response_sha256']=sha(clean)
                row['credential_redacted_from_response']=(raw!=clean)
            save(root/'responses'/(item['id']+'.json'),row)
            event(root,dict(event='completed',id=item['id'],sequence=item['sequence'],time=now(),http_status=row['http_status']))
            done.add(item['id'])
            summarize(root,'running' if not fatal else 'stopped',fatal)
            progress={k:row.get(k) for k in ('sequence','scene_id','condition','http_status','input_tokens','output_tokens','elapsed_seconds','contract_valid','label_agreement','error_type')}
            try:
                print(json.dumps(progress),flush=True)
            except OSError:
                pass
            if fatal:
                stopped_reason=fatal
                break
    finally:
        _SECRET=None
        state='completed' if len(done)==120 and stopped_reason is None else 'stopped' if stopped_reason else 'checkpoint'
        summary=summarize(root,state,stopped_reason)
    return summary


def self_check(root):
    manifest,schedule,requests=verify_inputs(root)
    registry=read(root/'inputs/basis/validation_registry.json')
    planner=load_official(root)
    def reply(operations):
        return {'choices':[{'message':{'content':json.dumps(dict(composition='memory-guided-program-library',operations=operations,rationale='Offline self-check'))}}]}
    assert validate_response(planner,registry,reply(['general-pickup']))[0]
    assert not validate_response(planner,registry,reply([{'handle':'general-pickup'}]))[0]
    assert manifest['monetary_limit_rmb'] is None and not manifest['budget_limit_enforced']
    assert set(Counter(x['request_id'] for x in schedule).values())=={3}
    print('Offline checks passed; no API calls.',flush=True)


def main():
    os.umask(0o077)
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['init','check','run','summarize'])
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--prepared',type=Path)
    parser.add_argument('--until',type=int,default=120)
    args=parser.parse_args();root=args.root.resolve()
    if args.action=='init':
        initialise(root,args.prepared.resolve())
    elif args.action=='check':
        with patch('socket.socket.connect',side_effect=RuntimeError('Offline check')):
            self_check(root)
    elif args.action=='run':
        with (root/'.execution.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            summary=run(root,args.until)
        print(json.dumps({k:summary[k] for k in ('status','recorded_responses','input_tokens_total','output_tokens_total','contract_valid','label_agreement','stopped_reason')}),flush=True)
    else:
        previous=read(root/'status.json')
        summarize(root,previous['status'],previous['stopped_reason'])


if __name__=='__main__':
    main()
