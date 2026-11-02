"""Build explicit native integration configuration; never launches an episode."""
from pathlib import Path
import json,os,sys,hashlib,xml.etree.ElementTree as ET
from datetime import datetime,timezone
R=Path('/mnt/data/physical-RSI');O=R/'result/25_system2_integration_20261030T050100Z';S=O/'integration-sources';F=S/'framework';D=S/'native-simulator';C=R/'models/skill-assets/implementations/code-skills';X=R/'code/RoboDojo/XPolicyLab';PY=R/'models/skill-assets/implementations/openpi/.venv/bin/python'
assert not (O/'runtime.json').exists()
env=json.loads((O/'environment-v2.json').read_text())
descriptor=json.loads((C/'runtime/descriptors/classify_objects.json').read_text())
paths=[p.replace('{assets}',str(C)).replace('{xpolicylab_parent}',str(X.parent)).replace('{xpolicylab}',str(X)) for p in descriptor['pythonpath']]
# Keep the modern frozen framework ahead of the historical bundled runtime.
paths=[str(S),str(F),str(D),str(X),*paths,str(C/'runtime')]
env.update(PYTHONPATH=':'.join(paths),PYTHONUNBUFFERED='1',PYTHONNOUSERSITE='1',
    XLA_PYTHON_CLIENT_PREALLOCATE='false',OPENPI_DATA_HOME=str(R/'cache/openpi'),
    XDG_CACHE_HOME=str(R/'cache/xdg'),HF_HOME=str(R/'cache/huggingface'),TMPDIR=str(R/'cache/tmp'),
    CUDA_HOME='/usr/local/cuda-12.8',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',
    CUDA_CACHE_PATH=str(R/'cache/cuda'),WARP_CACHE_PATH=str(R/'cache/warp'))
for k,v in descriptor['environment'].items():
 if k.startswith('CLASSIFY_') and 'MODEL' in k:env[k]=v.replace('{assets}',str(C))
os.environ.update(env);sys.path[:0]=paths
from PhysicalRSI_core.infra.storage import atomic_json,file_digest,digest
from PhysicalRSI_core.infra.isolation import build_runtime
from PhysicalRSI_baselines.robodojo.expert_service import freeze_spec,inventory
from PhysicalRSI_baselines.robodojo.native_runtime import NativeRuntime
from PhysicalRSI_baselines.robodojo.native_preflight import client_files

def status(stage):
 v=dict(stage=stage,pid=os.getpid(),complete=False,utc=datetime.now(timezone.utc).isoformat());atomic_json(O/'controller-status.json',v);atomic_json(R/'result/CURRENT_STEP4.json',dict(directory=str(O),**v));print(json.dumps(v),flush=True)
status('building_isolation_runtime')
build_runtime(O/'isolation-runtime')
status('pinning_primitive_closure')
program=C/'implementations/rdj_v1_classify_objects/6bb861ace4b706d9/rdj_v1_classify_objects'
robots=json.loads((O/'initialization-v3/run/robot-diagnostics.json').read_text())['robots']
arm_bases={r['arm'].split('_')[0]:r['poses']['base']['environment'] for r in robots}
cameras=json.loads((O/'initialization-v3/run/camera-diagnostics.json').read_text())['cameras']
cam=next(r['configuration'] for r in cameras if r['camera']=='cam_head')
state=json.loads((O/'initialization-v3/run/observations/0/state.json').read_text())
dims={k:len(v) for k,v in state.items() if k.endswith('joint_state')}
limits={j.get('name'):j.find('limit').attrib for j in ET.parse(program/'assets/x5/X5A.urdf').getroot().findall('joint') if j.find('limit') is not None}
low=[float(limits['joint'+str(i)]['lower']) for i in range(1,7)];high=[float(limits['joint'+str(i)]['upper']) for i in range(1,7)]
configuration=dict(dimensions=dims,joint_limits={a:dict(low=low,high=high) for a in ['left','right']},arm_bases=arm_bases,camera=cam,robot_yml=str(program/'assets/x5/curobo.yml'),output=str(O/'primitive-services'),object_sizes={'basket':[.20,.15,.07],'watch':[.08,.03,.025],'toy_car':[.08,.05,.04],'camera':[.06,.04,.055],'pen':[.12,.012,.012],'garage':[.06,.04,.055]})
primitive_files={str(S/'step4_native_primitives.py'):file_digest(S/'step4_native_primitives.py')}
closure_roots=[program,C/'dependencies/curobo/9077c9afff1c3fda/curobo',C/'assets/grounding-dino-tiny/074cad48ab8387c7/grounding-dino-tiny',C/'assets/clip-vit-base-patch32/5be8cdefa7ef9c95/clip-vit-base-patch32']
closure=[]
for p in closure_roots:closure.append(inventory(p))
atomic_json(O/'primitive-dependency-inventories.json',closure)
for inv in closure:
 for name,sha in inv['files'].items():primitive_files[str(Path(inv['root'])/name)]=sha
for path in (F/'PhysicalRSI_baselines/robodojo').glob('*.py'):primitive_files[str(path)]=file_digest(path)
policy_spec=dict(schema='physicalrsi.robodojo.code-policy/v1',runtime=str(O/'isolation-runtime'),runtime_manifest_sha256=file_digest(O/'isolation-runtime/manifest.json'),entrypoint='step4_native_primitives:assemble',files=primitive_files,dimensions=dims,configuration=configuration,timeout_s=1500,max_actors=1,action_timeout_s=600,cameras={'cam_head':[480,640,3]},completion_hold_steps=1100)
status('pinning_VLA_experts')
profiles={'pi05':dict(train_config_name='pi05_base_aloha_full_sim_arx-x5_seed_0',repo_id='arx_x5_sim'),'pi05-sparse-memory':dict(train_config_name='pi05_sparse_mem_robodojo_all35_80k',repo_id='robodojo_arx_x5_all35')}
experts={};models={}
for name,profile in profiles.items():
 checkpoint=inventory(R/'models/skill-assets/checkpoints'/name);revision=digest(checkpoint['files']);models[name]=revision
 module='pi05' if name=='pi05' else 'sparse'
 spec=freeze_spec(expert=dict(name=name,revision=revision),entrypoint='PhysicalRSI_baselines.robodojo.skills.'+module+':Model',checkpoint_root=checkpoint['root'],code_roots=[F/'PhysicalRSI_baselines/robodojo/skills',R/'models/skill-assets/implementations/openpi/src',X/'utils',X/'client_server'],deploy=dict(task_name='classify_objects',env_cfg_type='arx_x5',action_type='joint',require_gpu=True,**profile))
 experts[name]=dict(spec=spec,service=dict(python=str(PY),environment=env,dimensions=dims,timeout_s=600,startup_timeout_s=900))
policy_files={}
for root in [F/'PhysicalRSI_baselines/robodojo',F/'PhysicalRSI_core',X/'client_server']:
 for path in root.rglob('*.py'):
  if '__pycache__' not in path.parts:policy_files[str(path)]=file_digest(path)
for path in [X/'model_template.py',X/'utils/process_data.py',R/'code/RoboDojo/env_cfg/arx_x5.yml',R/'code/RoboDojo/env_cfg/robot/_robot_info.json']:
 policy_files[str(path)]=file_digest(path)
files={**client_files(D),**policy_files,str(S/'step4_native_primitives.py'):file_digest(S/'step4_native_primitives.py'),str(S/'simulator-python-v2'):file_digest(S/'simulator-python-v2'),str(S/'isolated-sim-entry.py'):file_digest(S/'isolated-sim-entry.py')}
runtime=dict(schema='physicalrsi.robodojo.native-runtime/v1',files=files,source=str(D),assets=str(R/'code/RoboDojo/Assets'),simulator_root=str(D),initialization_policy_name='physicalRSI',initialization_batch_size=1,generation_workers=1,generation_timeout_s=180,initialization_timeout_s=600,simulator_python=str(S/'simulator-python-v2'),simulator_environment=json.loads((O/'environment-v2.json').read_text()),policy_python=str(PY),policy_environment=env,policy_files=policy_files,policy_spec=policy_spec,experts=experts,gpu=0,simulator_seed=0,resources={'gpu':1},policy_startup_timeout_s=900,policy_cleanup_timeout_s=120,rollout_timeout_s=1800,camera_calibration=False,robot_calibration=False,skill_api=dict(policy_signature='def policy(robot, memory)',task='classify_objects',semantics='Sort visible objects by category into separate baskets; assign one basket per category, grouping identical objects together. No success signal is available from primitives.',methods={'scene':'robot.scene() -> {objects: {category_index: {pose:[x,y,z,w,x,y,z],dims:[x,y,z]}}, observation}; calibrated RGB estimates, names encode category, basket names sorted left to right; no hidden layouts or scores','reobserve':'robot.reobserve() -> {state: observed joint arrays}; no score','approach':'robot.approach(arm="left" or "right", position_m=[x,y,z], quaternion_wxyz=[w,x,y,z]); collision-aware released CuRobo joint trajectory, other arm/gripper preserved; raises RuntimeError if no path. No pose success claim.','gripper':'robot.gripper(arm="left" or "right", command=0 closed or 1 open) -> observed joints; settling only, no grasp success claim'},geometry=dict(world_units='metres',table_z=.765,gripper_tool_offset_above_contact=.125,minimum_contact_tool_z=.920,typical_downward_quaternion={'left':[.6130,-.3593,.6163,.3392],'right':[.3814,-.6197,.3785,.5720]},quaternion_requirement='Normalize to unit length using arithmetic; imports unavailable',basket_release_tool_z=1.01),execution='Only four supplied RPC methods. No imports/files/network/hidden simulation access. Use finite loops. Return gracefully if perception/planning is unavailable; do not retry uncertain manipulation. Returning ends code, then bounded measured-position hold until independent native evaluator termination.',scope='Step4 compatibility assembly with calibrated released RGB/CuRobo primitives; not stock paper performance or formal System2 improvement evidence'))
atomic_json(O/'runtime.json',runtime)
atomic_json(O/'workflow-configuration.json',dict(tasks=['classify_objects'],models=models,development_episodes=1,validation_episodes=1,minimum_vla_score=.6,minimum_gain=0,maximum_regression=0,rollout_batch_size=1))
report=NativeRuntime(runtime).check();atomic_json(O/'runtime-preflight.json',report);assert report['ready'],report
atomic_json(O/'runtime-amendment.json',dict(scope='step4 native compatibility integration only',changes=['Register implemented classify_objects sampler','Pin released RGB reader/CuRobo as trusted primitive backend, not whole task policy','Use measured SDK camera intrinsics and robot base calibration','Disable redundant advisory Agent in fixed-route SelfHarness assessments','Keep original checkpoints and native task rewards unchanged','1+1 integration cohort does not replace formal 5+5 round budgets'],calibration_observation=dict(head_sdk_fy=cam['fy'],released_rgb_ray_fy=640*10/22.212,causal_effect_not_tested=True),physical_qualification=False))
status('native_runtime_configured')
