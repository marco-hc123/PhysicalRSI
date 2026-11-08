"""Pin an isolated diagnostic runtime; preserve candidate and simulator sources."""
import copy,datetime,json,shutil,sys
from pathlib import Path
R=Path('/mnt/data/physical-RSI');O=R/'result/36_postgrasp_diagnosis_20261107';P=R/'result/35_trajectory_contract_20261106'
I=R/'result/25_system2_integration_20261030T050100Z/integration-sources'
sys.path[:0]=[str(O/'code'),str(I),str(I/'framework-validation-v3')]
from PhysicalRSI_core.infra.storage import atomic_json,file_digest,read_json
from PhysicalRSI_core.self_harness.artifacts import verify_harness
from PhysicalRSI_baselines.robodojo.native_runtime import NativeRuntime
from PhysicalRSI_baselines.robodojo.evidence import verify_case
from PhysicalRSI_baselines.robodojo.workflow import manifest
assert read_json(P/'migration/LAB_ARCHIVE_VERIFIED.json')['state']=='verified'
assert read_json(O/'offline-validation.json')['state']=='passed'
protocol=read_json(O/'protocol.json');prior=read_json(P/'native-campaign/campaign.json')
parent=next(e for e in prior['entries'] if e['name']=='released_waypoint_thinning')
assert verify_harness(parent['harness'])==parent['harness_sha256']
assert file_digest(Path(parent['runtime']))==parent['runtime_sha256']
config=read_json(parent['runtime']);cases=[prior['cases'][i] for i in protocol['source_layout_ids']]
for case in cases:verify_case(case,prior['layout_root'])
C=O/'native-campaign';C.mkdir(exist_ok=True);assert not (C/'campaign.json').exists()
new_files={str(p):file_digest(p) for p in (O/'code').glob('*.py')}
for key in ['files','policy_files']:config[key].update(new_files)
config['policy_spec']['files'].update(new_files)
config['policy_spec']['entrypoint']='postgrasp_contract:assemble'
config['policy_spec']['configuration']['output']=str(O/'backend-traces/logging_only')
config['policy_environment']['PYTHONPATH']=str(O/'code')+':'+config['policy_environment']['PYTHONPATH']
config['simulator_environment']['PYTHONPATH']=str(O/'code')+':'+config['simulator_environment']['PYTHONPATH']
config['simulator_environment']['PHYSICALRSI_SIDECAR_ROOT']=str(O/'sim-diagnostics/logging_only')
rp=O/'runtimes/logging_only.json';rp.parent.mkdir(exist_ok=True);atomic_json(rp,config)
runtime=NativeRuntime(config);identity=runtime.identity();target=C/'harnesses/logging_only'
shutil.copytree(Path(parent['harness']['root']),target,symlinks=False);atomic_json(target/'assets.json',identity)
assert file_digest(target/'code/classify_objects.py')==protocol['candidate_sha256']
harness=manifest(target,'postgrasp_logging_only');revision=verify_harness(harness)
admission=runtime.admit(harness,O/'native-preparation/admission/logging_only');check=runtime.check()
assert admission['accepted'] and check['ready'],(admission,check)
entry=dict(name='logging_only',expert=parent['expert'],harness=harness,harness_sha256=revision,runtime=str(rp),runtime_sha256=file_digest(rp),origin=dict(candidate='capability_feedback_2',source_sha256=parent['expert']['revision'],proposed_memory_unchanged=True))
atomic_json(O/'native-preparation/runtime-preflights.json',[dict(condition='logging_only',check=check,admission=admission)])
atomic_json(C/'campaign.json',dict(schema='physicalrsi.rgb-campaign/v1',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),protocol=str(O/'protocol.json'),protocol_sha256=file_digest(O/'protocol.json'),runtime=str(rp),runtime_sha256=file_digest(rp),per_entry_runtime=True,layout_root=prior['layout_root'],cases=cases,entries=[entry],planned_cases=3,api_calls=0,source_layout_ids=protocol['source_layout_ids'],selection='Analysis-only logging; no policy promotion',raw_task_budget_unchanged=1100))
print(json.dumps(dict(state='prepared',planned_cases=3,preflight_ready=check['ready'])))
