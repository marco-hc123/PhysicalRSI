"""Instrument the pinned PhysicalRSI model without modifying its skill decisions."""
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
import urllib.request
import urllib.error

import numpy as np
import yaml

ROOT = Path('/mnt/data/physical-RSI')
REPO = ROOT / 'code/RoboDojo'
parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--port', type=int, default=6012)
args = parser.parse_args()
OUT = args.output
OUT.mkdir(parents=True, exist_ok=True)
API = OUT / 'api'
API.mkdir(exist_ok=True)
credentials = json.loads((Path.home()/'.config/physicalrsi/agent.json').read_text())
os.environ['PHYSICALRSI_AGENT_API_KEY'] = credentials['api_key']
started = time.monotonic()
status = dict(state='initializing', agent_enabled=True, api_attempts=0,
              observation_calls=0, action_calls=0, model=credentials['model'])


def safe(value):
    if isinstance(value, str):
        return value.replace(credentials['api_key'], '[REDACTED]')
    if isinstance(value, dict):
        return {key: safe(child) for key, child in value.items()}
    if isinstance(value, list):
        return [safe(child) for child in value]
    return value


def write(path, value):
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(safe(value), indent=2, default=str)+'\n')
    temporary.replace(path)


def save(state=None, **extra):
    status.update(extra)
    if state:
        status['state'] = state
    status.update(elapsed_seconds=time.monotonic()-started,
                  utc=datetime.now(timezone.utc).isoformat())
    write(OUT/'policy-status.json', status)


original_urlopen = urllib.request.urlopen


def measured_urlopen(request, timeout=120, **kwargs):
    """Preserve the planner payload and response; add only Qwen's mode switch."""
    if request.full_url != credentials['endpoint']:
        raise ValueError('Planner endpoint differs from the private credential binding')
    if status['api_attempts'] >= 6:
        raise RuntimeError('API attempt limit reached for this single-episode run')
    status['api_attempts'] += 1
    number = status['api_attempts']
    payload = json.loads(request.data)
    payload['enable_thinking'] = False
    request.data = json.dumps(payload).encode()
    evidence = json.loads(request.data)
    image_count = 0
    for message in evidence['messages']:
        if not isinstance(message.get('content'), list):
            continue
        for part in message['content']:
            if part.get('type') == 'image_url':
                url = part['image_url']['url']
                if not url.startswith('data:image/png;base64,'):
                    raise ValueError('Expected planner-produced RGB PNG data URL')
                data = base64.b64decode(url.split(',', 1)[1], validate=True)
                target = API/f'call-{number:03d}-image-{image_count}.png'
                target.write_bytes(data)
                part['image_url'] = dict(artifact=target.name,
                                         sha256=hashlib.sha256(data).hexdigest())
                image_count += 1
    write(API/f'call-{number:03d}-request.json', evidence)
    meta = dict(attempt=number, started_utc=datetime.now(timezone.utc).isoformat(),
                requested_model=payload['model'], image_count=image_count,
                request_sha256=hashlib.sha256(request.data).hexdigest(),
                scope='Planner API transport with original prompt and RGB observations')
    tick = time.monotonic()
    save('calling_agent')
    try:
        with original_urlopen(request, timeout=timeout, **kwargs) as response:
            raw = response.read()
            meta['http_status'] = response.status
        parsed = json.loads(raw)
        write(API/f'call-{number:03d}-response.json', parsed)
        meta.update(success=True, returned_model=parsed.get('model'),
                    usage=parsed.get('usage'),
                    finish_reason=parsed.get('choices', [{}])[0].get('finish_reason'))
        return io.BytesIO(raw)
    except urllib.error.HTTPError as error:
        meta.update(success=False, http_status=error.code,
                    error_body=error.read().decode(errors='replace')[:4000])
        raise
    except Exception as error:
        meta.update(success=False, error_type=type(error).__name__, error=str(error))
        raise
    finally:
        meta['seconds'] = time.monotonic()-tick
        write(API/f'call-{number:03d}-metadata.json', meta)
        save('agent_response_received' if meta.get('success') else 'agent_request_failed')


save()
import PhysicalRSI_baselines.robodojo.agent_planner as planner_module
# Limit transport instrumentation to this module; other urllib users are untouched.
planner_module.urllib = types.SimpleNamespace(
    request=types.SimpleNamespace(Request=urllib.request.Request, urlopen=measured_urlopen),
    error=urllib.error)
from XPolicyLab.policy.physicalRSI.model import Model
from client_server.ws.model_server import PolicyServer, PolicyServerConfig


class MeasuredModel(Model):
    def update_obs_batch(self, observations):
        if status['observation_calls'] == 0:
            row = observations[0]
            values = {'instruction': np.asarray(row['instruction'])}
            values.update({'state__'+key: np.asarray(value) for key, value in row['state'].items()})
            values.update({'camera__'+key: np.asarray(value['color']) for key, value in row['vision'].items()})
            np.savez_compressed(OUT/'first_observation.npz', **values)
        status['observation_calls'] += 1
        try:
            return super().update_obs_batch(observations)
        except Exception as error:
            save('failed', error=dict(type=type(error).__name__, message=str(error)))
            raise

    def get_action_batch(self, env_idx_list=None):
        tick = time.monotonic()
        try:
            result = super().get_action_batch(env_idx_list)
            status['action_calls'] += 1
            with (OUT/'action-timing.jsonl').open('a') as stream:
                stream.write(json.dumps(dict(call=status['action_calls'],
                    seconds=time.monotonic()-tick, indices=env_idx_list,
                    action_counts=[len(chunk) for chunk in result]))+'\n')
            save('executing_selected_skill')
            return result
        except Exception as error:
            save('failed', error=dict(type=type(error).__name__, message=str(error)))
            raise

    def on_trial_end(self, result=None):
        write(OUT/'trial-end.json', result)
        return super().on_trial_end(result)


async def main():
    config = yaml.safe_load((REPO/'XPolicyLab/policy/physicalRSI/deploy.yml').read_text())
    config.update(bench_name='RoboDojo', task_name='general_pickup', ckpt_name='qwen-agent-smoke',
                  env_cfg_type='arx_x5', action_type='joint', seed=0, gpu_id=0,
                  host='127.0.0.1', port=args.port)
    write(OUT/'policy-deployment.json', config)
    model = MeasuredModel(config)
    runtime = getattr(model, 'model', model)
    server = PolicyServer(model, PolicyServerConfig(host='127.0.0.1', port=args.port))
    shutdown = asyncio.Event()
    loop = asyncio.get_running_loop()
    for signum in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(signum, shutdown.set)
    try:
        await server.start()
        save('ready', preloaded_skills=list(runtime.preloaded),
             composition_names=list(runtime.catalog),
             registered_operations=len(runtime.operation_program['operations']),
             runtime_output=str(runtime.root))
        print('QWEN_AGENT_READY', flush=True)
        await shutdown.wait()
    finally:
        await server.stop()
        model.close()


try:
    asyncio.run(main())
except Exception as error:
    save('failed', error=dict(type=type(error).__name__, message=str(error)))
    raise
