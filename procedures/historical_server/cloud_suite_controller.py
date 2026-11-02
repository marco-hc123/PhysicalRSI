"""Resume a declared suite, serializing GPU jobs and preserving failed attempts."""
import argparse
from datetime import datetime, timezone
import fcntl
import json
from pathlib import Path
import subprocess
import sys
import time

parser = argparse.ArgumentParser()
parser.add_argument('--suite', type=Path, required=True)
args = parser.parse_args()
suite = args.suite
root = Path('/mnt/data/physical-RSI/result')
lock = (suite/'controller.lock').open('a')
fcntl.lockf(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
protocol = json.loads((suite/'protocol.json').read_text())
jobs = []
for route in protocol['routes']:
    for repeat in range(1, protocol['control_repetitions'] + 1):
        name = f'control_{route}_{repeat:02d}'
        if route == 'code' and repeat == 1:
            name = 'control_code_01_retry2'
        jobs.append(dict(name=name, route=route, layouts=[protocol['control_layout']],
                         phase='control', repeat=repeat))
for route in protocol['new_layout_routes']:
    jobs.append(dict(name=f'new_layouts_{route}', route=route,
                     layouts=protocol['new_layouts'], phase='new_layouts'))

state = dict(started_utc=datetime.now(timezone.utc).isoformat(),
             planned_native_episodes=sum(len(j['layouts']) for j in jobs),
             jobs=[], complete=False)


def write():
    state['utc'] = datetime.now(timezone.utc).isoformat()
    state['completed_native_episodes'] = sum(
        len(j['layouts']) for j in state['jobs'] if j.get('complete'))
    tmp = suite/'controller-status.json.tmp'
    tmp.write_text(json.dumps(state, indent=2)+'\n')
    tmp.replace(suite/'controller-status.json')


for job in jobs:
    output = suite/job['name']
    status_path = output/'status.json'
    existing = json.loads(status_path.read_text()) if status_path.exists() else {}
    if existing.get('completed'):
        job.update(complete=True, reused=True, successes=existing['successes'])
        state['jobs'].append(job)
        write()
        continue
    if output.exists():
        # Do not overwrite or implicitly retry an interrupted evaluation.
        job.update(complete=False, error='Existing incomplete attempt requires review')
        state['jobs'].append(job)
        write()
        continue
    state['current_job'] = job
    write()
    command = [sys.executable, str(root/'cloud_suite_run.py'), '--output', str(output),
               '--route', job['route'], '--layouts', ','.join(map(str, job['layouts'])),
               '--thinking', 'false']
    with (suite/(job['name']+'.launch.log')).open('w') as log:
        process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
        while process.poll() is None:
            state['current_pid'] = process.pid
            write()
            time.sleep(10)
    status = json.loads(status_path.read_text()) if status_path.exists() else {}
    job.update(complete=bool(status.get('completed')), exit_code=process.returncode,
               successes=status.get('successes'), error=status.get('error'))
    state['jobs'].append(job)
    write()

state.pop('current_job', None)
state.pop('current_pid', None)
state['complete'] = all(j['complete'] for j in state['jobs'])
state['finished'] = True
write()
