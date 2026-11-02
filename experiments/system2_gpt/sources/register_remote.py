"""Stage one isolated System2 model swap; never edit prior experiment sources."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

R=Path('/mnt/data/physical-RSI')
OLD=R/'result/31_system2_final_validation_20261030T121000Z'
PRIOR=R/'result/29_system2_api_20261030T101800Z'
O=R/'result/38_system2_gpt61sol_20261102'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):Path(p).write_text(json.dumps(v,sort_keys=True,ensure_ascii=False,indent=2)+'\n')
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
assert not O.exists(), 'Reconcile existing supplement before retry'
assert not subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip()
old=read(OLD/'protocol.json')
for p,h in old['sources'].items():assert sha(p)==h,p
cfg=read(OLD/'runtime.json')
for p,h in cfg['files'].items():assert sha(p)==h,p
O.mkdir();S=O/'procedure-sources';S.mkdir()
for name in ['step5_scene_api_v4.py','step5_feedback.py']:
    shutil.copy2(OLD/'procedure-sources'/name,S/name)
cfg['policy_spec']['configuration']['output']=str(O/'primitive-services')
write(O/'runtime.json',cfg)
write(O/'workflow-configuration.json',read(OLD/'workflow-configuration.json'))
shutil.copy2(OLD/'historical-exclusions.json',O/'historical-exclusions.json')
body=read(PRIOR/'proposal-api/call-0001/request.json')
structured=read(OLD/'workspace/rounds/round-000000/proposals/classify_objects/request.json')
assert json.loads(body['messages'][1]['content'])==structured
shutil.copy2(PRIOR/'proposal-api/call-0001/request.json',O/'reference-chat-request.json')
shutil.copy2(OLD/'workspace/rounds/round-000000/proposals/classify_objects/request.json',O/'reference-structured-request.json')
fingerprint=dict(messages_sha256=digest(body['messages']),original_chat_sha256=sha(O/'reference-chat-request.json'),
    structured_request_sha256=sha(O/'reference-structured-request.json'),reference_model=body['model'],new_model='gpt-6.1-sol')
write(O/'reference-input-fingerprint.json',fingerprint)

driver=(OLD/'procedure-sources/step5_final_run.py').read_text()
driver=driver.replace("    atomic_json(R/'result/CURRENT_STEP5.json',dict(directory=str(O),**row))\n",'')
a=driver.index('    def cases(self, **kwargs):')
b=driver.index('\nclass Proposer(',a)
driver=driver[:a]+'''    def cases(self, **kwargs):
        split=kwargs['split']
        assert split in ['development','validation'] and kwargs['count']==5 and kwargs['tasks']==['classify_objects']
        source_round=OLD_W if split=='development' else Path(protocol['reference_validation_round'])
        rows=read_json(source_round/(split+'-cases.json'))
        shutil.copytree(source_round/(split+'-layouts'), kwargs['output'], copy_function=shutil.copy2, dirs_exist_ok=True)
        for case in rows:evidence.verify_case(case,Path(kwargs['output']))
        atomic_json(Path(kwargs['output'])/'reused-cohort.json',dict(source=str(source_round),
            split=split,reused_layout_metadata=True,new_native_resets=0,
            purpose='Frozen development input or matched historical validation layouts; not newly unseen geometry'))
        status('verified_frozen_'+split+'_cohort',count=len(rows),new_native_resets=0)
        return rows
''' + driver[b:]
a=driver.index('    def propose(self, *, feedback, output, **kwargs):')
b=driver.index('\nclass Task(',a)
driver=driver[:a]+'''    def propose(self, *, feedback, output, **kwargs):
        projected=project_feedback(feedback)
        reference=read_json(O/'reference-structured-request.json')
        def metrics(rows):return [{k:v for k,v in row.items() if k!='evidence_receipt'} for row in rows]
        assert metrics(projected)==metrics(reference['development_feedback'])
        assert kwargs['source']==reference['current_code'] and kwargs['memory']==reference['memory']
        assert kwargs['skill_api']==reference['primitive_api']
        atomic_json(output/'feedback-input-verification.json',dict(development_metrics_identical=True,
            current_code_identical=True,memory_identical=True,primitive_api_identical=True,
            reference_input_sha256=file_digest(O/'reference-structured-request.json'),
            provenance='Only artifact-location receipts were relocated in harness records; model receives exact original request'))
        return super().propose(feedback=reference['development_feedback'],output=output,**kwargs)
''' +driver[b:]
driver=driver.replace('copy_function=os.link','copy_function=shutil.copy2')
a=driver.index("private = read_json(Path('/home/ecs-user/.config/physicalrsi/agent.json'))")
b=driver.index('\nruntime=Runtime(configuration)',a)
driver=driver[:a]+'''profile=protocol['model_profile']
class PinnedConfig:
    def __init__(self):
        self.base=ModelConfig(model='gpt-6.1-sol',base_url='http://127.0.0.1:18776/v1',timeout_s=600)
    def __getattr__(self,key):return getattr(self.base,key)
    def public(self):
        value=self.base.public();value.pop('max_output_tokens')
        return dict(value,actual_transport_profile=profile,controller_sha256=file_digest(Path(__file__)))

def transport(suffix,body):
    assert suffix=='/chat/completions'
    original=read_json(O/'reference-chat-request.json')
    assert body['messages'][0]==original['messages'][0]
    assert json.loads(body['messages'][1]['content'])==json.loads(original['messages'][1]['content'])
    body=dict(original)
    body.pop('temperature');body.pop('enable_thinking')
    body.update(model='gpt-6.1-sol',reasoning_effort='medium',service_tier='default')
    assert body['messages']==original['messages'] and body['response_format']==original['response_format']
    assert not any(k in body for k in ['max_completion_tokens','max_tokens','tools'])
    dest=O/'proposal-api/call-0001'
    dest.mkdir(parents=True,exist_ok=False)
    atomic_json(dest/'request.json',body)
    atomic_json(dest/'input-check.json',dict(exact_original_messages=True,system_prompt_unchanged=True,
        user_content_byte_equal=True,no_output_limit_override=True,reference_chat_sha256=file_digest(O/'reference-chat-request.json'),
        changed_fields=['model','temperature removed','enable_thinking removed','reasoning_effort','service_tier']))
    raw=json.dumps(body).encode()
    atomic_json(dest/'started.json',dict(utc=stamp(),model='gpt-6.1-sol',request_sha256=__import__('hashlib').sha256(raw).hexdigest(),automatic_retry=False))
    status('calling_single_gpt_code_proposal')
    start=time.monotonic()
    req=urllib.request.Request('http://127.0.0.1:18776/v1/chat/completions',data=raw,
        headers={'Content-Type':'application/json','X-Experiment-Request-Id':O.name+'-proposal-1'})
    try:
        with urllib.request.urlopen(req,timeout=650) as response: result=json.load(response)
        atomic_json(dest/'response.json',result)
        atomic_json(dest/'completed.json',dict(utc=stamp(),elapsed_s=time.monotonic()-start,
            usage=result.get('usage'),finish_reason=result['choices'][0]['finish_reason'],http_attempts=1))
        assert result['model']=='gpt-6.1-sol'
        status('gpt_code_proposal_received',usage=result.get('usage'),finish_reason=result['choices'][0]['finish_reason'])
        return result
    except BaseException as error:
        atomic_json(dest/'failed.json',dict(utc=stamp(),elapsed_s=time.monotonic()-start,
            error_type=type(error).__name__,automatic_retry=False,check_local_budget_ledger=True))
        raise
''' +driver[b:]
a=driver.index("plan=read_json(R/'result/CURRENT_REPRODUCTION_PLAN.json')")
b=driver.index('# Verify the executed environment',a)
driver=driver[:a]+driver[b:]
driver=driver.replace('logical_total_rounds=2','logical_total_rounds=1')
driver=driver.replace('logical_round_index=1,rounds=rounds','logical_round_index=0,rounds=rounds')
driver=driver.replace("status('remaining_round_finished_awaiting_combined_audit',rounds_finished=len(rounds))",
    "status('complete',rounds_finished=len(rounds)); atomic_json(O/'completion.json',dict(complete=True,utc=stamp(),native_budget=read_json(O/'native-budget.json'),system2_rounds=1,new_proposals=1))")
driver=driver.replace("qualification='Scientific iterations finished; final evidence, lineage, usage and source audits still required'",
    "qualification='One GPT System2 model-swap pilot; verification and independent final-test claims require separate evidence'")
compile(driver,str(S/'system2_sol_run.py'),'exec')
(S/'system2_sol_run.py').write_text(driver)
protocol=dict(old)
protocol.update(schema='physicalrsi.system2-model-swap/v1',registered_utc=datetime.now(timezone.utc).isoformat(),
    maximum_rounds=1,logical_round_index=0,maximum_native_evaluations=10,proposal_http_attempts_maximum=1,
    expected_native_evaluations='Fresh parent 5 plus fresh GPT candidate 5 on the same frozen validation layouts',
    reference_validation_round=str(OLD/'workspace/rounds/round-000000'),
    original_reference_suite=str(OLD),new_model='gpt-6.1-sol',candidate_editing='No manual correction or extra feedback',
    prompt_input_fingerprint=fingerprint,
    model_profile=dict(model='gpt-6.1-sol',reasoning_effort='medium',service_tier='default',
        maximum_prompt_characters=100000,response_format={'type':'json_object'},output_limit_override=False,
        timeout_s=600,automatic_retries=0),
    budget=dict(cumulative_limit_usd=20,prior_upper_usd=.30173,client_reservation_per_request_usd=8,maximum_new_requests=1),
    configuration_sha256=sha(O/'runtime.json'),workflow_configuration_sha256=sha(O/'workflow-configuration.json'),
    historical_exclusions_sha256=sha(O/'historical-exclusions.json'),sources={str(p):sha(p) for p in S.glob('*.py')},
    allowed_changes=['Candidate generator model/provider/necessary compatible parameters','isolated output paths and provenance metadata'],
    held_constant=['exact original model messages','frozen development feedback','parent pi05','primitive API',
                   'local VLA and code implementations','five matched validation layouts','1100 steps','0.04s control interval','native scoring and selector'],
    exclusions=['feedback enhancement','manual candidate repair','directory changes','new VLA training','two complete new rounds','20-case independent final test'])
write(O/'protocol.json',protocol)
write(O/'controller-status.json',dict(stage='registered',complete=False,utc=protocol['registered_utc']))
shutil.copy2(Path(__file__),S/'register_remote.py')
print(json.dumps(dict(directory=str(O),ready_for_offline_preflight=True,fingerprint=fingerprint)))
