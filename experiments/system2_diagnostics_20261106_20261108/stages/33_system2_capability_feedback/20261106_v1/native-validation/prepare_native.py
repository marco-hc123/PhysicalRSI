"""Bind exact generated code AND proposed memory to the frozen native executor."""
import datetime,json,shutil,sys
from pathlib import Path
R=Path('/mnt/data/physical-RSI');O=R/'result/34_capability_feedback_20261106'
I=R/'result/25_system2_integration_20261030T050100Z/integration-sources'
sys.path.insert(0,str(I));sys.path.insert(0,str(I/'framework-validation-v3'))
from PhysicalRSI_core.infra.storage import atomic_json,file_digest,read_json
from PhysicalRSI_core.self_harness.artifacts import verify_harness
from PhysicalRSI_baselines.robodojo.native_runtime import NativeRuntime
from PhysicalRSI_baselines.robodojo.evidence import verify_case
from PhysicalRSI_baselines.robodojo.workflow import manifest
P=O/'inputs/protocol.json';protocol=read_json(P)
old=read_json(R/'result/31_rgb_supplement_20261105/native-campaign/campaign.json')
assert file_digest(Path(old['runtime']))==old['runtime_sha256']=='264b13eea4bc17a7505df43b868711eaba04f4f085117eade195e1e3eb341067'
runtime=NativeRuntime(read_json(old['runtime']));identity=runtime.identity()
parent=next(x for x in old['entries'] if x['name']=='augmented_3')
assert verify_harness(parent['harness'])==parent['harness_sha256']
cases=old['cases'];assert len(cases)==5
for case in cases:verify_case(case,old['layout_root'])
C=O/'native-campaign';C.mkdir(exist_ok=True);assert not (C/'campaign.json').exists()
audits={x['candidate']:x for x in read_json(O/'inputs/offline-validation/candidate-audit.json')}
ledger={x['id']:x for x in read_json(O/'inputs/ledger.json')}
entries=[];rejected=[]
for row in protocol['requests']:
 name=row['id'];a=audits[name]
 if not a['admitted']:rejected.append(dict(name=name,reason='CPU admission',detail=a,native_score=None));continue
 source=O/'inputs/candidates'/name/'candidate.py';proposal_path=source.parent/'proposal.json';proposal=read_json(proposal_path)
 assert file_digest(source)==ledger[name]['source_sha256']==a['source_sha256']
 assert file_digest(proposal_path)==ledger[name]['proposal_sha256']==a['proposal_sha256']
 target=C/'harnesses'/name;shutil.copytree(Path(parent['harness']['root']),target,symlinks=False)
 shutil.copy2(source,target/'code/classify_objects.py')
 expert=dict(name='code.classify_objects',revision=file_digest(source))
 atomic_json(target/'skills.json',{expert['name']:dict(revision=expert['revision'],source='code/classify_objects.py')})
 atomic_json(target/'skill_selection.json',dict(skill_choices={'classify_objects':expert}))
 memory=read_json(target/'memory_rules.json');memory['classify_objects']=proposal['memory'];atomic_json(target/'memory_rules.json',memory)
 assert read_json(target/'assets.json')==identity
 assert read_json(target/'memory_rules.json')['classify_objects']==proposal['memory']
 harness=manifest(target,'capability_'+name);revision=verify_harness(harness)
 admission=runtime.admit(harness,O/'native-preparation/admission'/name)
 if not admission['accepted']:rejected.append(dict(name=name,reason='native admission',detail=admission,native_score=None));continue
 entries.append(dict(name=name,arm=row['arm'],replicate=row['replicate'],expert=expert,harness=harness,harness_sha256=revision,origin=dict(role='New generated candidate and proposed memory, no manual code edit',source_sha256=file_digest(source),proposal_sha256=file_digest(proposal_path))))
atomic_json(O/'native-preparation/rejected.json',rejected)
assert entries,'No admitted candidates; do not invent native cases'
check=runtime.check();atomic_json(O/'native-preparation/runtime-preflight.json',check);assert check['ready'],check
atomic_json(C/'campaign.json',dict(schema='physicalrsi.rgb-campaign/v1',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),protocol=str(P),protocol_sha256=file_digest(P),runtime=old['runtime'],runtime_sha256=old['runtime_sha256'],layout_root=old['layout_root'],cases=cases,entries=entries,planned_cases=5*len(entries),generation_planned_native_cases=30,rejected_candidates=rejected,api_calls=0,selection='No promotion; pi05 retained. Generated feedback comparison on exposed diagnostic layouts.',raw_task_budget_unchanged=1100))
print(json.dumps(dict(state='prepared',conditions=len(entries),planned_cases=5*len(entries),rejected=len(rejected))))
