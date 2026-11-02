"""Prepare and replay identical native observations with projection on/off."""
import argparse
import base64
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import time
import types
from unittest.mock import patch
import urllib.request
import urllib.error

import numpy as np
from PIL import Image
from cloud_catalogue_common import sha256, verify_source_pins, write_json

parser = argparse.ArgumentParser()
parser.add_argument('--suite', type=Path, required=True)
parser.add_argument('--prepare-only', action='store_true')
args = parser.parse_args()
suite = args.suite
verify_source_pins(suite)
protocol = json.loads((suite/'protocol.json').read_text())
root = Path('/mnt/data/physical-RSI')
prior = root/'result/18_experiment_suite_20261029T020602Z/new_layouts_agent'
out = suite/'replay'
out.mkdir(exist_ok=True)
credentials = json.loads((Path.home()/'.config/physicalrsi/agent.json').read_text())
assert credentials['model'] == protocol['model'] == 'qwen3.7-plus'


def safe(value):
    if isinstance(value, str): return value.replace(credentials['api_key'], '[REDACTED]')
    if isinstance(value, dict): return {k: safe(v) for k,v in value.items()}
    if isinstance(value, list): return [safe(v) for v in value]
    return value


def write(path, value):
    write_json(path, safe(value))


import PhysicalRSI_baselines.robodojo.agent_planner as planner
import PhysicalRSI_baselines.robodojo.skill_model as skill_model
assert sha256(planner.__file__) == protocol['planner_sha256']
os.environ['PHYSICALRSI_SKILL_CONFIG'] = str(prior/'skills.json')
os.environ['PHYSICALRSI_EVAL_OUTPUT'] = str(suite/'preparation-runtime')
os.environ['PHYSICALRSI_AGENT_API_KEY'] = credentials['api_key']


class PreparationSkill:
    def close(self): pass


# Use the exact frozen model constructor for catalogues/memory. Checkpoint loading
# is stubbed only in this API-only preparation; no robot action is represented.
with patch.object(skill_model, 'load_skill', return_value=PreparationSkill()):
    model = skill_model.Model({'task_name':'general_pickup', 'seed':0})
catalogue = deepcopy(model.catalog)
program = deepcopy(model.operation_program)
model.close()
assert len(catalogue) == 3 and len(program['operations']) == 22
original_projection = planner._planner_catalogue
original_urlopen = urllib.request.urlopen
rows, pair_audits, inputs = [], [], {}


def get_input(layout):
    old = json.loads((prior/'api'/f'call-{layout:03d}-request.json').read_text())
    context = json.loads(old['messages'][1]['content'][0]['text'])
    observation = deepcopy(context['observation'])
    images = [p for m in old['messages'] if isinstance(m['content'], list)
              for p in m['content'] if p['type'] == 'image_url']
    for camera in observation['vision'].values():
        part = images[camera['color']['image_index']]
        image_path = prior/'api'/part['image_url']['artifact']
        assert sha256(image_path) == part['image_url']['sha256']
        camera['color'] = np.asarray(Image.open(image_path).convert('RGB')).copy()
    for key,value in observation['state'].items():
        observation['state'][key] = np.asarray(value)
    kwargs = dict(instruction=context['instruction'], observation=observation,
                  memory=context['task_specific_policy_memory'], previous_plan=context['previous_plan'],
                  compositions=deepcopy(catalogue), operation_program=deepcopy(program))
    return kwargs, old


def capture(kwargs, condition, response=None):
    recorded = []
    dummy = dict(composition='memory-guided-manipulation', operations=[], rationale='Offline request capture only.')
    raw = response if response is not None else json.dumps({'choices':[{'message':{'content':json.dumps(dummy)}}]}).encode()
    def transport(request, **unused):
        recorded.append(json.loads(request.data))
        return io.BytesIO(raw)
    instance = planner.AgentPlanner.__new__(planner.AgentPlanner)
    instance.api_key, instance.endpoint, instance.model = 'offline-no-secret', 'https://invalid.example', protocol['model']
    replacement = original_projection if condition == 'projected' else deepcopy
    error, plan = None, None
    with patch.object(planner, '_planner_catalogue', replacement), patch.object(
        planner, 'urllib', types.SimpleNamespace(request=types.SimpleNamespace(Request=urllib.request.Request,urlopen=transport),error=urllib.error)):
        try: plan = instance.plan(**kwargs)
        except Exception as exc: error = dict(type=type(exc).__name__, message=str(exc))
    assert len(recorded) == 1
    body = recorded[0]
    body['enable_thinking'] = True
    return body, plan, error


def portable_request(body, directory, stem):
    portable = deepcopy(body)
    number = 0
    for message in portable['messages']:
        if not isinstance(message['content'], list): continue
        for part in message['content']:
            if part['type'] != 'image_url': continue
            data = base64.b64decode(part['image_url']['url'].split(',',1)[1], validate=True)
            name = f'{stem}-image-{number}.png'; number += 1
            destination = directory/name
            if destination.exists(): assert destination.read_bytes() == data
            else: destination.write_bytes(data)
            part['image_url'] = dict(artifact=name, sha256=hashlib.sha256(data).hexdigest())
    return portable


for layout in protocol['layouts']:
    kwargs, old = get_input(layout)
    inputs[layout] = kwargs
    bodies = {condition: capture(kwargs, condition)[0] for condition in protocol['conditions']}
    contexts = {condition: json.loads(body['messages'][1]['content'][0]['text']) for condition,body in bodies.items()}
    a,b = contexts['projected'],contexts['unprojected']
    changed = sorted(k for k in a if a[k] != b[k])
    assert changed == ['available_compositions','operation_program'], changed
    residual = []
    for condition in protocol['conditions']:
        body = deepcopy(bodies[condition]); context = deepcopy(contexts[condition])
        for key in changed: context.pop(key)
        body['messages'][1]['content'][0]['text'] = json.dumps(context,sort_keys=True)
        residual.append(body)
        write(out/f'layout-{layout:02d}-{condition}-request.json',portable_request(bodies[condition],out,f'layout-{layout:02d}'))
    assert residual[0] == residual[1], 'Difference outside catalogue treatment'
    old_body = deepcopy(old)
    for message in old_body['messages']:
        if not isinstance(message['content'], list): continue
        for part in message['content']:
            if part['type'] == 'image_url':
                data = (prior/'api'/part['image_url']['artifact']).read_bytes()
                part['image_url'] = {'url':'data:image/png;base64,'+base64.b64encode(data).decode()}
    old_body['enable_thinking'] = True
    assert old_body == bodies['projected'], 'Reconstructed projected prompt differs from original native prompt'
    pair_audits.append(dict(layout=layout,input_identical_verified=True,prior_projected_request_identical=True,
        changed_context_fields=changed, common_input_sha256=hashlib.sha256(json.dumps(residual[0],sort_keys=True).encode()).hexdigest(),
        request_bytes={condition:len(json.dumps(body).encode()) for condition,body in bodies.items()}))

state = dict(finished=False,prepared=True,source_pin_verified=True,pair_audits=pair_audits,rows=rows,
             scope='Identical recorded native RGB replay; does not execute robots')
write(out/'preflight.json',state)
print('REPLAY_PREFLIGHT_VERIFIED',len(pair_audits),'identical-observation pairs',flush=True)
if args.prepare_only:
    sys.exit(0)
assert not (out/'replay-summary.json').exists(), 'Existing replay requires reconciliation, never repeat implicitly'
for index,layout in enumerate(protocol['layouts']):
    order = protocol['conditions'] if index % 2 == 0 else list(reversed(protocol['conditions']))
    for condition in order:
        stem = f'layout-{layout:02d}-{condition}'
        assert not (out/(stem+'-metadata.json')).exists() and not (out/(stem+'-dispatch.json')).exists(), 'Do not repeat existing or interrupted dispatched replay'
        body = capture(inputs[layout],condition)[0]
        row = dict(layout=layout,condition=condition,robot_executed=False,contract_valid=False,
                   started_utc=datetime.now(timezone.utc).isoformat(),attempts=[],request_sha256=hashlib.sha256(json.dumps(body).encode()).hexdigest())
        write(out/(stem+'-dispatch.json'),dict(dispatched=True,**row))
        tick = time.monotonic()
        # Preserve the frozen planner's maximum three transport attempts; semantic
        # failures are validated afterward and never repaired or retried.
        raw = None
        parsed = None
        response_error = None
        for attempt in range(1,4):
            ledger = dict(attempt=attempt,http_success=False,started_utc=datetime.now(timezone.utc).isoformat())
            attempt_tick = time.monotonic()
            try:
                request = urllib.request.Request(credentials['endpoint'],data=json.dumps(body).encode(),
                    headers={'Authorization':'Bearer '+credentials['api_key'],'Content-Type':'application/json'})
                with original_urlopen(request,timeout=300) as response:
                    raw = response.read(); ledger['http_status'] = response.status
                (out/(stem+f'-attempt-{attempt:02d}-raw-response.txt')).write_text(safe(raw.decode('utf-8', errors='replace')))
                ledger['raw_response_sha256'] = hashlib.sha256(raw).hexdigest()
                parsed = json.loads(raw)
                ledger.update(http_success=True,usage=parsed.get('usage'),returned_model=parsed.get('model'))
                write(out/(stem+f'-attempt-{attempt:02d}-response.json'),parsed)
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                ledger.update(http_success=True,envelope_valid=False,error_type=type(exc).__name__,error=str(exc))
                response_error = dict(type=type(exc).__name__,message=str(exc))
            except urllib.error.HTTPError as exc:
                ledger.update(error_type=type(exc).__name__,http_status=exc.code,error=exc.read().decode(errors='replace')[:2000])
            except (urllib.error.URLError,TimeoutError,ConnectionError,OSError) as exc:
                ledger.update(error_type=type(exc).__name__,error=str(exc))
            finally:
                ledger['seconds'] = time.monotonic()-attempt_tick
                row['attempts'].append(ledger)
                write(out/(stem+f'-attempt-{attempt:02d}-metadata.json'),ledger)
            if ledger['http_success']: break
            raw = None
            if attempt < 3: time.sleep(0.5*attempt)
        if response_error is not None:
            row.update(error=response_error,usage=None)
        elif raw is not None:
            _,plan,error = capture(inputs[layout],condition,raw)
            row.update(contract_valid=error is None,plan=plan,error=error,usage=parsed.get('usage'))
        else:
            row['error'] = dict(type='transport_failure',message='Three transport attempts exhausted')
        row['seconds'] = time.monotonic()-tick
        write(out/(stem+'-metadata.json'),row)
        rows.append(row); state.update(rows=rows,completed=len(rows),finished=len(rows)==2*len(protocol['layouts']))
        write(out/'replay-summary.json',state)
        print('REPLAY',layout,condition,'valid='+str(row['contract_valid']),'tokens='+str((row.get('usage') or {}).get('total_tokens')),flush=True)
