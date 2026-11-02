"""Run one preregistered native B job with exact process and timing evidence."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

parser=argparse.ArgumentParser()
parser.add_argument('--suite',type=Path,required=True)
parser.add_argument('--job',required=True)
args=parser.parse_args()
SUITE=args.suite
protocol=json.loads((SUITE/'protocol.json').read_text())
job=next(x for x in protocol['jobs'] if x['name']==args.job)
OUT=SUITE/job['name']
OUT.mkdir(exist_ok=False)
ROOT=Path('/mnt/data/physical-RSI')
REPO=ROOT/'code/RoboDojo'
SOURCES=SUITE/'analysis-sources'
started=time.monotonic()
state=dict(job=job,stage='initializing',complete=False,started_monotonic=started,
           started_utc=datetime.now(timezone.utc).isoformat())
server=client=None
native_run_id=SUITE.name+'--'+OUT.name


def write(path,value):
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(value,indent=2,default=str)+'\n')
    tmp.replace(path)


def save(stage,**v):
    state.update(stage=stage,elapsed_seconds=time.monotonic()-started,
                 utc=datetime.now(timezone.utc).isoformat(),**v)
    write(OUT/'status.json',state)


def terminate(process):
    if process is not None and process.poll() is None:
        os.killpg(process.pid,signal.SIGTERM)
        try:
            process.wait(timeout=25)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid,signal.SIGKILL)
            process.wait()


def sample():
    p=subprocess.run(['nvidia-smi','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True,capture_output=True)
    if p.returncode==0:
        memory,util=[int(x.strip()) for x in p.stdout.strip().split(',')]
        with (OUT/'gpu.jsonl').open('a') as f:
            f.write(json.dumps(dict(monotonic=time.monotonic(),used_MiB=memory,utilization=util))+'\n')


try:
    assert json.loads((SUITE/'preparation-status.json').read_text())['complete']
    assert json.loads((SUITE/'analysis-status.json').read_text())['complete']
    for path,expected in protocol['source_hashes'].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==expected, 'Frozen source changed: '+path
    credential=json.loads((Path.home()/'.config/physicalrsi/agent.json').read_text())
    assert credential['model']=='qwen3.7-plus'
    env=os.environ.copy()
    for key in ['PHYSICALRSI_AGENT_API_KEY','OPENAI_API_KEY','ARK_API_KEY','DASHSCOPE_API_KEY']:
        env.pop(key,None)
    env.update(PYTHONPATH=':'.join(map(str,[REPO/'XPolicyLab/policy/physicalRSI/runtime',REPO,REPO/'XPolicyLab'])),
        PYTHONUNBUFFERED='1',CUDA_VISIBLE_DEVICES='0',XLA_PYTHON_CLIENT_PREALLOCATE='false',
        OPENPI_DATA_HOME=str(ROOT/'cache/openpi'),XDG_CACHE_HOME=str(ROOT/'cache/xdg'),
        HF_HOME=str(ROOT/'cache/huggingface'),TMPDIR=str(ROOT/'cache/tmp'),
        PHYSICALRSI_LOG_GT='1' if job['ground_truth'] else '0', PHYSICALRSI_MAX_HTTP=str(3*len(job['layouts'])), PHYSICALRSI_SKILL_CONFIG=str(OUT/'skills.json'),PHYSICALRSI_EVAL_OUTPUT=str(OUT/'runtime'))
    python=ROOT/'models/skill-assets/implementations/openpi/.venv/bin/python'
    command=[str(python),'-m','PhysicalRSI_baselines.robodojo.configure_skills',
       '--assets',str(ROOT/'models/skill-assets'),'--python',str(python),
       '--output',str(OUT/'skills.json'),'--evidence',str(OUT/'code-evidence'),
       '--endpoint',credential['endpoint'],'--model',credential['model'],'--framework',str(REPO/'XPolicyLab')]
    save('configure')
    with (OUT/'configuration.log').open('w') as f:
        subprocess.run(command,cwd=REPO,env=env,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=180)
    config=json.loads((OUT/'skills.json').read_text())
    assert len(config['program_registry'])==22 and len(config['compositions'])==3
    save('loading_policy')
    with (OUT/'policy.log').open('w') as f:
        server=subprocess.Popen([str(python),str(SOURCES/'cloud_comparison_policy.py'),
            '--output',str(OUT),'--task',job['task'],'--route',job['route'],'--port','6012'],cwd=REPO,env=env,
            stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
    save('loading_policy',policy_pid=server.pid)
    deadline=time.monotonic()+1200
    while True:
        if server.poll() is not None:
            raise RuntimeError('Policy process exited during initialization; see policy.log')
        if (OUT/'policy-status.json').exists():
            p=json.loads((OUT/'policy-status.json').read_text())
            if p['state']=='ready':break
            if p['state']=='fatal':raise RuntimeError('Policy initialization failed')
        if time.monotonic()>deadline:raise TimeoutError('Policy load deadline')
        sample();time.sleep(2)
    save('policy_ready',policy_ready_monotonic=time.monotonic())
    env.update(PHYSICALRSI_STUDY_OUTPUT=str(OUT),EVAL_NUM=str(len(job['layouts'])),
        ROBODOJO_RUN_ID=native_run_id,PHYSICALRSI_EVAL_LAYOUTS=','.join(map(str,job['layouts'])))
    label='steps23-'+job['condition']+'-'+job['route']
    command=[str(ROOT/'envs/run-native-simulator.sh'),str(SOURCES/'cloud_comparison_native.py'),
        '--task_name',job['task'],'--num_envs','1','--env_cfg_type','arx_x5',
        '--device_id','0','--policy_name','physicalRSI','--port','6012','--host','127.0.0.1',
        '--additional_info',label,'--seed','0','--headless','--enable_cameras']
    write(OUT/'client-command.json',command)
    with (OUT/'client.log').open('w') as f:
        client=subprocess.Popen(command,cwd=REPO,env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
    save('running_native',client_pid=client.pid,client_started_monotonic=time.monotonic())
    deadline=time.monotonic()+3600
    while client.poll() is None:
        if server.poll() is not None:raise RuntimeError('Policy process exited during native evaluation')
        if time.monotonic()>deadline:raise TimeoutError('Native job exceeded 60-minute cap')
        sample();time.sleep(3)
    state['client_exit_code']=client.returncode
    state['native_finished_monotonic']=time.monotonic()
    results=list((REPO/'eval_result').glob(f"*/{job['task']}/physicalRSI/*/0_{label}/{native_run_id}/_result.json"))
    native=json.loads(results[0].read_text()) if len(results)==1 else None
    if native:
        assert len(results)==1
        write(OUT/'native-result.json',native)
        state['native_result_path']=str(results[0])
        video=OUT/'videos';video.mkdir()
        for p in results[0].parent.glob('*.mp4'):
            os.link(p,video/p.name)
    # A job may contain a counted planner failure: preserve it, don't silently rerun.
    events=[json.loads(l) for l in (OUT/'native-events.jsonl').read_text().splitlines()] if (OUT/'native-events.jsonl').exists() else []
    terminal=[e for e in events if e['kind'] in ['episode_end','episode_error','reset_error']]
    indices={e['episode_index'] for e in terminal}
    attempted={e['layout'] for e in events if e['kind']=='reset_start'}
    assert attempted==set(job['layouts']) and len(indices)==len(job['layouts']), 'Incomplete episode coverage'
    assert all(e['kind']!='reset_error' for e in terminal), 'Infrastructure failure during native reset'
    assert all(e['kind'] == 'episode_error' for e in terminal) or any(e['kind']=='control_ack' for e in events), 'No native control instrumentation observed'
    if job['ground_truth']:
        truth=[json.loads(l) for l in (OUT/'ground-truth.jsonl').read_text().splitlines()]
        assert not any('error' in r for r in truth), 'Ground truth observer failed'
        assert len([r for r in truth if r['phase']=='terminal']) == len(job['layouts'])
    policy_events=[json.loads(l) for l in (OUT/'policy-events.jsonl').read_text().splitlines()]
    assert any(e['kind']=='planner_binding_verified' and e['route']==job['route'] for e in policy_events)
    if job['route']!='agent':
        assert not list((OUT/'api').glob('*metadata.json')), 'Unexpected fixed-route HTTP cost'
        plans=[e['plan'] for e in policy_events if e['kind']=='fixed_route_end']
        assert len(plans)==len(job['layouts']), 'Fixed routes must execute each registered plan'
        composition={'pi05':'memory-guided-manipulation','pi05-sparse-memory':'memory-guided-visual-history','code':'memory-guided-program-library'}[job['route']]
        assert all(p['composition']==composition for p in plans)
    save('complete',complete=True,native_completed=sum(e['kind']=='episode_end' for e in terminal),
         counted_episode_errors=sum(e['kind']=='episode_error' for e in terminal),
         successes=sum(bool(e.get('success',[False])[0]) for e in terminal if e['kind']=='episode_end'))
except Exception as e:
    save('failed',error_type=type(e).__name__,error=str(e))
    raise
finally:
    terminate(client);terminate(server)
    save(state['stage'],finished_monotonic=time.monotonic())
