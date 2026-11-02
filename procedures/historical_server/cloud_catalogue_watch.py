"""Stream compact, read-only native progress without repeated SSH reconnects."""
import json
from pathlib import Path
import sys
import time

suite=Path(sys.argv[1])
last=None
deadline=time.monotonic()+3*3600
while time.monotonic()<deadline:
    path=suite/'controller-status.json'
    if not path.exists():
        time.sleep(5);continue
    state=json.loads(path.read_text())
    row=dict(completed=state.get('completed_cases',0),native=state.get('native_completed',0),finished=state.get('finished'),needs_review=state.get('needs_review',False))
    row['groups']={c:dict(attempts=len(group),successes=sum(j.get('successes',0) for j in group),planner_failures=sum(j.get('outcome')=='planner_failure' for j in group))
        for c in ['projected','unprojected'] for group in [[j for j in state['jobs'] if j['condition']==c]]}
    job=state.get('current_job')
    if job:
        row['current']=job['name']
        for filename,key in [('status.json','stage'),('policy-status.json','state')]:
            current=suite/job['name']/filename
            if current.exists():
                record=json.loads(current.read_text())
                row[key]=record.get(key)
                if record.get('error'):row['error']=record['error']
    elif state['jobs']:
        row['last']={k:state['jobs'][-1].get(k) for k in ['name','outcome','successes','error']}
    signature=json.dumps(row,sort_keys=True)
    if signature!=last:
        print(json.dumps(row,ensure_ascii=False),flush=True)
        last=signature
    if row['finished'] or row['needs_review']:break
    time.sleep(5)
