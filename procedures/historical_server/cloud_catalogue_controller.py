"""Run the frozen paired cloud study once, reconciling every native outcome."""
import argparse
from datetime import datetime, timezone
import fcntl
import json
from pathlib import Path
import subprocess
import sys
import time
from cloud_catalogue_common import verify_source_pins, write_json

parser = argparse.ArgumentParser()
parser.add_argument('--suite', type=Path, required=True)
args = parser.parse_args()
suite = args.suite
root = Path('/mnt/data/physical-RSI/result')
lock = (suite/'controller.lock').open('a')
fcntl.lockf(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
verify_source_pins(suite)
protocol = json.loads((suite/'protocol.json').read_text())
replay = json.loads((suite/'replay/replay-summary.json').read_text())
assert replay['finished'] and replay['source_pin_verified']
assert len(replay['rows']) == 10 and all(p['input_identical_verified'] for p in replay['pair_audits'])
assert not (suite/'controller-status.json').exists(), 'Reconcile prior controller before resuming'
state = dict(started_utc=datetime.now(timezone.utc).isoformat(),finished=False,jobs=[],planned_cases=len(protocol['jobs']))


def write():
    state['utc'] = datetime.now(timezone.utc).isoformat()
    state['completed_cases'] = len(state['jobs'])
    state['native_completed'] = sum(j['native_complete'] for j in state['jobs'])
    write_json(suite/'controller-status.json',state)


write()
for registered in protocol['jobs']:
    verify_source_pins(suite)
    job = dict(registered)
    output = suite/job['name']
    assert not output.exists(), 'Never repeat an existing or interrupted evaluation'
    state['current_job'] = job
    write()
    command = [sys.executable,str(root/'cloud_catalogue_run.py'),'--output',str(output),
               '--route','agent','--layouts',str(job['layout']),'--thinking','true','--catalogue',job['condition']]
    with (suite/(job['name']+'.launch.log')).open('w') as log:
        process = subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
        state['current_pid'] = process.pid
        write()
        while process.poll() is None:
            time.sleep(5)
            write()
    result = json.loads((output/'status.json').read_text()) if (output/'status.json').exists() else {}
    policy = json.loads((output/'policy-status.json').read_text()) if (output/'policy-status.json').exists() else {}
    usage = json.loads((output/'usage-summary.json').read_text()) if (output/'usage-summary.json').exists() else {}
    native_complete = bool(result.get('completed')) and result.get('client_exit_code') == 0
    if native_complete:
        outcome = 'native_completed'
    elif (output/'observation-000.npz').exists() and usage.get('api_attempts',0)>0:
        validation = json.loads((output/'planner-validation.json').read_text()) if (output/'planner-validation.json').exists() else {}
        outcome = 'planner_failure' if not validation.get('contract_valid') else 'execution_failure'
    else:
        outcome = 'infrastructure_failure'
    job.update(native_complete=native_complete,outcome=outcome,exit_code=process.returncode,
               successes=result.get('successes',0) if native_complete else 0,
               error=policy.get('error') or result.get('error'))
    state['jobs'].append(job)
    state.pop('current_pid',None)
    state.pop('current_job',None)
    write()
    print('CASE',len(state['jobs']),job['name'],outcome,'successes='+str(job['successes']),flush=True)
    if outcome == 'infrastructure_failure':
        state['needs_review'] = True
        write()
        raise RuntimeError('Infrastructure failure requires evidence review before dispatching more cases')
    if len(state['jobs']) == 10:
        review = dict(utc=datetime.now(timezone.utc).isoformat(),cases=10,
                      native_completed=state['native_completed'],source_pin_verified=verify_source_pins(suite),
                      input_pair_audits_verified=True,
                      infrastructure_failures=0,
                      decision='Continue the two preregistered repeats; keep every planning/execution failure in denominator',
                      outcomes=[{k:j[k] for k in ('name','condition','layout','successes','outcome')} for j in state['jobs']])
        write_json(suite/'pilot-review.json',review)
state['finished'] = True
state['complete'] = len(state['jobs']) == len(protocol['jobs'])
write()
print('ALL_CATALOGUE_CASES_FINISHED',len(state['jobs']),flush=True)
