import copy,json,sys,shutil
from pathlib import Path
R=Path('/mnt/data/physical-RSI');O=R/'result/43_rejection_contract_20261107';P=R/'result/41_observation_loop_20261107';I=R/'result/25_system2_integration_20261030T050100Z/integration-sources'
sys.path[:0]=[str(O/'code'),str(I),str(I/'framework-validation-v3')]
from PhysicalRSI_core.infra.storage import atomic_json,read_json,file_digest
from PhysicalRSI_core.self_harness.artifacts import verify_harness
from PhysicalRSI_baselines.robodojo.native_runtime import NativeRuntime
from PhysicalRSI_baselines.robodojo.workflow import manifest
from PhysicalRSI_baselines.robodojo.evidence import verify_case
assert read_json(P/'migration/LAB_ARCHIVE_VERIFIED.json')['state']=='verified'
assert read_json(O/'cpu-contract-results.json')['state']=='passed'
protocol=read_json(O/'protocol.json');old=read_json(P/'native-campaign/campaign.json');parent=next(e for e in old['entries'] if e['name']=='fixed_six_turns');assert verify_harness(parent['harness'])==parent['harness_sha256']
base=read_json(parent['runtime']);assert base['policy_spec']['configuration']['latch_gripper_commands'] is True
cases=old['cases'];assert cases==protocol['layouts']
for case in cases:verify_case(case,old['layout_root'])
C=O/'native-campaign';C.mkdir();files={str(p):file_digest(p) for p in (O/'code').glob('*.py')};evidence=O/'driver-contract-provenance/code_execution.py';files[str(evidence)]=file_digest(evidence);entries=[];checks=[]
for row in protocol['conditions']:
 name=row['name'];cfg=copy.deepcopy(base);cfg['policy_spec']['entrypoint']='structured_feedback:assemble'
 for key in ['files','policy_files']:cfg[key].update(files)
 cfg['policy_spec']['files'].update(files);cfg['policy_spec']['configuration']['output']=str(O/'backend-traces'/name)
 for key in ['simulator_environment','policy_environment']:cfg[key]['PYTHONPATH']=str(O/'code')+':'+cfg[key]['PYTHONPATH']
 cfg['simulator_environment']['PHYSICALRSI_SIDECAR_ROOT']=str(O/'sim-diagnostics'/name)
 rp=O/'runtimes'/(name+'.json');rp.parent.mkdir(exist_ok=True);atomic_json(rp,cfg);runtime=NativeRuntime(cfg)
 target=C/'harnesses'/name;shutil.copytree(Path(parent['harness']['root']),target,symlinks=False);atomic_json(target/'assets.json',runtime.identity())
 source=O/'candidates'/name/'candidate.py';assert file_digest(source)==row['candidate_sha256'];shutil.copy2(source,target/'code/classify_objects.py')
 expert=dict(name='code.classify_objects',revision=file_digest(source));atomic_json(target/'skills.json',{expert['name']:dict(revision=expert['revision'],source='code/classify_objects.py')});atomic_json(target/'skill_selection.json',dict(skill_choices={'classify_objects':expert}))
 harness=manifest(target,'rejection_contract_'+name);revision=verify_harness(harness);admit=runtime.admit(harness,O/'native-preparation/admission'/name);check=runtime.check();assert admit['accepted'] and check['ready'],(admit,check)
 checks.append(dict(condition=name,check=check));entries.append(dict(name=name,expert=expert,harness=harness,harness_sha256=revision,runtime=str(rp),runtime_sha256=file_digest(rp)))
atomic_json(O/'native-preparation/runtime-preflights.json',checks)
atomic_json(C/'campaign.json',dict(schema='physicalrsi.rgb-campaign/v1',protocol=str(O/'protocol.json'),protocol_sha256=file_digest(O/'protocol.json'),runtime=entries[0]['runtime'],runtime_sha256=file_digest(Path(entries[0]['runtime'])),per_entry_runtime=True,layout_root=old['layout_root'],cases=cases,entries=entries,planned_cases=5,api_calls=0,selection='Manual zero-action rejection contract pilot;prior control reused,pi05 retained',raw_task_budget_unchanged=1100))
print(json.dumps(dict(state='prepared',planned_cases=5)))
