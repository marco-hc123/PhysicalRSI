import json, subprocess, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent
state = dict(stage='starting', completed_jobs=[])
def save():
    state['unix'] = time.time()
    (ROOT/'suite-status.json').write_text(json.dumps(state, indent=2))
save()
for job in json.loads((ROOT/'protocol.json').read_text())['jobs']:
    state.update(stage='running', active_job=job['name']); save()
    with (ROOT/(job['name']+'-launcher.log')).open('w') as log:
        result = subprocess.run(['python3', str(ROOT/'analysis-sources/cloud_comparison_run.py'), '--suite', str(ROOT), '--job', job['name']], stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        state.update(stage='failed', exit_code=result.returncode); save(); raise SystemExit(result.returncode)
    state['completed_jobs'].append(job['name']); save()
state.update(stage='complete'); save()
