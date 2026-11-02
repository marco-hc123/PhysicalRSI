"""Read a compact progress snapshot; optional bounded wait never changes jobs."""
import argparse
import json
from pathlib import Path
import time

parser=argparse.ArgumentParser()
parser.add_argument('--suite',type=Path,required=True)
parser.add_argument('--wait-seconds',type=int,default=0)
args=parser.parse_args()
assert 0 <= args.wait_seconds <= 45
suite=args.suite
baseline=None
end=time.monotonic()+args.wait_seconds


def snapshot():
    result={}
    replay=suite/'replay/replay-summary.json'
    if replay.exists():
        d=json.loads(replay.read_text())
        result['replay']=dict(completed=d.get('completed',0),finished=d['finished'],
            conditions={c:dict(calls=len(rows),valid=sum(r['contract_valid'] for r in rows),
                input_tokens=sum((r.get('usage') or {}).get('prompt_tokens',0) for r in rows),
                total_tokens=sum((r.get('usage') or {}).get('total_tokens',0) for r in rows))
                for c in ['projected','unprojected']
                for rows in [[r for r in d['rows'] if r['condition']==c]]})
    controller=suite/'controller-status.json'
    if controller.exists():
        d=json.loads(controller.read_text())
        result['controller']={k:d.get(k) for k in ['finished','complete','completed_cases','native_completed','current_job','needs_review']}
        result['native_conditions']={c:dict(cases=len(rows),successes=sum(r['successes'] for r in rows),
            planner_failures=sum(r['outcome']=='planner_failure' for r in rows))
            for c in ['projected','unprojected']
            for rows in [[r for r in d['jobs'] if r['condition']==c]]}
        if d.get('current_job'):
            current=suite/d['current_job']['name']
            for file in ['status.json','policy-status.json']:
                path=current/file
                if path.exists():
                    row=json.loads(path.read_text())
                    result[file]={k:row.get(k) for k in ['stage','state','api_attempts','action_calls','error']}
    for log in ['replay.launch.log','controller.launch.log','report.launch.log']:
        p=suite/log
        if p.exists() and 'Traceback' in p.read_text():
            result[log]='\n'.join(p.read_text().splitlines()[-6:])
    return result


while True:
    result=snapshot()
    comparable=json.loads(json.dumps(result))
    if 'policy-status.json' in comparable: comparable['policy-status.json'].pop('action_calls',None)
    signature=json.dumps(comparable,sort_keys=True)
    if baseline is None: baseline=signature
    if signature != baseline or time.monotonic() >= end: break
    time.sleep(2)
print(json.dumps(result,ensure_ascii=False))
