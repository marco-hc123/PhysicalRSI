"""Preserve a planner-contract failure and evaluate each remaining layout once."""
from datetime import datetime, timezone
import fcntl
import hashlib
import json
from pathlib import Path
import subprocess
import sys

root = Path('/mnt/data/physical-RSI/result')
suite = Path(json.loads((root/'CURRENT_EXPERIMENT_SUITE.json').read_text())['directory'])
lock = (suite/'thinking-continuation.lock').open('a')
fcntl.lockf(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
original = suite/'new_layouts_agent_thinking'
policy = json.loads((original/'policy-status.json').read_text())
assert policy['error']['message'] == 'Agent operation plan contains an unknown composition'
assert policy['api_attempts'] == 5
native_path = next(Path('/mnt/data/physical-RSI/code/RoboDojo/eval_result').glob(
    '*/general_pickup/physicalRSI/*/*/new_layouts_agent_thinking/_result.json'))
native = json.loads(native_path.read_text())
assert [d['layout_id'] for d in native['details'].values()] == [1,2,3,4]
(original/'partial-native-result.json').write_text(json.dumps(native,indent=2)+'\n')
state = dict(registered_utc=datetime.now(timezone.utc).isoformat(), finished=False,
    reason='Layout5 returned unknown composition operation_program. Preserve it as an end-to-end planner failure; do not remap or retry it. Evaluate layouts6..10 once each in fresh processes so a failure cannot abort later layouts.',
    original_native_path=str(native_path), original_valid_native_layouts=[1,2,3,4],
    failed_layout=5, failure_kind='planner_contract_failure',
    failure_response_sha256=hashlib.sha256((original/'api/call-005-response.json').read_bytes()).hexdigest(),
    remaining_layouts=[6,7,8,9,10], jobs=[])


def write():
    state['utc']=datetime.now(timezone.utc).isoformat()
    temp=suite/'thinking-continuation-status.json.tmp'
    temp.write_text(json.dumps(state,indent=2)+'\n')
    temp.replace(suite/'thinking-continuation-status.json')


write()
for layout in state['remaining_layouts']:
    name=f'new_layouts_agent_thinking_layout{layout:02d}'
    output=suite/name
    assert not output.exists(), 'Do not implicitly repeat an existing attempt'
    job=dict(name=name,route='agent',thinking=True,layouts=[layout],phase='new_layouts')
    state['current_job']=job
    write()
    command=[sys.executable,str(root/'cloud_suite_run.py'),'--output',str(output),
             '--route','agent','--layouts',str(layout),'--thinking','true']
    with (suite/(name+'.launch.log')).open('w') as log:
        result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
    result_state=json.loads((output/'status.json').read_text())
    if result_state.get('completed'):
        job.update(native_complete=True,successes=result_state['successes'])
    else:
        pol=json.loads((output/'policy-status.json').read_text())
        assert (output/'observation-000.npz').exists() and pol.get('api_attempts',0)>0, 'Infrastructure failure requires review'
        job.update(native_complete=False,successes=0,error=pol.get('error'),
                   failure_kind='planner_failure' if pol.get('action_calls',0)==0 else 'execution_failure')
    job['exit_code']=result.returncode
    state['jobs'].append(job)
    write()
state.pop('current_job',None)
state['finished']=True
write()
