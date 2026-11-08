import datetime,fcntl,json,os,subprocess,time,traceback
from pathlib import Path
O=Path(__file__).resolve().parent
def status(state,**x):
    p=O/'analysis-status.json';v=dict(state=state,pid=os.getpid(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**x);p.write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v),flush=True)
lock=(O/'analysis.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
try:
    status('waiting_for_native_validation');deadline=time.monotonic()+5400
    while True:
        d=json.loads((O/'route-status.json').read_text())
        if d['state']=='requires_diagnosis':raise RuntimeError('Native route needs diagnosis; no automatic repeat')
        if d['state']=='native_and_validation_completed':break
        if time.monotonic()>deadline:raise TimeoutError('Native route not complete; no process terminated')
        time.sleep(15)
    status('analyzing_chain')
    with (O/'analyze_chain.stdout.log').open('w') as out,(O/'analyze_chain.stderr.log').open('w') as err:
        p=subprocess.run(['/mnt/data/physical-RSI/envs/simulator/bin/python','-B',str(O/'analyze_chain.py')],cwd=O,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'),stdout=out,stderr=err,timeout=300)
    assert p.returncode==0,'Analysis failed; inspect saved stderr; native results unchanged'
    status('ready_for_visual_review_and_archive',native_cases=10,api_calls=0)
except BaseException as e:status('requires_diagnosis',error=repr(e),traceback=traceback.format_exc());raise
