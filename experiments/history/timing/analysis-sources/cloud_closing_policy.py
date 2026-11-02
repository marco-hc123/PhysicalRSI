"""Measure the unmodified pinned PhysicalRSI planner and skill runtime."""
import argparse
import asyncio
import base64
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import signal
import time
import types
import urllib.error
import urllib.request

import numpy as np
import yaml

parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--task', required=True)
parser.add_argument('--output-contract',choices=['original','typed'],default='original')
parser.add_argument('--port', type=int, default=6012)
args = parser.parse_args()
OUT = args.output
OUT.mkdir(parents=True, exist_ok=True)
ROOT = Path('/mnt/data/physical-RSI')
REPO = ROOT/'code/RoboDojo'
API = OUT/'api'
API.mkdir(exist_ok=True)
credential = json.loads((Path('/home/ecs-user/.config/physicalrsi/agent.json')).read_text())
os.environ['PHYSICALRSI_AGENT_API_KEY'] = credential['api_key']
started = time.monotonic()
status = dict(state='initializing', task=args.task, output_contract=args.output_contract, api_attempts=0, logical_calls=0,
              observation_calls=0, action_calls=0, returned_actions=0, episode_index=-1,
              model=credential['model'], pid=os.getpid())


def safe(v):
    if isinstance(v, str):
        return v.replace(credential['api_key'], '[REDACTED]')
    if isinstance(v, dict):
        return {k: safe(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [safe(x) for x in v]
    if hasattr(v, 'item'):
        return v.item()
    return v


def write(path, v):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(safe(v), indent=2, default=str)+'\n')
    tmp.replace(path)


def event(kind, **values):
    row = dict(kind=kind, monotonic=time.monotonic(), unix=time.time(),
               episode_index=status['episode_index'], pid=os.getpid())
    row.update(values)
    with (OUT/'policy-events.jsonl').open('a') as f:
        f.write(json.dumps(safe(row), default=str)+'\n')


def save(state=None, **values):
    if state:
        status['state'] = state
    status.update(values, elapsed_seconds=time.monotonic()-started,
                  utc=datetime.now(timezone.utc).isoformat())
    write(OUT/'policy-status.json', status)


original_urlopen = urllib.request.urlopen


def measured_urlopen(request, timeout=120, **kwargs):
    if request.full_url != credential['endpoint']:
        raise ValueError('Unexpected planner endpoint')
    if status['api_attempts'] >= 12:
        raise RuntimeError('Preregistered per-process API attempt cap reached')
    status['api_attempts'] += 1
    number = status['api_attempts']
    payload = json.loads(request.data)
    if args.output_contract=='typed':
        from cloud_closing_contract import apply_contract
        payload=apply_contract(payload)
    assert payload['model'] == 'qwen3.7-plus' and payload['temperature'] == 0
    payload['enable_thinking'] = True
    request.data = json.dumps(payload).encode()
    evidence = json.loads(request.data)
    count = 0
    for message in evidence['messages']:
        if not isinstance(message.get('content'), list):
            continue
        for part in message['content']:
            if part.get('type') == 'image_url':
                data = base64.b64decode(part['image_url']['url'].split(',', 1)[1], validate=True)
                target = API/f'call-{number:03d}-image-{count}.png'
                target.write_bytes(data)
                part['image_url'] = dict(artifact=target.name, sha256=hashlib.sha256(data).hexdigest())
                count += 1
    write(API/f'call-{number:03d}-request.json', evidence)
    tick = time.monotonic()
    meta = dict(attempt=number, output_contract=args.output_contract, logical_call=status['logical_calls'],
                episode_index=status['episode_index'], started_monotonic=tick,
                started_utc=datetime.now(timezone.utc).isoformat(), image_count=count,
                request_sha256=hashlib.sha256(request.data).hexdigest())
    event('transport_start', attempt=number, logical_call=status['logical_calls'])
    save('calling_agent')
    try:
        with original_urlopen(request, timeout=max(timeout, 300), **kwargs) as response:
            raw = response.read()
            meta['http_status'] = response.status
        value = json.loads(raw)
        write(API/f'call-{number:03d}-response.json', value)
        meta.update(success=True, returned_model=value.get('model'), usage=value.get('usage'),
                    finish_reason=value.get('choices', [{}])[0].get('finish_reason'))
        return io.BytesIO(raw)
    except urllib.error.HTTPError as e:
        meta.update(success=False, http_status=e.code, error_body=e.read().decode(errors='replace')[:4000])
        raise
    except Exception as e:
        meta.update(success=False, error_type=type(e).__name__, error=str(e))
        raise
    finally:
        meta['seconds'] = time.monotonic()-tick
        write(API/f'call-{number:03d}-metadata.json', meta)
        event('transport_end', **meta)


import PhysicalRSI_baselines.robodojo.agent_planner as planner_module
import PhysicalRSI_baselines.robodojo.skill_model as skill_module

assert hashlib.sha256(Path(planner_module.__file__).read_bytes()).hexdigest() == 'd6f6936d5b57283c7c8affacd857356f9b1e8f8d5f54a7b6959a4e70c1cb25db'
planner_module.urllib = types.SimpleNamespace(
    request=types.SimpleNamespace(Request=urllib.request.Request, urlopen=measured_urlopen),
    error=urllib.error)
original_plan = planner_module.AgentPlanner.plan


def plan(self, **kwargs):
    status['logical_calls'] += 1
    number, tick = status['logical_calls'], time.monotonic()
    event('logical_plan_start', logical_call=number)
    try:
        result = original_plan(self, **kwargs)
        write(OUT/f'plan-{number:03d}.json', dict(valid=True, plan=result,
              episode_index=status['episode_index'], seconds=time.monotonic()-tick))
        event('logical_plan_end', logical_call=number, plan=result, seconds=time.monotonic()-tick)
        return result
    except Exception as e:
        write(OUT/f'plan-{number:03d}.json', dict(valid=False, error_type=type(e).__name__,
              error=str(e), episode_index=status['episode_index'], seconds=time.monotonic()-tick))
        event('logical_plan_error', logical_call=number, error_type=type(e).__name__, error=str(e))
        raise


planner_module.AgentPlanner.plan = plan
original_load = skill_module.load_skill


def load_skill(descriptor, deployment):
    tick = time.monotonic()
    event('skill_load_start', name=descriptor.get('name'), implementation=descriptor.get('implementation'))
    result = original_load(descriptor, deployment)
    event('skill_load_end', name=descriptor.get('name'), seconds=time.monotonic()-tick)
    close = result.close
    def measured_close():
        event('skill_close_start', name=descriptor.get('name'))
        try:
            return close()
        finally:
            event('skill_close_end', name=descriptor.get('name'))
    result.close = measured_close
    return result


skill_module.load_skill = load_skill
from XPolicyLab.policy.physicalRSI.model import Model
from client_server.ws.model_server import PolicyServer, PolicyServerConfig


def instrument(runtime):
    observe, action, reset = runtime.update_obs_batch, runtime.get_action_batch, runtime.reset
    seen = False
    def measured_observe(rows):
        nonlocal seen
        if not seen:
            seen = True
            status['episode_index'] += 1
            row = rows[0]
            arrays = {'instruction': np.asarray(row['instruction'])}
            arrays.update({'state__'+k: np.asarray(v) for k, v in row['state'].items()})
            arrays.update({'camera__'+k: np.asarray(v['color']) for k, v in row['vision'].items()})
            np.savez_compressed(OUT/f"observation-{status['episode_index']:03d}.npz", **arrays)
            event('first_observation', instruction=row['instruction'])
        status['observation_calls'] += 1
        try:
            return observe(rows)
        except Exception as e:
            event('observe_error', error_type=type(e).__name__, error=str(e))
            save('episode_error', error_type=type(e).__name__, error=str(e))
            raise
    def measured_action(env_idx_list=None):
        tick = time.monotonic()
        try:
            result = action(env_idx_list)
            counts = [len(v) for v in result]
            status['action_calls'] += 1
            status['returned_actions'] += sum(counts)
            event('action_batch', seconds=time.monotonic()-tick, counts=counts)
            save('executing_selected_skill')
            return result
        except Exception as e:
            event('action_error', error_type=type(e).__name__, error=str(e))
            save('episode_error', error_type=type(e).__name__, error=str(e))
            raise
    def measured_reset():
        nonlocal seen
        event('runtime_reset_start')
        result = reset()
        seen = False
        event('runtime_reset_end')
        return result
    runtime.update_obs_batch, runtime.get_action_batch, runtime.reset = measured_observe, measured_action, measured_reset


async def main():
    config = yaml.safe_load((REPO/'XPolicyLab/policy/physicalRSI/deploy.yml').read_text())
    config.update(bench_name='RoboDojo', task_name=args.task, ckpt_name='cross-project-measurement',
                  env_cfg_type='arx_x5', action_type='joint', seed=0, gpu_id=0,
                  host='127.0.0.1', port=args.port)
    write(OUT/'policy-deployment.json', config)
    event('policy_load_start')
    model = Model(config)
    runtime = model.model
    instrument(runtime)
    server = PolicyServer(model, PolicyServerConfig(host='127.0.0.1', port=args.port))
    shutdown = asyncio.Event()
    for sig in [signal.SIGTERM, signal.SIGINT]:
        asyncio.get_running_loop().add_signal_handler(sig, shutdown.set)
    try:
        await server.start()
        event('policy_ready', runtime_output=str(runtime.root), preloaded=list(runtime.preloaded))
        save('ready', runtime_output=str(runtime.root), ready_monotonic=time.monotonic())
        await shutdown.wait()
    finally:
        await server.stop()
        model.close()
        event('policy_closed')


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        save('fatal', error_type=type(e).__name__, error=str(e))
        raise
