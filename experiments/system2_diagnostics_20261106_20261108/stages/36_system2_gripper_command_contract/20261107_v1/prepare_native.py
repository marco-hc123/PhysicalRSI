import copy,datetime,shutil,sys,json
from pathlib import Path
R=Path('/mnt/data/physical-RSI');O=R/'result/37_gripper_command_contract_20261107';P=R/'result/36_postgrasp_diagnosis_20261107';I=R/'result/25_system2_integration_20261030T050100Z/integration-sources'
sys.path[:0]=[str(O/'code'),str(I),str(I/'framework-validation-v3')]
from PhysicalRSI_core.infra.storage import atomic_json,read_json,file_digest
from PhysicalRSI_core.self_harness.artifacts import verify_harness
from PhysicalRSI_baselines.robodojo.native_runtime import NativeRuntime
from PhysicalRSI_baselines.robodojo.workflow import manifest
from PhysicalRSI_baselines.robodojo.evidence import verify_case
assert read_json(P/'migration/LAB_ARCHIVE_VERIFIED.json')['state']=='verified'
assert read_json(O/'offline-validation.json')['state']=='passed';assert read_json(O/'native-cpu-validation.json')['state']=='passed'
protocol=read_json(O/'protocol.json');prior=read_json(P/'native-campaign/campaign.json');parent=prior['entries'][0];assert verify_harness(parent['harness'])==parent['harness_sha256'];base=read_json(parent['runtime'])
full=read_json(R/'result/35_trajectory_contract_20261106/native-campaign/campaign.json');cases=full['cases'];assert len(cases)==5
for case in cases:verify_case(case,full['layout_root'])
C=O/'native-campaign';C.mkdir();files={str(p):file_digest(p) for p in (O/'code').glob('*.py')};entries=[];checks=[]
for name,latch in [('measured_state_control',False),('latched_command',True)]:
 cfg=copy.deepcopy(base)
 for key in ['files','policy_files']:cfg[key].update(files)
 cfg['policy_spec']['files'].update(files);cfg['policy_spec']['entrypoint']='gripper_contract:assemble'
 cfg['policy_spec']['configuration'].update(output=str(O/'backend-traces'/name),latch_gripper_commands=latch)
 for key in ['simulator_environment','policy_environment']:cfg[key]['PYTHONPATH']=str(O/'code')+':'+cfg[key]['PYTHONPATH']
 cfg['simulator_environment']['PHYSICALRSI_SIDECAR_ROOT']=str(O/'sim-diagnostics'/name)
 rp=O/'runtimes'/(name+'.json');rp.parent.mkdir(exist_ok=True);atomic_json(rp,cfg);runtime=NativeRuntime(cfg)
 target=C/'harnesses'/name;shutil.copytree(Path(parent['harness']['root']),target,symlinks=False);atomic_json(target/'assets.json',runtime.identity());assert file_digest(target/'code/classify_objects.py')==protocol['candidate_sha256']
 harness=manifest(target,'gripper_contract_'+name);revision=verify_harness(harness);admission=runtime.admit(harness,O/'native-preparation/admission'/name);check=runtime.check();assert admission['accepted'] and check['ready'],(admission,check)
 checks.append(dict(condition=name,check=check));entries.append(dict(name=name,expert=parent['expert'],harness=harness,harness_sha256=revision,runtime=str(rp),runtime_sha256=file_digest(rp)))
atomic_json(O/'native-preparation/runtime-preflights.json',checks)
atomic_json(C/'campaign.json',dict(schema='physicalrsi.rgb-campaign/v1',protocol=str(O/'protocol.json'),protocol_sha256=file_digest(O/'protocol.json'),runtime=entries[0]['runtime'],runtime_sha256=entries[0]['runtime_sha256'],per_entry_runtime=True,layout_root=full['layout_root'],cases=cases,entries=entries,planned_cases=10,api_calls=0,selection='Manual command-retention diagnosis, pi05 retained',raw_task_budget_unchanged=1100))
print(json.dumps(dict(state='prepared',planned_cases=10,conditions=2)))
