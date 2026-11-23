"""Run approved M1 paired evaluations, gating formal runs on actual development outcomes."""
import os,sys,time,fcntl,subprocess
from pathlib import Path
from formal_queue import D,read,save,frozen_files,check
from batch_remaining_v2 import launcher
from batch_device import stable_idle,Context,assert_owned
from holding_windows import windows
PARENT=D.parent/'47_pickup_three_module_20261119'
def status(phase,**details):
    save('CONTINUATION.json',dict(goal='M1 three development and conditional twenty paired native formal episodes',phase=phase,pid=os.getpid(),server_directory=str(D),time=time.strftime('%F %T %z'),**details))
def collect(script, split, manifest, frozen):
    rows=[]
    for i,c in enumerate(manifest[split]):
        assert frozen_files()==frozen
        dest=D/'runs'/split/str(i)
        past=[p.parent for p in dest.glob('*/stage2.json') if read(p).get('status')=='passed']
        if past: run,=past
        else:
            attempt=max([int(p.name) for p in dest.glob('*')],default=0)+1
            assert_owned()
            status('native_'+split,layout=i+1,attempt=attempt,gpu=os.environ['PICKUP_BATCH_UUID'],completed=len(rows))
            with (D/f'{split}-{i+1}-{attempt}.log').open('x') as log:
                subprocess.run([sys.executable,'-B',str(script),split,str(i),str(attempt)],stdout=log,stderr=subprocess.STDOUT,check=True)
            run=dest/str(attempt)
        native=check(run,c['sha256']); result,=native['details'].values()
        actions=[read(p)['phase'] for p in run.glob('cmd-*.json') if 'action' in read(p)]
        old,=[p for p in (PARENT/'runs'/split/str(i)).glob('*/stage2.json') if read(p).get('status')=='passed']
        oldnative=check(old.parent,c['sha256']); oldrow,=oldnative['details'].values()
        stop=read(run/'policy-stop.json') if (run/'policy-stop.json').exists() else {'reason':'native_terminal' if result['success'] else 'unrecorded'}
        import json
        (run/'holding-windows.json').write_text(json.dumps(dict(windows=windows(run)),indent=2))
        rows.append(dict(layout=i+1,sha256=c['sha256'],target=read(run/'target.json')['description'],original=c['original_score'],m0=oldrow['score'],m1=result['score'],success=result['success'],close_actions=actions.count('close'),lift_actions=actions.count('lift'),stop=stop['reason'],steps=read(run/'stage2.json')['steps'],run=str(run)))
        save(split+'-paired.json',rows)
    return rows
def main():
    frozen=read(D/'preflight.json')['files'];assert frozen_files()==frozen
    manifest=read(D/'verified-case-manifest.json')
    status('waiting_for_one_idle_gpu')
    while (g:=stable_idle()) is None:time.sleep(25)
    script=launcher(g);uuid=g.findtext('uuid')
    os.environ.update(PICKUP_BATCH_OWNER=str(os.getpid()),PICKUP_BATCH_UUID=uuid)
    context=Context(uuid)
    try:
        time.sleep(2);assert_owned()
        dev=collect(script,'development',manifest,frozen)
        passed=all(r['close_actions'] and r['lift_actions'] for r in dev[:2]) and any(r['success'] for r in dev)
        save('development-gate.json',dict(passed=bool(passed),successes=sum(r['success'] for r in dev),paired=dev))
        if not passed: return 'development_gate_not_met'
        save('freeze.json',dict(files=frozen,cohort='previously analyzed layouts',development=dev))
        collect(script,'formal',manifest,frozen)
        return 'm1_formal_verified'
    finally:context.close()
if __name__=='__main__':
    with (D/'m1-batch.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        try: status(main(),gpu_context_released=True)
        except Exception as e:
            status('needs_inspection',error=repr(e));raise
