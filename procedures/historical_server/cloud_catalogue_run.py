"""Run one declared catalogue-ablation case with frozen skills and strict planning."""
from datetime import datetime, timezone
import hashlib
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path('/mnt/data/physical-RSI')
REPO = ROOT/'code/RoboDojo'
parser=argparse.ArgumentParser()
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--route',choices=['pi05','pi05-sparse-memory','code','agent'],required=True)
parser.add_argument('--layouts',default='0')
parser.add_argument('--thinking',choices=['true','false'],default='true')
parser.add_argument('--catalogue',choices=['projected','unprojected'],required=True)
args=parser.parse_args()
LAYOUTS=[int(x) for x in args.layouts.split(',')]
OUT=args.output
OUT.mkdir(parents=True, exist_ok=False)
from cloud_catalogue_common import verify_source_pins
verify_source_pins(OUT.parent)
assert args.route == 'agent' and args.thinking == 'true' and len(LAYOUTS) == 1
started = time.monotonic()
state = dict(scope='Preregistered native general_pickup evaluation with fixed or API-selected frozen skills',
             task='general_pickup', condition=args.catalogue, layouts=LAYOUTS, route=args.route, thinking=args.thinking, agent_enabled=args.route=='agent', completed=False)
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
    save('configuring_complete_skill_library', started_unix=time.time())
    (ROOT/'result/CURRENT_CATALOGUE_RUN.json').write_text(json.dumps({'directory':str(OUT)}))
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
    prior_directory=ROOT/'result/18_experiment_suite_20261029T020602Z/new_layouts_agent'
    prior_config=json.loads((prior_directory/'skills.json').read_text())
    def normalize(value, directory):
        if isinstance(value,str): return value.replace(str(directory),'$RUN')
        if isinstance(value,dict): return {k:normalize(v,directory) for k,v in value.items()}
        if isinstance(value,list): return [normalize(v,directory) for v in value]
        return value
    assert normalize(config,OUT)==normalize(prior_config,prior_directory), 'Skill configuration changed beyond output evidence paths'
    (OUT/'skill-config-equivalence.json').write_text(json.dumps(dict(verified=True, scope='Exact config equality after replacing only run output directory', reference=str(prior_directory/'skills.json')),indent=2))
    assert len(config['program_registry'])==22 and len(config['compositions'])==3
    assert 'pi05' in config['skills'] and 'pi05-sparse-memory' in config['skills']
    source_paths=[REPO/'XPolicyLab/policy/physicalRSI/runtime/PhysicalRSI_baselines/robodojo/agent_planner.py',
                  ROOT/'result/cloud_catalogue_policy.py',ROOT/'result/cloud_catalogue_run.py',ROOT/'result/cloud_catalogue_common.py',ROOT/'result/cloud_native_subset.py']
    (OUT/'sources').mkdir(exist_ok=True)
    for source in source_paths:
        (OUT/'sources'/source.name).write_bytes(source.read_bytes())
    (OUT/'source-hashes.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths},indent=2))
    server_command=[str(python),str(ROOT/'result/cloud_catalogue_policy.py'),'--output',str(OUT),'--port','6012','--route',args.route,'--thinking',args.thinking,'--catalogue',args.catalogue]
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
    save('policy_ready', policy_ready_seconds=time.monotonic()-started)
    label='catalogue-'+args.catalogue
    env.update(EVAL_NUM=str(len(LAYOUTS)),ROBODOJO_RUN_ID=OUT.name,PHYSICALRSI_EVAL_LAYOUTS=args.layouts)
    client_command=[str(ROOT/'envs/run-native-simulator.sh'),str(ROOT/'result/cloud_native_subset.py'),
        '--task_name','general_pickup','--num_envs','1','--env_cfg_type','arx_x5',
        '--device_id','0','--policy_name','physicalRSI','--port','6012','--host','127.0.0.1',
        '--additional_info',label,'--seed','0','--headless','--enable_cameras']
    (OUT/'client-command.json').write_text(json.dumps(client_command,indent=2))
    with (OUT/'client.log').open('w') as log:
        client=subprocess.Popen(client_command,cwd=REPO,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    save('running_native_episode',client_pid=client.pid,client_started_seconds=time.monotonic()-started)
    deadline=time.monotonic()+3600
    while client.poll() is None:
        if server.poll() is not None:raise RuntimeError('Policy server exited during episode')
        policy=json.loads((OUT/'policy-status.json').read_text())
        if policy.get('first_observation_monotonic') and 'first_native_observation_seconds' not in state:
            state['first_native_observation_seconds']=policy['first_observation_monotonic']-started
        if policy['state']=='failed':raise RuntimeError('Selected skill or planner failed; inspect policy-status.json')
        sample_gpu()
        if time.monotonic()>deadline:raise TimeoutError('Native layout batch timed out after 60 minutes')
        time.sleep(3)
    results=list((REPO/'eval_result').glob(f'*/general_pickup/physicalRSI/*/0_{label}/{OUT.name}/_result.json'))
    if len(results)!=1:raise RuntimeError(f'Expected one native result; found {len(results)}')
    native=json.loads(results[0].read_text())
    (OUT/'native-result.json').write_text(json.dumps(native,indent=2)+'\n')
    details=list(native.get('details',{}).values())
    if native.get('eval_time')!=len(LAYOUTS) or sorted(int(d['layout_id']) for d in details)!=sorted(LAYOUTS):
        raise RuntimeError('Native result does not exactly cover the preregistered layouts')
    save('complete',completed=True,native_finished_seconds=time.monotonic()-started,successes=sum(bool(d['success']) for d in details),
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
        gpu_sample_period_seconds=3,scope='Selected native evaluation only')
    (OUT/'usage-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    state['usage']=summary
    save(state['stage'])
