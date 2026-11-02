"""Run the registered thinking-mode native extension after the base GPU queue."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time

root = Path('/mnt/data/physical-RSI/result')
suite = Path(json.loads((root/'CURRENT_EXPERIMENT_SUITE.json').read_text())['directory'])
amendment = json.loads((suite/'protocol-amendment-thinking-native.json').read_text())
job = amendment['additional_job']
output = suite/job['name']


def save(stage, **values):
    state = dict(stage=stage, utc=datetime.now(timezone.utc).isoformat(), job=job, **values)
    temp = suite/'extension-status.json.tmp'
    temp.write_text(json.dumps(state, indent=2)+'\n')
    temp.replace(suite/'extension-status.json')


save('waiting_for_base_suite', complete=False)
deadline = time.monotonic()+7200
while True:
    base = json.loads((suite/'controller-status.json').read_text())
    if base.get('finished'):
        assert base.get('complete'), 'Base suite requires error review before extension'
        break
    if time.monotonic() > deadline:
        raise TimeoutError('Base suite did not complete within two hours')
    time.sleep(15)

save('running_native_thinking', complete=False)
assert not output.exists(), 'Preserve existing extension attempt; review before retry'
command = [sys.executable, str(root/'cloud_suite_run.py'), '--output', str(output),
           '--route', 'agent', '--layouts', ','.join(map(str,job['layouts'])),
           '--thinking', 'true']
with (suite/(job['name']+'.launch.log')).open('w') as log:
    result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
state = json.loads((output/'status.json').read_text())
save('complete' if state.get('completed') else 'failed', complete=bool(state.get('completed')),
     exit_code=result.returncode, successes=state.get('successes'), error=state.get('error'))
