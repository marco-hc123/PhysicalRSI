"""Preserve the zero-outcome startup attempt; fix missing logging directory only."""
import json,shutil,sys,datetime
from pathlib import Path
O=Path(__file__).resolve().parent;I=O.parent/'25_system2_integration_20261030T050100Z/integration-sources'
sys.path[:0]=[str(I),str(I/'framework-validation-v3')]
from PhysicalRSI_core.infra.storage import atomic_json,read_json,file_digest
from PhysicalRSI_core.self_harness.artifacts import verify_harness
from PhysicalRSI_baselines.robodojo.native_runtime import NativeRuntime
from PhysicalRSI_baselines.robodojo.workflow import manifest
C=O/'native-campaign';campaign=read_json(C/'campaign.json');old=campaign['entries'][0]
A=C/'runs/structured_rejection/attempt-001';observed=read_json(A/'native/run/observed.json')
assert observed['outcomes']==[] and len(observed['failures'])==5
assert all('driver-contract.jsonl' in x and 'No such file or directory' in x for x in observed['failures'])
assert not list((A/'episodes').glob('*.json')) and not list(A.rglob('root/input.json'))
before=O/'code/structured_feedback.py';after=O/'code-v2/structured_feedback.py'
assert after.read_text()==before.read_text().replace("    append(output/'driver-contract.jsonl'","    output.mkdir(parents=True,exist_ok=True)\n    append(output/'driver-contract.jsonl'")
save=O/'deployment-attempt01';save.mkdir()
for p in [C/'campaign.json',C/'status.json',C/'controller-failure.json',O/'launch.json',O/'controller.log']:
    shutil.copy2(p,save/p.name)
cfg=read_json(old['runtime']);files={str(p):file_digest(p) for p in (O/'code-v2').glob('*.py')}
for k in ['files','policy_files']:cfg[k].update(files)
cfg['policy_spec']['files'].update(files)
for k in ['simulator_environment','policy_environment']:cfg[k]['PYTHONPATH']=str(O/'code-v2')+':'+cfg[k]['PYTHONPATH']
rp=O/'runtimes/structured_rejection_v2.json';atomic_json(rp,cfg);runtime=NativeRuntime(cfg)
target=C/'harnesses/structured_rejection_v2';shutil.copytree(Path(old['harness']['root']),target,symlinks=False);atomic_json(target/'assets.json',runtime.identity())
h=manifest(target,'rejection_contract_structured_v2');revision=verify_harness(h)
check=runtime.check();admit=runtime.admit(h,O/'native-preparation/admission-v2');assert check['ready'] and admit['accepted']
entry=dict(old,harness=h,harness_sha256=revision,runtime=str(rp),runtime_sha256=file_digest(rp))
campaign.update(entries=[entry],runtime=str(rp),runtime_sha256=file_digest(rp));atomic_json(C/'campaign.json',campaign)
repair=dict(state='verified_startup_repair',valid_native_cases=0,policy_zero_score=False,failed_setup_starts=5,reason='Diagnostic logging attempted before output directory existed; candidate never started',change='Create stage-local diagnostic output directory before append; driver transformation unchanged',original_sha256=file_digest(before),repaired_sha256=file_digest(after),check=check,admission=admit)
atomic_json(O/'deployment-repair-v2.json',repair)
row=dict(condition='structured_rejection',attempt=str(A),classification='invalid_deployment',valid_native_cases=0,policy_zero_score=False,failed_sha256=file_digest(A/'failed.json'),observed_sha256=file_digest(A/'native/run/observed.json'),simulator_log_sha256=file_digest(A/'native/processes/simulator/process.log'),repair=str(O/'deployment-repair-v2.json'),repair_sha256=file_digest(O/'deployment-repair-v2.json'))
atomic_json(C/'deployment-retry-authorization.json',dict(excluded_attempts=[row],reason='Within authorized autonomous deployment repair; preserve unsuccessful setup and exclude from scores'))
print(json.dumps(dict(state='prepared_v2',valid_native_cases_in_attempt01=0,planned_cases=5)))
