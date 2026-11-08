"""Prepare one new task smoke cohort; stop at auditable qualification milestone."""
import datetime,fcntl,json,os,subprocess,sys,traceback
from pathlib import Path
O=Path(__file__).resolve().parent
PY='/mnt/data/physical-RSI/models/skill-assets/implementations/openpi/.venv/bin/python'
lock=(O/'bootstrap.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
def save(state,**extra):
    p=O/'bootstrap-status.json';t=p.with_suffix('.tmp');t.write_text(json.dumps(dict(state=state,pid=os.getpid(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**extra),indent=2)+'\n');t.replace(p)
try:
    for name,args in [('pickup_smoke_layouts',['prepare_layouts_v3.py','general_pickup','smoke','1']),('pickup_smoke_native',['run_phase.py','general_pickup-smoke'])]:
        if name=='pickup_smoke_native':
            root=O/'layouts/general_pickup/smoke';cases=json.loads((root/'cases.json').read_text())
            plan=dict(task='general_pickup',cases=cases,layout_root=str(root),entries=[dict(name='parent',source='parents/general_pickup.py')],selection='Preparation only; excluded from development and heldout; no candidate selection',research_role='New-task interface qualification')
            (O/'general_pickup-smoke-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
        with (O/(name+'.log')).open('a') as out:
            p=subprocess.Popen([PY,'-B',str(O/args[0]),*args[1:]],cwd=O,stdout=out,stderr=subprocess.STDOUT,stdin=subprocess.PIPE)
            save(name,child_pid=p.pid,log=str(O/(name+'.log')));rc=p.wait();p.stdin.close()
        if rc:raise RuntimeError(name+' exit '+str(rc))
    save('smoke_complete_review_required',paid_requests=0)
except BaseException as e:
    save('stopped_for_diagnosis',error=str(e),traceback=traceback.format_exc(),paid_requests=0);raise
