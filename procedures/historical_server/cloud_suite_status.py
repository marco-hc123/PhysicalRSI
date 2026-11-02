"""Print bounded live progress including finished layouts within a running batch."""
import json
from pathlib import Path
import subprocess

root = Path('/mnt/data/physical-RSI/result')
suite = Path(json.loads((root/'CURRENT_EXPERIMENT_SUITE.json').read_text())['directory'])
controller = json.loads((suite/'controller-status.json').read_text())
rows = []
for directory in sorted(suite.iterdir()):
    p = directory/'status.json'
    if not p.is_file() or directory.name in ('api-modes', 'layout-assets'):
        continue
    state = json.loads(p.read_text())
    if not state.get('route'):
        continue
    if state.get('completed'):
        rows.append(dict(name=directory.name, route=state['route'],
                         episodes=state['native_result']['eval_time'],
                         successes=state['successes'], complete=True))
current = controller.get('current_job', {})
extension_file = suite/'extension-status.json'
if controller.get('finished') and extension_file.exists():
    extension = json.loads(extension_file.read_text())
    if not extension.get('complete'):
        current = extension['job'].copy()
        current['extension_stage'] = extension['stage']
directory = suite/current.get('name', 'missing')
for name in ('status.json', 'policy-status.json'):
    if (directory/name).exists():
        state = json.loads((directory/name).read_text())
        current[name] = {k: state[k] for k in ('stage', 'state', 'action_calls',
                        'observation_calls', 'api_attempts', 'error') if k in state}
native = Path('/mnt/data/physical-RSI/code/RoboDojo/eval_result')
partial = list(native.glob(f'*/general_pickup/physicalRSI/*/*/{directory.name}/_result.json'))
if partial:
    current['native_partial'] = json.loads(partial[0].read_text())
gpu = subprocess.run(['nvidia-smi', '--query-gpu=memory.used,utilization.gpu',
                      '--format=csv,noheader'], capture_output=True, text=True).stdout.strip()
print(json.dumps(dict(completed=rows, current=current, gpu=gpu,
                     controller_finished=controller.get('finished', False),
                     controller_complete=controller.get('complete', False)), ensure_ascii=False))
