"""Verify both frozen VLA routes on a captured native observation, without an agent."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import time
import traceback
import numpy as np

parser=argparse.ArgumentParser()
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--observation',type=Path,required=True)
args=parser.parse_args()
ROOT=Path('/mnt/data/physical-RSI')
OUT=args.output
OUT.mkdir(parents=True,exist_ok=True)
start=time.monotonic()
result=dict(scope='Both checkpoint skills resident together and inference on one captured native observation',
            simulator_running=False,agent_enabled=False,api_calls=0,task_success=None,
            passed=False,skills={},state='starting')
loaded={}


def save(state):
    result.update(state=state,elapsed_seconds=time.monotonic()-start)
    temp=OUT/'result.json.tmp';temp.write_text(json.dumps(result,indent=2)+'\n');temp.replace(OUT/'result.json')


def gpu():
    return subprocess.run(['nvidia-smi','--query-gpu=memory.used,memory.total,utilization.gpu',
                           '--format=csv,noheader,nounits'],capture_output=True,text=True,check=True).stdout.strip()


def action_arrays(value):
    if isinstance(value,dict):
        for item in value.values():yield from action_arrays(item)
    elif isinstance(value,(list,tuple)):
        for item in value:yield from action_arrays(item)
    elif isinstance(value,np.ndarray):yield value


save('loading')
try:
    from PhysicalRSI_baselines.robodojo.execution_skills import load_skill
    import PhysicalRSI_baselines.robodojo as package
    config=json.loads((Path(package.__file__).parent/'configs/skill_library.example.json').read_text())
    deployment=dict(task_name='general_pickup',env_cfg_type='arx_x5',action_type='joint',seed=0)
    for name in ['pi05','pi05-sparse-memory']:
        descriptor=deepcopy(config['skills'][name]);descriptor['configuration'].update(
            model_path=str(ROOT/'models/skill-assets/checkpoints'/name),require_gpu=True)
        tick=time.monotonic();loaded[name]=load_skill(descriptor,deployment)
        result['skills'][name]=dict(load_seconds=time.monotonic()-tick,identity=loaded[name].describe())
        result['gpu_after_load']=gpu();save('loaded_'+name)
    result['both_resident']=True
    with np.load(args.observation,allow_pickle=False) as data:
        observation=dict(instruction=str(data['instruction']),env_idx=0,
                         state={key.removeprefix('state__'):data[key] for key in data.files if key.startswith('state__')},
                         vision={key.removeprefix('camera__'):{'color':data[key]} for key in data.files if key.startswith('camera__')})
    for name,skill in loaded.items():
        save('inferring_'+name);skill.observe([observation]);tick=time.monotonic()
        actions=skill.execute([0]);values=list(action_arrays(actions))
        valid=bool(values) and all(np.isfinite(value).all() for value in values)
        result['skills'][name].update(first_inference_seconds=time.monotonic()-tick,
                                      action_shapes=[list(value.shape) for value in values],finite=bool(valid))
        if not valid:raise ValueError('Invalid actions from '+name)
        result['gpu_after_inference']=gpu();save('inferred_'+name)
    result['passed']=True;save('complete')
except BaseException as exc:
    result['error']=dict(type=type(exc).__name__,message=str(exc));save('failed');traceback.print_exc();raise
finally:
    for skill in loaded.values():skill.close()
