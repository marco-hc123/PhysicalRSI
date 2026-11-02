"""Exercise the pinned native general_pickup scene without a policy or API calls."""
from pathlib import Path
import argparse
import json
import os
import time
import traceback

ROOT = Path('/mnt/data/physical-RSI')
REPO = ROOT / 'code/RoboDojo'
started = time.monotonic()
parser = argparse.ArgumentParser()
parser.add_argument('--output', required=True)
from isaaclab.app import AppLauncher
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
OUT = Path(args.output)
OUT.mkdir(parents=True, exist_ok=True)
os.chdir(REPO)
result = {
    'scope': 'Native RoboDojo general_pickup episode-zero scene, robot state and RGB preflight',
    'task': 'general_pickup', 'episode': 0, 'num_envs': 1,
    'api_calls': 0, 'policy_executed': False, 'robot_task_success': None,
    'passed': False,
}
app = None
env = None


def write(stage):
    result['stage'] = stage
    result['elapsed_seconds'] = time.monotonic() - started
    tmp = OUT / 'result.json.tmp'
    tmp.write_text(json.dumps(result, indent=2) + '\n')
    tmp.replace(OUT / 'result.json')
    print('NATIVE_SCENE_STAGE', stage, flush=True)


try:
    write('starting_isaac_app')
    from env.camera_manager.capture.render_sync import add_zero_delay_kit_args
    add_zero_delay_kit_args(args)
    app = AppLauncher(args).app
    write('importing_native_environment')
    import numpy as np
    import torch
    from PIL import Image
    from omegaconf import OmegaConf
    from utils.load_file import load_yaml
    from utils.pipeline_utils import process_randomization, process_config
    from env.seed_manager.seed_manager import SeedManager
    from env.observation_manager.obs_manager import ObsManager
    from task.RoboDojo.tasks.general_pickup import general_pickup

    eval_cfg = load_yaml(REPO / 'env_cfg/arx_x5.yml')
    eval_cfg.update(task_name='general_pickup', num_envs=1, device_id=0,
                    eval_batch=False, seed=0, eval_num=1)
    cfg = OmegaConf.create({
        name: load_yaml(REPO / 'env_cfg' / name / (eval_cfg['config'][name] + '.yml'))
        for name in ['sim', 'scene', 'camera', 'robot']
    })
    cfg.task_env = load_yaml(REPO / 'task/RoboDojo/config/general_pickup.yml')
    cfg.eval_cfg = eval_cfg
    cfg.sim.scene.num_envs = 1
    cfg.sim.seed = [0]
    cfg.camera.default_frequency = eval_cfg['observation']['collect_freq']
    cfg = process_randomization(cfg)
    cfg, _ = process_config(cfg, task_name='general_pickup')
    (OUT / 'config.yaml').write_text(OmegaConf.to_yaml(cfg))
    seeds = SeedManager(cfg.eval_cfg)
    seeds.init_eval()
    layout = seeds.get_seed_scene_info(0)

    write('constructing_robot_and_scene')
    env = general_pickup(cfg, app)
    env.success = [True]  # Layout-stability state, not task-success evidence.
    env.end_flag = [False]
    env.scene_manager.layout_manager.replay = True
    env.scene_manager.layout_manager.set_saved_layout(0, layout)
    write('resetting_episode_zero')
    env.reset(seed=[0])
    env.scene_manager.apply_saved_poses(env_idx_list=[0])
    result['layout_valid'] = bool(env.scene_manager.layout_manager.layout_valid[0])
    write('checking_layout_stability')
    stable, unstable = env.scene_manager.layout_manager.check_layout_stability(env)
    result['layout_stable'] = bool(stable)
    result['unstable_envs'] = list(unstable)
    env.robot_manager.set_origin_endpose()
    env.robot_manager.set_robot_init_state()
    env.reward_manager.init_state()
    obs = ObsManager(cfg.eval_cfg.observation, 1, env.dt, 'general_pickup', {}, [0])
    obs.initialize(env)
    obs.reset()

    write('warming_cameras')
    tick = time.monotonic()
    for i in range(200):
        env.sim_step()
        if i % 5 == 0:
            obs.render_for_capture()
    result['warmup_steps'] = 200
    result['warmup_wall_seconds'] = time.monotonic() - tick
    cameras = []
    states = {}
    write('capturing_observations')
    for frame in range(3):
        obs.render_for_capture()
        observation = obs.get_obs([0])[0]
        result['instruction'] = str(observation['instruction'])
        for key, value in observation['state'].items():
            if isinstance(value, torch.Tensor):
                value = value.detach().cpu().numpy()
            value = np.asarray(value)
            states[key] = {'shape': list(value.shape), 'finite': bool(np.isfinite(value).all())}
        for name, camera in observation['vision'].items():
            value = camera['color']
            if isinstance(value, torch.Tensor):
                value = value.detach().cpu().numpy()
            value = np.asarray(value)
            valid = value.ndim == 3 and value.shape[2] == 3 and value.size > 0
            safe_name = ''.join(c if c.isalnum() or c in '-_' else '_' for c in name)
            if valid:
                Image.fromarray(value.astype(np.uint8)).save(OUT / f'{safe_name}-{frame}.png')
            cameras.append({'name': name, 'frame': frame, 'shape': list(value.shape),
                            'std': float(value.std()), 'rgb_valid': bool(valid),
                            'nonconstant': bool(value.std() > 1)})
        for _ in range(5):
            env.sim_step()
    result['cameras'] = cameras
    result['robot_state'] = states
    result['gpu_peak_torch_allocated_bytes'] = int(torch.cuda.max_memory_allocated())
    result['passed'] = bool(result['layout_valid'] and result['layout_stable'] and states
                            and all(v['finite'] for v in states.values()) and cameras
                            and all(v['rgb_valid'] and v['nonconstant'] for v in cameras))
    write('complete')
except Exception as exc:
    result['error'] = {'type': type(exc).__name__, 'message': str(exc)}
    result['traceback'] = traceback.format_exc()
    traceback.print_exc()
    write('failed')
finally:
    if env is not None:
        try:
            env.close()
        except Exception:
            traceback.print_exc()
    if app is not None:
        app.close()
raise SystemExit(0 if result['passed'] else 1)
