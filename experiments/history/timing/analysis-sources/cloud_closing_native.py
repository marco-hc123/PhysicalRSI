"""Instrument the native evaluator without changing decisions, rewards or resets."""
import builtins
import json
import os
from pathlib import Path
import runpy
import sys
import time

OUT = Path(os.environ['PHYSICALRSI_STUDY_OUTPUT'])
selected = [int(x) for x in os.environ['PHYSICALRSI_EVAL_LAYOUTS'].split(',')]
assert selected and len(selected) == len(set(selected))
episode = {'index': -1, 'layout': None}


def event(kind, **values):
    row = dict(kind=kind, monotonic=time.monotonic(), unix=time.time(), pid=os.getpid(),
               episode_index=episode['index'], layout=episode['layout'], **values)
    with (OUT/'native-events.jsonl').open('a') as f:
        f.write(json.dumps(row, default=str)+'\n')


event('native_process_start', requested_layouts=selected)
from env.seed_manager.seed_manager import SeedManager
original_init = SeedManager.init_eval


def subset_init(self, *args, **kwargs):
    original_init(self, *args, **kwargs)
    assert not (set(selected)-set(self.seed_info)), 'Missing preregistered layout'
    self.seed_list = [x for x in selected if x in self.seed_list]
    self.st_idx, self.ed_idx, self.idx = 0, len(self.seed_list), 0
    self._current_batch_seeds = None
    event('layout_inventory_bound', layouts=self.seed_list,
          files={i: self.seed_info[i] for i in self.seed_list})


SeedManager.init_eval = subset_init


def instrument(env):
    event('native_environment_created', step_limit=env.step_lim, physics_dt=env.dt,
          collect_interval=env.obs_manager.collect_interval, save_dir=env.save_dir)
    reset, run_eval, take = env.reset, env.run_eval, env.take_action_batch
    def measured_reset(seed=None, options=None):
        episode['index'] += 1
        episode['layout'] = int(seed[0])
        event('reset_start')
        try:
            result = reset(seed=seed, options=options)
            event('reset_ready', control_dt=env.dt*env.obs_manager.collect_interval)
            return result
        except Exception as e:
            event('reset_error', error_type=type(e).__name__, error=str(e))
            raise
    def measured_take(actions_list, env_idx_list=None):
        before, tick = list(env.take_action_cnt), time.monotonic()
        try:
            result = take(actions_list, env_idx_list)
            event('control_ack', seconds=time.monotonic()-tick,
                  before=before, after=list(env.take_action_cnt), ended=list(env.end_flag),
                  success=list(env.success))
            return result
        except Exception as e:
            event('control_error', before=before, after=list(env.take_action_cnt),
                  error_type=type(e).__name__, error=str(e))
            raise
    def measured_run():
        event('episode_start')
        try:
            result = run_eval()
            event('episode_end', steps=list(env.take_action_cnt), success=list(env.success),
                  ended=list(env.end_flag), native_result=env.eval_result,
                  unstable_envs=list(env.unstable_envs))
            return result
        except Exception as e:
            event('episode_error', steps=list(env.take_action_cnt), error_type=type(e).__name__, error=str(e))
            raise
    env.reset, env.run_eval, env.take_action_batch = measured_reset, measured_run, measured_take
    return env


original_import = builtins.__import__
patched = False


def measured_import(name, globals=None, locals=None, fromlist=(), level=0):
    global patched
    result = original_import(name, globals, locals, fromlist, level)
    if name == 'src.eval_client.eval_env' and not patched:
        module = sys.modules.get(name)
        if module and hasattr(module, 'create_eval_env'):
            patched = True
            factory = module.create_eval_env
            def create(*a, **kw):
                return instrument(factory(*a, **kw))
            module.create_eval_env = create
    return result


builtins.__import__ = measured_import
try:
    runpy.run_path('/mnt/data/physical-RSI/code/RoboDojo/src/eval_client/main.py', run_name='__main__')
finally:
    event('native_process_exit')
