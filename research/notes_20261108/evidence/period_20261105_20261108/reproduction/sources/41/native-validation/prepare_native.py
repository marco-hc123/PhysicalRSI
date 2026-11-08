"""Freeze a one-cycle skill-capacity experiment without changing native tasks."""
import copy, json, sys, shutil, hashlib
from pathlib import Path
O=Path(__file__).resolve().parent; R=O.parents[1]
P=R/'result/43_rejection_contract_20261107'
I=R/'result/25_system2_integration_20261030T050100Z/integration-sources'
sys.path[:0]=[str(O/'code'),str(I),str(I/'framework-validation-v3')]
from PhysicalRSI_core.infra.storage import atomic_json,read_json,file_digest
from PhysicalRSI_core.self_harness.artifacts import verify_harness
from PhysicalRSI_baselines.robodojo.native_runtime import NativeRuntime
from PhysicalRSI_baselines.robodojo.workflow import manifest
from PhysicalRSI_baselines.robodojo.evidence import verify_case
assert read_json(P/'native-campaign/status.json')['state']=='diagnostic_matrix_completed'
assert read_json(P/'migration/LAB_ARCHIVE_VERIFIED.json')['state']=='verified'
old=read_json(P/'native-campaign/campaign.json');parent=old['entries'][0]
assert verify_harness(parent['harness'])==parent['harness_sha256']
cfg=copy.deepcopy(read_json(parent['runtime']))
source=O/'candidates/single_cycle/candidate.py'
original=P/'candidates/structured_rejection/candidate.py'
assert source.read_text()==original.read_text().replace('for turn in range(6):','for turn in range(1):')
shutil.copytree(P/'driver-contract-provenance',O/'driver-contract-provenance')
protocol=read_json(O/'protocol-draft.json')
protocol.update(layouts=old['cases'],layout_root=old['layout_root'],parent_candidate_sha256=file_digest(original),source_versions_reference=str(P/'native-campaign/campaign.json'))
for case in old['cases']:verify_case(case,old['layout_root'])
atomic_json(O/'protocol.json',protocol)
files={str(p):file_digest(p) for p in (O/'code').glob('*.py')}
p=O/'driver-contract-provenance/code_execution.py';files[str(p)]=file_digest(p)
for key in ['files','policy_files']:cfg[key].update(files)
cfg['policy_spec']['files'].update(files)
cfg['policy_spec']['entrypoint']='structured_feedback:assemble'
cfg['policy_spec']['configuration']['output']=str(O/'backend-traces/single_cycle')
for key in ['simulator_environment','policy_environment']:
    cfg[key]['PYTHONPATH']=str(O/'code')+':'+cfg[key]['PYTHONPATH']
cfg['simulator_environment']['PHYSICALRSI_SIDECAR_ROOT']=str(O/'sim-diagnostics/single_cycle')
rp=O/'runtimes/single_cycle.json';rp.parent.mkdir();atomic_json(rp,cfg)
runtime=NativeRuntime(cfg);C=O/'native-campaign';C.mkdir()
target=C/'harnesses/single_cycle';shutil.copytree(parent['harness']['root'],target,symlinks=False)
atomic_json(target/'assets.json',runtime.identity());shutil.copy2(source,target/'code/classify_objects.py')
expert=dict(name='code.classify_objects',revision=file_digest(source))
atomic_json(target/'skills.json',{expert['name']:dict(revision=expert['revision'],source='code/classify_objects.py')})
atomic_json(target/'skill_selection.json',dict(skill_choices={'classify_objects':expert}))
h=manifest(target,'single_cycle_skill_floor');revision=verify_harness(h)
check=runtime.check();admit=runtime.admit(h,O/'native-preparation/admission')
assert check['ready'] and admit['accepted'],(check,admit)
atomic_json(O/'native-preparation/check.json',check)
entry=dict(name='single_cycle',expert=expert,harness=h,harness_sha256=revision,runtime=str(rp),runtime_sha256=file_digest(rp))
atomic_json(C/'campaign.json',dict(protocol=str(O/'protocol.json'),protocol_sha256=file_digest(O/'protocol.json'),runtime=str(rp),runtime_sha256=file_digest(rp),per_entry_runtime=True,layout_root=old['layout_root'],cases=old['cases'],entries=[entry],planned_cases=5,api_calls=0,selection='Single-cycle capability diagnosis only; pi05 retained',raw_task_budget_unchanged=1100))
print(json.dumps(dict(state='prepared',native_cases=5,protocol_sha256=file_digest(O/'protocol.json'))))
