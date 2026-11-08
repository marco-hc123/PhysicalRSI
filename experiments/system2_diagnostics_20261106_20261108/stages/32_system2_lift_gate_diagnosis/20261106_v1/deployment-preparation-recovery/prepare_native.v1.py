"""Prepare two immutable native harnesses; run only after lab protocol transfer."""
import datetime
import json
import shutil
import sys
from pathlib import Path

R=Path('/mnt/data/physical-RSI')
O=R/'result/32_lift_gate_validation_20261106'
OLD=R/'result/31_rgb_supplement_20261105'
I=R/'result/25_system2_integration_20261030T050100Z/integration-sources'
sys.path.insert(0,str(I/'framework-validation-v3'))
from PhysicalRSI_core.infra.storage import atomic_json,file_digest,read_json
from PhysicalRSI_core.self_harness.artifacts import verify_harness
from PhysicalRSI_baselines.robodojo.native_runtime import NativeRuntime
from PhysicalRSI_baselines.robodojo.evidence import verify_case
from PhysicalRSI_baselines.robodojo.workflow import manifest

protocol=read_json(O/'protocol/native-protocol.json')
old=read_json(OLD/'native-campaign/campaign.json')
assert file_digest(Path(old['runtime']))==old['runtime_sha256']==protocol['runtime_sha256']
runtime=NativeRuntime(read_json(old['runtime']))
identity=runtime.identity()
parent=next(x for x in old['entries'] if x['name']=='augmented_3')
assert verify_harness(parent['harness'])==parent['harness_sha256']
cases=old['cases'];assert len(cases)==5
for case in cases:verify_case(case,old['layout_root'])
assert [x['layout_sha256'] for x in cases]==protocol['layout_sha256']
C=O/'native-campaign';C.mkdir(exist_ok=True)
assert not (C/'campaign.json').exists(),'Existing campaign must be reconciled before prepare'
entries=[]
for name in ['original','bypass_lift_guard']:
    source=O/'inputs/candidates'/name/'candidate.py'
    row=next(v for v in protocol['conditions'] if v['name']==name)
    assert file_digest(source)==row['candidate_sha256']
    target=C/'harnesses'/name
    shutil.copytree(Path(parent['harness']['root']),target,symlinks=False)
    shutil.copy2(source,target/'code/classify_objects.py')
    expert=dict(name='code.classify_objects',revision=file_digest(source))
    atomic_json(target/'skills.json',{expert['name']:dict(revision=expert['revision'],source='code/classify_objects.py')})
    atomic_json(target/'skill_selection.json',dict(skill_choices={'classify_objects':expert}))
    assert read_json(target/'assets.json')==identity
    harness=manifest(target,'lift_gate_'+name)
    revision=verify_harness(harness)
    admission=runtime.admit(harness,O/'native-preparation/admission'/name)
    assert admission['accepted'],admission
    entries.append(dict(name=name,expert=expert,harness=harness,harness_sha256=revision,
        origin=dict(role='manual mechanism ablation; no new model generation',source=str(source),source_sha256=file_digest(source))))
check=runtime.check();atomic_json(O/'native-preparation/runtime-preflight.json',check)
assert check['ready'],check
atomic_json(C/'campaign.json',dict(schema='physicalrsi.rgb-campaign/v1',
    utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),protocol=str(O/'protocol/native-protocol.json'),
    protocol_sha256=file_digest(O/'protocol/native-protocol.json'),runtime=old['runtime'],runtime_sha256=old['runtime_sha256'],
    layout_root=old['layout_root'],cases=cases,entries=entries,planned_cases=10,api_calls=0,
    selection='diagnostic only; pi05 retained without running a new selector',
    qualification='Same frozen native runtime; whole lift guard ablation, not Z-only repair. Historical layouts reused.',
    raw_task_budget_unchanged=1100))
print(json.dumps(dict(state='prepared',conditions=2,planned_cases=10,runtime_ready=check['ready'])))
