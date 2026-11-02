"""Serialized, locked campaign; never repeat an existing attempt directory."""
from datetime import datetime,timezone
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys

suite=Path(sys.argv[1]); sources=suite/'analysis-sources'
protocol=json.loads((suite/'protocol.json').read_text())
lock=(suite/'controller.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
state=dict(complete=False,finished=False,pid=os.getpid(),current=None,jobs=[],stage='preparing_assets',
           started_utc=datetime.now(timezone.utc).isoformat())
def save():
    state['utc']=datetime.now(timezone.utc).isoformat()
    p=suite/'controller-status.json.tmp';p.write_text(json.dumps(state,indent=2)+'\n');p.replace(suite/'controller-status.json')
    pointer=dict(directory=str(suite),**{k:v for k,v in state.items() if k!='jobs'},
                 completed_jobs=len(state['jobs']),protocol=str(suite/'protocol.json'),raw_retention='cloud_only')
    p=suite.parent/'CURRENT_STEPS23.json.tmp';p.write_text(json.dumps(pointer,indent=2)+'\n');p.replace(suite.parent/'CURRENT_STEPS23.json')
try:
    save()
    with (suite/'assets.log').open('w') as log:
        subprocess.run([sys.executable,str(sources/'steps23_assets.py'),str(suite)],stdout=log,stderr=subprocess.STDOUT,check=True,timeout=3600)
    for index,job in enumerate(protocol['jobs']):
        state.update(current=job['name'],stage='running_step'+str(job['step']));save()
        if job.get('retained'):
            assert (suite/job['name']/'retained-evidence-provenance.json').exists()
            code=0
        else:
            assert not (suite/job['name']).exists(), 'Existing attempt requires reconciliation'
            with (suite/(job['name']+'.launch.log')).open('w') as log:
                child=subprocess.run([sys.executable,str(sources/'cloud_comparison_run.py'),'--suite',str(suite),'--job',job['name']],stdout=log,stderr=subprocess.STDOUT)
            code=child.returncode
        result=json.loads((suite/job['name']/'status.json').read_text())
        state['jobs'].append(dict(job=job,exit_code=code,result=result));save()
        assert code==0 and result['complete'], 'Inspect job before any resume: '+job['name']
        if job['step']==2 and protocol['jobs'][index+1]['step']==3:
            state.update(current=None,stage='validating_step2');save()
            subprocess.run([sys.executable,str(sources/'steps23_finalize.py'),str(suite),'--step2-only'],check=True)
    state.update(current=None,stage='validating_step3');save()
    subprocess.run([sys.executable,str(sources/'steps23_finalize.py'),str(suite)],check=True)
    state.update(complete=True,finished=True,stage='complete');save()
except Exception as exc:
    state.update(finished=True,complete=False,stage='needs_review',error_type=type(exc).__name__,error=str(exc));save()
    raise
