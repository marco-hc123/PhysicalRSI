import copy,datetime,json,shutil,sys,hashlib
from pathlib import Path
R=Path('/mnt/data/physical-RSI');O=R/'result/36_postgrasp_diagnosis_20261107';I=R/'result/25_system2_integration_20261030T050100Z/integration-sources'
sys.path[:0]=[str(O/'code-v2'),str(I),str(I/'framework-validation-v3')]
from PhysicalRSI_core.infra.storage import atomic_json,file_digest,read_json
from PhysicalRSI_core.self_harness.artifacts import verify_harness
from PhysicalRSI_baselines.robodojo.native_runtime import NativeRuntime
from PhysicalRSI_baselines.robodojo.workflow import manifest
C=O/'native-campaign';old=read_json(C/'campaign.json');assert read_json(C/'status.json')['state']=='stopped_for_diagnosis'
failed=C/'runs/logging_only/attempt-001';observed=read_json(failed/'native/run/observed.json');assert not observed['outcomes'] and len(observed['failures'])==3;assert not list((failed/'episodes').glob('*.json'))
assert read_json(O/'offline-validation-v2.json')['state']=='passed'
D=O/'deployment-attempts/attempt-001';D.mkdir(parents=True)
for rel in ['launch.json','native-controller.log','native-campaign/campaign.json','native-campaign/status.json','native-campaign/controller-failure.json']:
 p=O/rel;q=D/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
repair=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),classification='invalid_deployment',valid_native_cases=0,policy_zero_score=False,errors=['instrumentation wrapper **kwargs altered RPC signature','native worker exclusive eval import hook outranked simulator sidecar'],repairs=['explicit named approach/gripper parameters','wrap NativeObserver.attach while preserving original observer, reward and observation data'],changed_policy_or_scoring=False)
atomic_json(O/'instrumentation-repair-v2.json',repair)
protocol=read_json(O/'protocol.json');protocol.update(instrumentation_revision=2,prior_protocol_sha256=file_digest(O/'protocol.json'),repair=str(O/'instrumentation-repair-v2.json'),frozen_utc=datetime.datetime.now(datetime.timezone.utc).isoformat());atomic_json(O/'protocol-v2.json',protocol)
config=read_json(old['runtime']);files={str(p):file_digest(p) for p in (O/'code-v2').glob('*.py')}
for key in ['files','policy_files']:config[key].update(files)
config['policy_spec']['files'].update(files)
for k in ['policy_environment','simulator_environment']:config[k]['PYTHONPATH']=str(O/'code-v2')+':'+config[k]['PYTHONPATH']
config['policy_spec']['configuration']['output']=str(O/'backend-traces-v2/logging_only')
config['simulator_environment']['PHYSICALRSI_SIDECAR_ROOT']=str(O/'sim-diagnostics/logging_only')
rp=O/'runtimes/logging_only-v2.json';atomic_json(rp,config);runtime=NativeRuntime(config)
parent=old['entries'][0];target=C/'harnesses/logging_only-v2';shutil.copytree(Path(parent['harness']['root']),target,symlinks=False);atomic_json(target/'assets.json',runtime.identity())
harness=manifest(target,'postgrasp_logging_only_v2');revision=verify_harness(harness);admission=runtime.admit(harness,O/'native-preparation/admission/logging_only-v2');check=runtime.check();assert admission['accepted'] and check['ready'],(admission,check)
entry=copy.deepcopy(parent);entry.update(runtime=str(rp),runtime_sha256=file_digest(rp),harness=harness,harness_sha256=revision)
campaign=copy.deepcopy(old);campaign.update(runtime=str(rp),runtime_sha256=file_digest(rp),entries=[entry],protocol=str(O/'protocol-v2.json'),protocol_sha256=file_digest(O/'protocol-v2.json'),instrumentation_revision=2)
atomic_json(C/'campaign.json',campaign)
atomic_json(C/'deployment-retry-authorization.json',dict(excluded_attempts=[dict(condition='logging_only',attempt=str(failed),classification='invalid_deployment',valid_native_cases=0,policy_zero_score=False,failed_sha256=file_digest(failed/'failed.json'),observed_sha256=file_digest(failed/'native/run/observed.json'),simulator_log_sha256=file_digest(failed/'native/processes/simulator/process.log'),repair=str(O/'instrumentation-repair-v2.json'),repair_sha256=file_digest(O/'instrumentation-repair-v2.json'))]))
atomic_json(O/'native-preparation/runtime-preflight-v2.json',check)
print(json.dumps(dict(state='prepared_v2',planned_cases=3,previous_invalid_native_cases=0)))
