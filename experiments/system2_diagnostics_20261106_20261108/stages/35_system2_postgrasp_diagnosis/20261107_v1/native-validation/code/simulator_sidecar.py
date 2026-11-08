"""Privileged state is read ONLY to side files, never added to observations.

No step/render/reset/reward function is invoked by the logger. Original data
object is returned by identity. Diagnostic failures are recorded independently.
"""
import functools, importlib.abc, importlib.machinery, os, sys, time
from pathlib import Path
from diagnostic_common import append,safe

def attach(env, root):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    output=root/('simulator-%s.jsonl'%os.getpid())
    append(output,dict(event='attached',pid=os.getpid(),observation_mutation=False))
    original=env.get_obs_batch
    @functools.wraps(original)
    def observed(*args,**kwargs):
        data=original(*args,**kwargs)
        began=time.monotonic_ns()
        try:
            for observation in data:
                i=int(observation['env_idx'])
                lm=env.scene_manager.layout_manager;rm=env.robot_manager
                record=dict(event='snapshot',env_idx=i,layout_seed=int(env.env_seeds[i]),
                    native_action_count=int(env.take_action_cnt[i]),monotonic_ns=time.monotonic_ns(),
                    scope='analysis-only; no policy access',objects={},robots={},
                    observation_keys=sorted(observation),observation_state=safe(observation.get('state')))
                labels=[]
                for prefix in ['cat0','cat1','cat2','basket']:
                    labels.extend(lm.get_labels_by_prefix(i,prefix))
                for label in sorted(set(labels)):
                    try:
                        name=lm.get_instance_name(i,label);pos,quat=lm.get_instance_pose(i,label=label,relative=False)
                        record['objects'][label]=dict(instance=name,position_world=safe(pos),quaternion_wxyz=safe(quat))
                    except Exception as e:record['objects'][label]=dict(error=type(e).__name__+': '+str(e))
                for robot in rm.robot_list:
                    name=rm.process_name(robot.arm_name)
                    try:
                        record['robots'][name]=dict(ee_pose_world=safe(rm.get_real_endpose(robot,env_idx_list=[i],is_relative=False)[i]),
                            joints=safe(rm.get_joint(robot,env_idx_list=[i])[i]),
                            gripper_raw=safe(rm.get_end_effector_real_val(robot,env_idx_list=[i])[i]))
                    except Exception as e:record['robots'][name]=dict(error=type(e).__name__+': '+str(e))
                record['logging_elapsed_ms']=(time.monotonic_ns()-began)/1e6
                append(output,record)
        except Exception as e:append(output,dict(event='logging_error',error=type(e).__name__+': '+str(e)))
        return data
    env.get_obs_batch=observed
    return env

class Hook(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname!='src.eval_client.eval_env':return None
        spec=importlib.machinery.PathFinder.find_spec(fullname,path)
        if spec is None or spec.loader is None:return None
        loader=spec.loader
        class Loader:
            def create_module(self,spec):return loader.create_module(spec) if hasattr(loader,'create_module') else None
            def exec_module(self,module):
                loader.exec_module(module)
                factory=module.create_eval_env
                @functools.wraps(factory)
                def create(*args,**kwargs):return attach(factory(*args,**kwargs),os.environ['PHYSICALRSI_SIDECAR_ROOT'])
                module.create_eval_env=create
        spec.loader=Loader();return spec

def install_import_hook():sys.meta_path.insert(0,Hook())
