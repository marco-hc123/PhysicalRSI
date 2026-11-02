"""Run one fixed-skill native episode once its verified checkpoint is installed."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import subprocess
import time

ROOT = Path('/mnt/data/physical-RSI')
REPO = ROOT / 'code/RoboDojo'
parser = argparse.ArgumentParser()
parser.add_argument('--skill', choices=['pi05', 'pi05-sparse-memory'], required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
OUT = args.output
OUT.mkdir(parents=True, exist_ok=True)
started = time.monotonic()
status = dict(scope='One native episode with a fixed pretrained skill, not an agent-selected episode',
              skill=args.skill, task='general_pickup', episode=0, api_calls=0,
              agent_enabled=False, native_result=None, completed=False)
server = None
client = None


def save(stage, **data):
    status.update(stage=stage, **data, elapsed_seconds=time.monotonic()-started,
                  utc=datetime.now(timezone.utc).isoformat())
    temp = OUT / 'status.json.tmp'
    temp.write_text(json.dumps(status, indent=2)+'\n')
    temp.replace(OUT / 'status.json')


def stop(process):
    if process is not None and process.poll() is None:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()


try:
    save('waiting_for_verified_checkpoint')
    checkpoint = ROOT / 'models/skill-assets/checkpoints' / args.skill
    deadline = time.monotonic()+7200
    while not (checkpoint / 'params').exists():
        if time.monotonic()>deadline:
            raise TimeoutError('Checkpoint installation not completed within two hours')
        time.sleep(20)
    env = os.environ.copy()
    env.update(XLA_PYTHON_CLIENT_PREALLOCATE='false', PYTHONUNBUFFERED='1',
               XDG_CACHE_HOME=str(ROOT/'cache/xdg'), HF_HOME=str(ROOT/'cache/huggingface'),
               TMPDIR=str(ROOT/'cache/tmp'), CUDA_VISIBLE_DEVICES='0',
               PYTHONPATH=':'.join(str(p) for p in [REPO/'XPolicyLab/policy/physicalRSI/runtime', REPO, REPO/'XPolicyLab']))
    for secret in ['PHYSICALRSI_AGENT_API_KEY','OPENAI_API_KEY','ARK_API_KEY']:
        env.pop(secret,None)
    policy_python = ROOT/'models/skill-assets/implementations/openpi/.venv/bin/python'
    server_command = [str(policy_python),str(ROOT/'result/cloud_fixed_skill_server.py'),
                      '--skill',args.skill,'--output',str(OUT),'--port','6011']
    (OUT/'policy-command.json').write_text(json.dumps(server_command,indent=2))
    with (OUT/'policy.log').open('w') as log:
        server = subprocess.Popen(server_command,cwd=REPO,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    save('loading_policy',policy_pid=server.pid)
    deadline=time.monotonic()+1200
    while True:
        if server.poll() is not None:
            raise RuntimeError('Policy server exited during initialization; see policy.log')
        receipt=OUT/'policy-status.json'
        if receipt.exists():
            current=json.loads(receipt.read_text())
            if current['state']=='ready':break
            if current['state']=='failed':raise RuntimeError(str(current['error']))
        if time.monotonic()>deadline:raise TimeoutError('Policy initialization exceeded 20 minutes')
        time.sleep(3)
    run_id = OUT.name
    label='cloud-fixed-'+args.skill+'-smoke'
    env.update(EVAL_NUM='1',ROBODOJO_RUN_ID=run_id)
    client_command=[str(ROOT/'envs/run-native-simulator.sh'),str(REPO/'src/eval_client/main.py'),
                    '--task_name','general_pickup','--num_envs','1','--env_cfg_type','arx_x5',
                    '--device_id','0','--policy_name','physicalRSI','--port','6011','--host','127.0.0.1',
                    '--additional_info',label,'--seed','0','--headless','--enable_cameras']
    (OUT/'client-command.json').write_text(json.dumps(client_command,indent=2))
    with (OUT/'client.log').open('w') as log:
        client=subprocess.Popen(client_command,cwd=REPO,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    save('running_native_episode',client_pid=client.pid)
    deadline=time.monotonic()+3600
    while client.poll() is None:
        if server.poll() is not None:raise RuntimeError('Policy server exited during the native episode')
        if time.monotonic()>deadline:raise TimeoutError('Native episode exceeded one hour')
        time.sleep(5)
    results=list((REPO/'eval_result').glob(f'*/general_pickup/physicalRSI/*/0_{label}/{run_id}/_result.json'))
    if len(results)!=1:raise RuntimeError(f'Expected one native result, found {len(results)}; client exit={client.returncode}')
    native=json.loads(results[0].read_text())
    (OUT/'native-result.json').write_text(json.dumps(native,indent=2)+'\n')
    completed=native.get('eval_time')==1 and len(native.get('details',{}))==1
    if not completed:raise RuntimeError('Native result did not contain one completed episode')
    if int(next(iter(native['details'].values()))['layout_id']) != 0:
        raise RuntimeError('Native result is not the requested episode-zero layout')
    save('complete',completed=True,client_exit_code=client.returncode,
         native_result=native,native_result_path=str(results[0]),
         task_success=bool(next(iter(native['details'].values()))['success']))
except Exception as exc:
    save('failed',error={'type':type(exc).__name__,'message':str(exc)})
    raise
finally:
    stop(client)
    stop(server)
