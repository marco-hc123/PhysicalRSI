"""One actual step-4 integration iteration; cloud-only evidence, no HTTP retries."""
from pathlib import Path
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
import sys
import time
import traceback
import urllib.request

R = Path('/mnt/data/physical-RSI')
O = R / 'result/25_system2_integration_20261030T050100Z/attempt-03'
configuration = json.loads((O / 'runtime.json').read_text())
os.environ.update(configuration['policy_environment'])
sys.path[:0] = configuration['policy_environment']['PYTHONPATH'].split(':')
from PhysicalRSI_core.infra.storage import atomic_json, file_digest
from PhysicalRSI_core.infra.language import LanguageModel, ModelConfig
from PhysicalRSI_baselines.robodojo.native_runtime import NativeRuntime
from PhysicalRSI_baselines.robodojo.proposal import CodeProposer
from PhysicalRSI_baselines.robodojo.workflow import RoboDojoTask

lock = (O / 'controller.lock').open('a')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
assert not (O / 'iteration-started.json').exists(), 'Inspect existing iteration before any resume'
assert os.geteuid() == 0, 'Actual isolated code execution requires root supervisor'

def stamp():
    return datetime.now(timezone.utc).isoformat()

def status(stage, **extra):
    row = dict(stage=stage, pid=os.getpid(), utc=stamp(), complete=False, **extra)
    atomic_json(O / 'controller-status.json', row)
    atomic_json(R / 'result/CURRENT_STEP4.json', dict(directory=str(O), **row))
    print(json.dumps(row), flush=True)

private = json.loads(Path('/home/ecs-user/.config/physicalrsi/agent.json').read_text())
assert private['model'] == 'qwen3.7-plus'
endpoint = private['endpoint']
assert endpoint.endswith('/chat/completions')
profile = dict(model=private['model'], temperature=0, enable_thinking=True,
               response_format={'type': 'json_object'},
               unspecified=['max_tokens', 'max_completion_tokens', 'top_p', 'stream'],
               automatic_retries=0, timeout_s=600)
atomic_json(O / 'proposal-transport-profile.json', profile)

class PinnedConfig:
    def __init__(self):
        self.base = ModelConfig(model=private['model'], base_url=endpoint[:-len('/chat/completions')], timeout_s=600)
    def __getattr__(self, key):
        return getattr(self.base, key)
    def public(self):
        value = self.base.public()
        value.pop('max_output_tokens')
        value['actual_transport_profile'] = profile
        value['controller_sha256'] = file_digest(Path(__file__))
        return value

def transport(suffix, body):
    assert suffix == '/chat/completions'
    request_body = dict(body)
    request_body.pop('max_completion_tokens', None)
    request_body.pop('tools', None)
    request_body.update(temperature=0, enable_thinking=True, response_format={'type': 'json_object'})
    calls = O / 'proposal-api'
    calls.mkdir(exist_ok=True)
    number = len(list(calls.glob('call-*'))) + 1
    directory = calls / ('call-%04d' % number)
    directory.mkdir()
    atomic_json(directory / 'request.json', request_body)
    atomic_json(directory / 'started.json', dict(utc=stamp(), model=private['model'], retry=False))
    status('calling_code_proposal_api', call=number)
    start = time.monotonic()
    request = urllib.request.Request(endpoint, data=json.dumps(request_body).encode(), method='POST',
        headers={'Authorization': 'Bearer ' + private['api_key'], 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(request, timeout=600) as response:
            raw = response.read()
            result = json.loads(raw)
        atomic_json(directory / 'response.json', result)
        atomic_json(directory / 'completed.json', dict(utc=stamp(), elapsed_s=time.monotonic()-start,
            usage=result.get('usage'), finish_reason=result['choices'][0]['finish_reason'], http_attempts=1))
        status('code_proposal_api_completed', call=number, usage=result.get('usage'))
        return result
    except BaseException as error:
        # Never log request headers, URL errors or exception repr containing credentials.
        atomic_json(directory / 'failed.json', dict(utc=stamp(), elapsed_s=time.monotonic()-start,
            error_type=type(error).__name__, retry=False, usage_unknown=True))
        raise RuntimeError('Code proposal API failed; uncertain call is preserved and will not be retried') from None

status('verifying_runtime_before_one_iteration')
runtime = NativeRuntime(configuration)
task = RoboDojoTask(json.loads((O/'workflow-configuration.json').read_text()), O/'workspace',
    runtime, CodeProposer(LanguageModel(PinnedConfig(), transport=transport)), rsi_plan={'scheme': 'hybrid'})
atomic_json(O/'iteration-started.json', dict(utc=stamp(), pid=os.getpid(),
    workspace=str(O/'workspace'), max_iterations=1, development_episodes=1, validation_episodes=1,
    scope='Actual native integration smoke; not formal step5 or performance proof',
    controller_sha256=file_digest(Path(__file__))))
try:
    status('one_native_iteration_running')
    result = task.evolve()
    atomic_json(O/'iteration-result.json', dict(utc=stamp(), result=result, task_status=task.status(),
        qualification='Requires audit of actual native evidence; no improvement claim from 1+1 episodes'))
    status('one_native_iteration_finished', result=result)
except BaseException as error:
    atomic_json(O/'iteration-failed.json', dict(utc=stamp(), type=type(error).__name__,
        message=str(error), traceback=traceback.format_exc(), automatic_retry=False))
    status('one_native_iteration_failed', error_type=type(error).__name__, error=str(error))
    raise
