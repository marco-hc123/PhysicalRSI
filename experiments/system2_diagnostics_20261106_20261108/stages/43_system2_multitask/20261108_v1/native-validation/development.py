"""Sequential development baselines after new-task qualification and freeze."""
import datetime,fcntl,json,os,subprocess,sys,traceback
from pathlib import Path
O=Path(__file__).resolve().parent
PY='/mnt/data/physical-RSI/models/skill-assets/implementations/openpi/.venv/bin/python'
lock=(O/'development.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert (O/'protocol.json').exists()
def save(state,**extra):
    p=O/'development-status.json';t=p.with_suffix('.tmp');t.write_text(json.dumps(dict(state=state,pid=os.getpid(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**extra),indent=2)+'\n');t.replace(p)
def run(name,args):
    with (O/(name+'.log')).open('a') as out:
        p=subprocess.Popen([PY,'-B',str(O/args[0]),*args[1:]],cwd=O,stdout=out,stderr=subprocess.STDOUT,stdin=subprocess.PIPE)
        save(name,child_pid=p.pid);rc=p.wait();p.stdin.close()
    if rc:raise RuntimeError(name+' exit '+str(rc))
try:
    for task in ['classify_objects','general_pickup']:
        run(task+'_development_layouts',['prepare_layouts_v3.py',task,'development','5'])
        root=O/'layouts'/task/'development';cases=json.loads((root/'cases.json').read_text())
        entries=[dict(name='parent',source=f'parents/{task}.py')]
        if task=='general_pickup':entries.append(dict(name='pi05_reference',expert='pi05'))
        phase=task+'-parent'
        plan=dict(task=task,cases=cases,layout_root=str(root),entries=entries,selection='Parent development evidence; pi05 is a capacity reference, not eligible for code-candidate selection',research_role='Fixed development baselines before candidate evaluation')
        p=O/(phase+'-plan.json');assert not p.exists();p.write_text(json.dumps(plan,indent=2)+'\n')
        run(phase,['run_phase.py',phase])
    save('completed')
except BaseException as e:
    save('stopped_for_diagnosis',error=str(e),traceback=traceback.format_exc());raise
