"""Freeze an honestly named released-controller reference, separate from System2."""
from pathlib import Path
import json,hashlib,datetime
R=Path('/mnt/data/physical-RSI');O=R/'result/38_candidate_capacity_20261107';P=R/'result/37_gripper_command_contract_20261107'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
cfg=read(P/'runtimes/measured_state_control.json');c=read(P/'native-campaign/campaign.json')
pkg=R/'models/skill-assets/implementations/code-skills/implementations/rdj_v1_classify_objects/6bb861ace4b706d9/rdj_v1_classify_objects'
files={str(p):sha(p) for p in pkg.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
revision=hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest()
spec=dict(name='released.classify_objects.6bb861ace4b706d9',revision=revision,files=files,camera=cfg['policy_spec']['configuration']['camera'],entrypoint='rdj_v1_classify_objects.model:Model')
dump(O/'reference-spec.json',spec)
protocol=dict(schema='physicalrsi.candidate-capacity/v1',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),question='Can the frozen complete released classification controller perform these same five exposed layouts, compared descriptively with the generated candidate?',planned_native_cases=5,api_calls=0,lab_gpu_used=False,layouts=c['cases'],layout_root=c['layout_root'],task='classify_objects',native_budget=1100,reference_spec_sha256=sha(O/'reference-spec.json'),reference_code_revision=revision,source_candidate_sha256='ff4f3438f43a1db92b5affebfcbe1147a1cda6f71ccfe0927558f84d0f10485a',decision='Reference skill competence check; no candidate promotion. Not a one-variable causal comparison: the complete controller changes perception use, motion and recovery together.',limits=['Reused development layouts, not independent generalization.','Same released Reader with the frozen head-camera ray and robot-mask calibration applied in both routes.','No simulator truth is available to the policy.','Symbolic coverage audit does not produce native scores or robot successes.','Failure of this reference does not establish a universal task or model capability limit.'],code_sha256={p.name:sha(p) for p in O.glob('*.py') if p.name in ['reference_service.py','run_reference.py','prepare_reference.py']})
dump(O/'protocol.json',protocol)
dump(O/'environment.json',dict(simulator_python=cfg['simulator_python'],simulator_environment=cfg['simulator_environment'],policy_python=cfg['policy_python'],policy_environment=cfg['policy_environment']))
req=read(next((P/'native-campaign/runs').rglob('native/request.json')))
req['expert']={'name':spec['name'],'revision':revision};req['harness_sha256']=sha(O/'protocol.json')
req.update(layouts=c['cases'],layout_root=c['layout_root'])
dump(O/'request-template.json',req)
print(json.dumps(dict(state='prepared',reference=spec['name'],files=len(files),native_cases=5)))
