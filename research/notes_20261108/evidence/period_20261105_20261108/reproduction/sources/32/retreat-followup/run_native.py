"""Sequential native execution of the preregistered saved-candidate matrix.

Waits for verified resources. A failed deployment stops the campaign and stays
separate from task outcomes. Does not call any paid API or promote a candidate.
"""
import datetime
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import traceback

R=Path('/mnt/data/physical-RSI')
O=R/'result/33_retreat_recovery_20261106'
RESOURCES=R/'result/31_rgb_supplement_20261105/resource-verification'
I=R/'result/25_system2_integration_20261030T050100Z/integration-sources'
sys.path.insert(0,str(I))
sys.path.insert(0,str(I/'framework-validation-v3'))
from PhysicalRSI_core.infra.storage import atomic_json, file_digest, read_json
from PhysicalRSI_core.self_harness.artifacts import verify_harness
from PhysicalRSI_baselines.robodojo.native_runtime import NativeRuntime
from PhysicalRSI_baselines.robodojo.evidence import episode_receipt, verify_case

C=O/'native-campaign'
lock=(C/'controller.lock').open('a')
fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
campaign=read_json(C/'campaign.json')
assert campaign['planned_cases']==10 and len(campaign['entries'])==2 and len(campaign['cases'])==5
assert file_digest(Path(campaign['protocol']))==campaign['protocol_sha256']
assert file_digest(Path(campaign['runtime']))==campaign['runtime_sha256']
running=True
started=time.monotonic()

def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()

def status(state,**extra):
    value=dict(utc=utc(),pid=os.getpid(),state=state,elapsed_s=time.monotonic()-started,
               api_calls=0,paid_cost_usd=0,lab_gpu_used=False,**extra)
    atomic_json(C/'status.json',value)
    with (C/'events.jsonl').open('a') as stream:stream.write(json.dumps(value)+'\n')
    print(json.dumps(value),flush=True)

def sampler():
    while running:
        value=dict(utc=utc())
        try:
            result=subprocess.run(['nvidia-smi','--query-gpu=memory.used,utilization.gpu,temperature.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=5)
            value['gpu']=result.stdout.strip()
            value['loadavg']=Path('/proc/loadavg').read_text().strip()
            value['meminfo']={x.split(':')[0]:x.split(':')[1].strip() for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith(('MemAvailable:','MemFree:'))}
        except Exception as exc:value['sample_error']=type(exc).__name__
        with (C/'resource-samples.jsonl').open('a') as stream:stream.write(json.dumps(value)+'\n')
        time.sleep(10)

def receipts_for(entry,folder):
    paths=sorted((folder/'episodes').glob('*.json'),key=lambda p:int(p.stem))
    if len(paths)!=len(campaign['cases']):raise ValueError('Incomplete outer episode receipts')
    out=[]
    for path,case in zip(paths,campaign['cases']):
        row=episode_receipt(path,directory=folder,task=case['task'],split=case['split'],
            layout_sha256=case['layout_sha256'],expert=entry['expert'],harness_sha256=entry['harness_sha256'])
        out.append(dict(condition=entry['name'],layout=case['file'],layout_sha256=case['layout_sha256'],
            success=row['success'],score=row['episode_score'],receipt=str(path),diagnostics=row.get('diagnostics',{})))
    return out

try:
    assert os.geteuid()==0,'Recorded chroot/seccomp isolation requires a privileged trusted controller'
    status('waiting_for_verified_resources',completed_cases=0)
    tokenizer=R/'cache/openpi/big_vision/paligemma_tokenizer.model'
    while not (RESOURCES/'completion.json').exists() or not tokenizer.exists():time.sleep(20)
    assert file_digest(tokenizer)=='8986bb4f423f07f8c7f70d0dbe3526fb2316056c17bae71b1ea975e77a168fc6'
    for name,count in [('scene_assets',15369),('implementations',10691),('weights',41)]:
        report=read_json(RESOURCES/(name+'.json'))
        assert report['state']=='verified' and report['matched']==report['file_count']==count,(name,report.get('state'))
    for case in campaign['cases']:verify_case(case,campaign['layout_root'])
    runtime=NativeRuntime(read_json(campaign['runtime']))
    status('artifact_preflight',completed_cases=0)
    check=runtime.check();atomic_json(C/'runtime-preflight.json',check)
    assert check['ready'],check
    threading.Thread(target=sampler,daemon=True).start()
    outcomes=[]
    for entry in campaign['entries']:
        assert verify_harness(entry['harness'])==entry['harness_sha256']
        base=C/'runs'/entry['name'];base.mkdir(parents=True,exist_ok=True)
        completed=base/'completed.json'
        if completed.exists():
            prev=read_json(completed);outcomes+=receipts_for(entry,Path(prev['output']));continue
        previous=sorted(base.glob('attempt-*'))
        retry_path=C/'deployment-retry-authorization.json'
        exclusions=read_json(retry_path)['excluded_attempts'] if retry_path.exists() else []
        excluded={row['attempt']:row for row in exclusions if row['condition']==entry['name']}
        # Resume an unindexed completed run without executing it twice.
        valid=[]
        for folder in previous:
            if str(folder) in excluded:
                row=excluded[str(folder)]
                assert row['classification']=='invalid_deployment' and row['valid_native_cases']==0
                assert row['policy_zero_score'] is False
                assert not list((folder/'episodes').glob('*.json'))
                assert file_digest(folder/'failed.json')==row['failed_sha256']
                assert file_digest(folder/'native/run/observed.json')==row['observed_sha256']
                assert file_digest(folder/'native/processes/simulator/process.log')==row['simulator_log_sha256']
                assert file_digest(Path(row['repair']))==row['repair_sha256']
                continue
            if (folder/'episodes').exists():valid.append((folder,receipts_for(entry,folder)))
        assert len(valid)<=1,'Multiple valid executions need explicit accounting review'
        if valid:
            folder,rows=valid[0]
        else:
            unreviewed=[p for p in previous if str(p) not in excluded]
            if unreviewed:raise RuntimeError('Existing incomplete attempt requires diagnosis before rerun: '+str(base))
            number=max([int(p.name.split('-')[1]) for p in previous],default=0)+1
            folder=base/('attempt-%03d'%number)
            status('native_cohort_running',condition=entry['name'],completed_cases=len(outcomes),current_output=str(folder))
            t=time.monotonic()
            paths=runtime.rollouts(candidate=entry['harness'],expert=entry['expert'],cases=campaign['cases'],
                                   layout_root=campaign['layout_root'],output=folder)
            rows=receipts_for(entry,folder)
            atomic_json(base/'timing.json',dict(start_to_valid_receipts_s=time.monotonic()-t,scope='Policy startup, native execution, strict cleanup, final evidence verification'))
        atomic_json(completed,dict(utc=utc(),output=str(folder),cases=len(rows),harness_sha256=entry['harness_sha256']))
        outcomes+=rows
        atomic_json(C/'outcomes.json',dict(rows=outcomes,valid_native_cases=len(outcomes),api_calls=0,diagnostic_layout_reuse=True))
        status('cohort_completed',condition=entry['name'],completed_cases=len(outcomes),successes=sum(x['success'] for x in rows),mean_score=sum(x['score'] for x in rows)/len(rows))
    status('diagnostic_matrix_completed',completed_cases=len(outcomes),selection='pi05 retained; diagnostic comparison only')
except BaseException as exc:
    atomic_json(C/'controller-failure.json',dict(utc=utc(),error=type(exc).__name__+': '+str(exc),traceback=traceback.format_exc(),policy_zero_score=False))
    status('stopped_for_diagnosis',error=type(exc).__name__+': '+str(exc),policy_zero_score=False)
    raise
finally:
    running=False
