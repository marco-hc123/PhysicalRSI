"""Run one native episode with Qwen choosing among the complete skill catalogue."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path('/mnt/data/physical-RSI')
REPO = ROOT/'code/RoboDojo'
OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=False)
started = time.monotonic()
state = dict(scope='One native general_pickup episode with API-selected frozen skills',
             task='general_pickup', episode=0, agent_enabled=True, completed=False)
server = client = None
samples = []


def save(stage, **values):
    state.update(stage=stage, elapsed_seconds=time.monotonic()-started,
                 utc=datetime.now(timezone.utc).isoformat(), **values)
    p=OUT/'status.json.tmp';p.write_text(json.dumps(state,indent=2)+'\n');p.replace(OUT/'status.json')


def stop(process):
    if process is not None and process.poll() is None:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()


def sample_gpu():
    result=subprocess.run(['nvidia-smi','--query-gpu=memory.used,utilization.gpu',
        '--format=csv,noheader,nounits'],capture_output=True,text=True)
    if result.returncode == 0:
        values=[int(v.strip()) for v in result.stdout.strip().split(',')]
        row=dict(seconds=time.monotonic()-started, used_MiB=values[0], utilization=values[1])
        samples.append(row)
        with (OUT/'gpu.jsonl').open('a') as file:file.write(json.dumps(row)+'\n')


try:
    save('configuring_complete_skill_library')
    (ROOT/'result/CURRENT_QWEN_EPISODE.json').write_text(json.dumps({'directory':str(OUT)}))
    credential=json.loads((Path.home()/'.config/physicalrsi/agent.json').read_text())
    env=os.environ.copy()
    for name in ['PHYSICALRSI_AGENT_API_KEY','OPENAI_API_KEY','ARK_API_KEY','DASHSCOPE_API_KEY']:
        env.pop(name,None)
    env.update(PYTHONPATH=':'.join(map(str,[REPO/'XPolicyLab/policy/physicalRSI/runtime',REPO,REPO/'XPolicyLab'])),
        XLA_PYTHON_CLIENT_PREALLOCATE='false',PYTHONUNBUFFERED='1',CUDA_VISIBLE_DEVICES='0',
        OPENPI_DATA_HOME=str(ROOT/'cache/openpi'),XDG_CACHE_HOME=str(ROOT/'cache/xdg'),
        HF_HOME=str(ROOT/'cache/huggingface'),TMPDIR=str(ROOT/'cache/tmp'),
        PHYSICALRSI_SKILL_CONFIG=str(OUT/'skills.json'),PHYSICALRSI_EVAL_OUTPUT=str(OUT/'runtime'))
    python=ROOT/'models/skill-assets/implementations/openpi/.venv/bin/python'
    command=[str(python),'-m','PhysicalRSI_baselines.robodojo.configure_skills',
        '--assets',str(ROOT/'models/skill-assets'),'--python',str(python),
        '--output',str(OUT/'skills.json'),'--evidence',str(OUT/'code-evidence'),
        '--endpoint',credential['endpoint'],'--model',credential['model'],
        '--framework',str(REPO/'XPolicyLab')]
    with (OUT/'configuration.log').open('w') as log:
        subprocess.run(command,cwd=REPO,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
    config=json.loads((OUT/'skills.json').read_text())
    assert len(config['program_registry'])==22 and len(config['compositions'])==3
    assert 'pi05' in config['skills'] and 'pi05-sparse-memory' in config['skills']
    source_paths=[REPO/'XPolicyLab/policy/physicalRSI/runtime/PhysicalRSI_baselines/robodojo/agent_planner.py',
                  ROOT/'result/cloud_qwen_agent_server.py',ROOT/'result/cloud_run_qwen_episode.py']
    (OUT/'source-hashes.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths},indent=2))
    server_command=[str(python),str(ROOT/'result/cloud_qwen_agent_server.py'),'--output',str(OUT),'--port','6012']
    with (OUT/'policy.log').open('w') as log:
        server=subprocess.Popen(server_command,cwd=REPO,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    save('loading_both_vla_skills',policy_pid=server.pid)
    deadline=time.monotonic()+1200
    while True:
        if server.poll() is not None:raise RuntimeError('Agent policy server exited during initialization')
        sample_gpu()
        if (OUT/'policy-status.json').exists():
            policy=json.loads((OUT/'policy-status.json').read_text())
            if policy['state']=='ready':break
            if policy['state']=='failed':raise RuntimeError('Agent policy initialization failed; see policy-status.json')
        if time.monotonic()>deadline:raise TimeoutError('Policy initialization timed out')
        time.sleep(3)
    label='cloud-qwen-agent-smoke'
    env.update(EVAL_NUM='1',ROBODOJO_RUN_ID=OUT.name)
    client_command=[str(ROOT/'envs/run-native-simulator.sh'),str(REPO/'src/eval_client/main.py'),
        '--task_name','general_pickup','--num_envs','1','--env_cfg_type','arx_x5',
        '--device_id','0','--policy_name','physicalRSI','--port','6012','--host','127.0.0.1',
        '--additional_info',label,'--seed','0','--headless','--enable_cameras']
    (OUT/'client-command.json').write_text(json.dumps(client_command,indent=2))
    with (OUT/'client.log').open('w') as log:
        client=subprocess.Popen(client_command,cwd=REPO,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    save('running_native_episode',client_pid=client.pid)
    deadline=time.monotonic()+1800
    while client.poll() is None:
        if server.poll() is not None:raise RuntimeError('Policy server exited during episode')
        policy=json.loads((OUT/'policy-status.json').read_text())
        if policy['state']=='failed':raise RuntimeError('Selected skill or planner failed; inspect policy-status.json')
        sample_gpu()
        if time.monotonic()>deadline:raise TimeoutError('Episode timed out after 30 minutes')
        time.sleep(3)
    results=list((REPO/'eval_result').glob(f'*/general_pickup/physicalRSI/*/0_{label}/{OUT.name}/_result.json'))
    if len(results)!=1:raise RuntimeError(f'Expected one native result; found {len(results)}')
    native=json.loads(results[0].read_text())
    (OUT/'native-result.json').write_text(json.dumps(native,indent=2)+'\n')
    details=list(native.get('details',{}).values())
    if native.get('eval_time')!=1 or len(details)!=1 or int(details[0]['layout_id'])!=0:
        raise RuntimeError('Native result is not one completed episode-zero evaluation')
    save('complete',completed=True,task_success=bool(details[0]['success']),
         native_result=native,native_result_path=str(results[0]),client_exit_code=client.returncode)
except Exception as error:
    save('failed',error=dict(type=type(error).__name__,message=str(error)))
    raise
finally:
    stop(client)
    stop(server)
    calls=[json.loads(p.read_text()) for p in sorted((OUT/'api').glob('*-metadata.json'))]
    usage={k:sum((c.get('usage') or {}).get(k,0) for c in calls) for k in ['prompt_tokens','completion_tokens','total_tokens']}
    summary=dict(api_attempts=len(calls),successful_calls=sum(c.get('success',False) for c in calls),
        provider_reported_usage=usage,api_seconds=sum(c['seconds'] for c in calls),
        sampled_gpu_peak_MiB=max((s['used_MiB'] for s in samples),default=0),
        gpu_sample_period_seconds=3,scope='Native agent episode only; excludes API preflight checks')
    (OUT/'usage-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    state['usage']=summary
    save(state['stage'])
