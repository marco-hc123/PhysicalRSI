"""Evaluate immutable candidates, freeze selection, qualify heldout, then evaluate."""
import datetime,fcntl,json,os,subprocess,sys,traceback
from pathlib import Path
O=Path(__file__).resolve().parent;task=sys.argv[1]
PY='/mnt/data/physical-RSI/models/skill-assets/implementations/openpi/.venv/bin/python'
lock=(O/(task+'-finish.lock')).open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
def read(p):return json.loads(p.read_text())
def save(state,**extra):
    p=O/(task+'-finish-status.json');t=p.with_suffix('.tmp');t.write_text(json.dumps(dict(state=state,task=task,pid=os.getpid(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**extra),indent=2)+'\n');t.replace(p)
def run(name,args):
    with (O/(name+'.log')).open('a') as out:
        p=subprocess.Popen([PY,'-B',str(O/args[0]),*args[1:]],cwd=O,stdout=out,stderr=subprocess.STDOUT,stdin=subprocess.PIPE);save(name,child_pid=p.pid);rc=p.wait();p.stdin.close()
    if rc:raise RuntimeError(name+' exit '+str(rc))
try:
    assert (O/(task+'-generation-complete.json')).exists()
    phase=task+'-candidates';root=O/'layouts'/task/'development'
    entries=[dict(name=r['id'],source=f"candidates/{r['id']}/candidate.py",proposal=f"candidates/{r['id']}/proposal.json") for r in read(O/(task+'-generation.json'))['requests']]
    plan=dict(task=task,cases=read(root/'cases.json'),layout_root=str(root),entries=entries,selection='No test feedback; evaluate all admitted proposals; rejected outputs kept without native zero scores',research_role='Three basic versus three actual-feedback independent proposals')
    p=O/(phase+'-plan.json');assert not p.exists();p.write_text(json.dumps(plan,indent=2)+'\n')
    run(phase,['run_phase.py',phase]);run(task+'_selection',['select_task.py',task])
    run(task+'_heldout_layouts',['prepare_layouts_v3.py',task,'heldout','5'])
    run(task+'_heldout_audit',['audit_heldout.py',task])
    selection=read(O/'selection'/f'{task}.json');root=O/'layouts'/task/'heldout';phase=task+'-heldout'
    plan=dict(task=task,cases=read(root/'cases.json'),layout_root=str(root),entries=selection['unique_entries'],selection='Locked strategies only; no tuning or reselection on heldout',research_role='Five independent fresh qualified layouts after task-specific strategy freeze')
    p=O/(phase+'-plan.json');assert not p.exists();p.write_text(json.dumps(plan,indent=2)+'\n')
    run(phase,['run_phase.py',phase]);save('completed')
except BaseException as e:
    save('stopped_for_diagnosis',error=str(e),traceback=traceback.format_exc());raise
