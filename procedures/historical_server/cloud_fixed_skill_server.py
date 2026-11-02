"""One fixed VLA route for a native closed-loop deployment test; no agent calls."""
import argparse
import asyncio
from copy import deepcopy
import json
import os
from pathlib import Path
import time
import traceback

import numpy as np

ROOT = Path('/mnt/data/physical-RSI')
parser = argparse.ArgumentParser()
parser.add_argument('--skill', choices=['pi05', 'pi05-sparse-memory'], required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--port', type=int, default=6011)
args = parser.parse_args()
OUT = args.output
OUT.mkdir(parents=True, exist_ok=True)
start = time.monotonic()
status = dict(scope='Fixed pretrained VLA native closed-loop deployment test',
              agent_enabled=False, api_calls=0, skill=args.skill, task='general_pickup',
              episode=0, seed=0, action_calls=0, observation_calls=0,
              task_success=None, state='loading_checkpoint')


def save():
    status['elapsed_seconds'] = time.monotonic() - start
    temp = OUT / 'policy-status.json.tmp'
    temp.write_text(json.dumps(status, indent=2) + '\n')
    temp.replace(OUT / 'policy-status.json')


def arrays(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from arrays(item)
    elif isinstance(value, (tuple, list)):
        for item in value:
            yield from arrays(item)
    elif isinstance(value, np.ndarray):
        yield value


save()
try:
    from PhysicalRSI_baselines.robodojo.execution_skills import load_skill
    from XPolicyLab.model_template import ModelTemplate
    from client_server.ws.model_server import PolicyServer, PolicyServerConfig
    import PhysicalRSI_baselines.robodojo as package
    example = Path(package.__file__).parent / 'configs/skill_library.example.json'
    descriptor = deepcopy(json.loads(example.read_text())['skills'][args.skill])
    descriptor['configuration']['model_path'] = str(ROOT / 'models/skill-assets/checkpoints' / args.skill)
    descriptor['configuration']['require_gpu'] = True
    deployment = dict(task_name='general_pickup', env_cfg_type='arx_x5', action_type='joint', seed=0)
    (OUT / 'fixed-skill.json').write_text(json.dumps(dict(descriptor=descriptor, deployment=deployment), indent=2))
    skill = load_skill(descriptor, deployment)
    status['load_seconds'] = time.monotonic() - start
    status['skill_identity'] = skill.describe()
    save()

    class FixedModel(ModelTemplate):
        def update_obs(self, observation):
            return self.update_obs_batch([observation])

        def update_obs_batch(self, observations):
            if status['observation_calls'] == 0:
                row = observations[0]
                payload = {'instruction': np.asarray(row['instruction'])}
                payload.update({'state__'+key: np.asarray(value) for key, value in row['state'].items()})
                payload.update({'camera__'+key: np.asarray(value['color']) for key, value in row['vision'].items()})
                np.savez_compressed(OUT / 'first_observation.npz', **payload)
            status['observation_calls'] += 1
            return skill.observe(observations)

        def get_action(self):
            return self.get_action_batch([0])[0]

        def get_action_batch(self, env_idx_list=None):
            tick = time.monotonic()
            actions = skill.execute(env_idx_list or [0])
            values = list(arrays(actions))
            if not values or any(not np.isfinite(value).all() for value in values):
                raise ValueError('No action arrays or non-finite action returned')
            status['action_calls'] += 1
            status['state'] = 'serving_native_actions'
            with (OUT / 'inference.jsonl').open('a') as stream:
                stream.write(json.dumps(dict(call=status['action_calls'], seconds=time.monotonic()-tick,
                                             shapes=[list(value.shape) for value in values], finite=True))+'\n')
            save()
            return actions

        def reset(self):
            return skill.reset()

        def physicalrsi_identity(self):
            return dict(scope=status['scope'], agent_enabled=False, api_calls=0,
                        fixed_skill=skill.describe(), qualification=False)

        def on_trial_end(self, result=None):
            (OUT / 'trial-end.json').write_text(json.dumps(result, default=str, indent=2))

    async def serve():
        server = PolicyServer(FixedModel(), PolicyServerConfig(host='127.0.0.1', port=args.port))
        await server.start()
        status['state'] = 'ready'
        save()
        print('FIXED_SKILL_READY', args.skill, flush=True)
        try:
            await asyncio.Future()
        finally:
            await server.stop()
            skill.close()

    asyncio.run(serve())
except BaseException as exc:
    status['state'] = 'failed'
    status['error'] = dict(type=type(exc).__name__, message=str(exc))
    save()
    traceback.print_exc()
    raise
