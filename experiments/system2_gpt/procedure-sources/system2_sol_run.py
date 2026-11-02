"""Two actual fifth-step System2 iterations, no implicit replay after interruption."""
from pathlib import Path
from datetime import datetime, timezone
import fcntl
import shutil
from copy import deepcopy
import json
import os
import sys
import time
import traceback
import urllib.request

R = Path('/mnt/data/physical-RSI')
O = Path(sys.argv[1]).resolve()
configuration = json.loads((O/'runtime.json').read_text())
os.environ.update(configuration['policy_environment'])
sys.path[:0] = [str(O/'procedure-sources'), *configuration['policy_environment']['PYTHONPATH'].split(':')]
from PhysicalRSI_core.infra.storage import atomic_json, file_digest, digest, read_json
from PhysicalRSI_core.infra.language import LanguageModel, ModelConfig
from PhysicalRSI_baselines.robodojo.native_runtime import NativeRuntime
from step5_scene_api_v4 import CheckedCodeProposer, semantic_gate
from PhysicalRSI_baselines.robodojo import evidence
from PhysicalRSI_baselines.robodojo.workflow import RoboDojoTask
from step5_feedback import project_feedback

protocol = read_json(O/'protocol.json')
assert file_digest(O/'runtime.json') == protocol['configuration_sha256']
assert file_digest(O/'workflow-configuration.json') == protocol['workflow_configuration_sha256']
for name, sha in protocol['sources'].items():
    assert file_digest(Path(name)) == sha, name
assert file_digest(O/'historical-exclusions.json') == protocol['historical_exclusions_sha256']

def stamp():
    return datetime.now(timezone.utc).isoformat()

PRIOR = Path(protocol["reuse_development"]["directory"])
OLD_W = PRIOR/"workspace/rounds/round-000001"
ROUND = None
def status(stage, **extra):
    row = dict(stage=stage,pid=os.getpid(),utc=stamp(),complete=False,round_index=ROUND,**extra)
    atomic_json(O/'controller-status.json', row)
    print(json.dumps(row),flush=True)

class Runtime(NativeRuntime):
    def identity(self):
        return dict(super().identity(), campaign_adapter_sha256=file_digest(Path(__file__)),
            historical_exclusions_sha256=protocol['historical_exclusions_sha256'])

    def cases(self, **kwargs):
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

class Proposer(CheckedCodeProposer):
    def identity(self):
        return dict(super().identity(), feedback_projection_sha256=file_digest(O/'procedure-sources/step5_feedback.py'),
            campaign_adapter_sha256=file_digest(Path(__file__)),model_feedback='all development metrics plus full-row evidence digest')

    def propose(self, *, feedback, output, **kwargs):
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

class Task(RoboDojoTask):
    def _seed(self):
        selected = read_json(Path(protocol['selected_parent_commit']))
        from PhysicalRSI_core.self_harness.artifacts import verify_harness
        from PhysicalRSI_baselines.robodojo.workflow import manifest
        assert verify_harness(selected['harness']) == protocol['selected_parent_freeze_sha256']
        root = self.root/'seed'
        if not root.exists():
            shutil.copytree(selected['harness']['root'], root)
            atomic_json(root/'assets.json', self.runtime.identity())
            atomic_json(root/'prompts.json', {'proposal': self.code_proposer.identity()})
            atomic_json(root/'dependencies.json', self.identity())
        rebound = manifest(root, selected['harness']['id'])
        changed = {key for key in rebound['components'] if rebound['components'][key] != selected['harness']['components'][key]}
        assert changed == {'assets', 'prompts', 'dependencies'}, changed
        assert read_json(root/'assets.json') == self.runtime.identity()
        return rebound

    def execute_cases(self, harness, cases, cohort_root, output, *, expert=None):
        if ROUND == 0 and cases and cases[0]['split'] == 'development':
            assert expert and expert['name'] in {'pi05', 'pi05-sparse-memory'}
            name = expert['name']
            original_rows = [row for row in read_json(OLD_W/'development-results.json') if row['expert'] == name]
            assert len(original_rows) == len(cases) == 5
            assert [row['layout_sha256'] for row in original_rows] == [case['layout_sha256'] for case in cases]
            for index, row in enumerate(original_rows):
                leaf = OLD_W/'development'/name/('batch-%06d'%index)
                receipt = read_json(leaf/'episodes/0.json')
                checked = evidence.episode_receipt(leaf/'episodes/0.json', directory=leaf,
                    task=row['task'], split='development', layout_sha256=row['layout_sha256'],
                    expert=expert, harness_sha256=receipt['harness_sha256'])
                assert checked == row
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(OLD_W/'development'/name, output, copy_function=shutil.copy2)
            results = deepcopy(original_rows)
            round_root = Path(output).parent.parent
            for row in results:
                row['evidence'] = {str(round_root/Path(p).relative_to(OLD_W)): sha for p, sha in row['evidence'].items()}
                for p, sha in row['evidence'].items():
                    assert file_digest(Path(p)) == sha
            reused = O/'reused-development'
            reused.mkdir(exist_ok=True)
            atomic_json(reused/(name+'.json'), dict(verified=True, episodes=5, new_native_episodes=0,
                source_results=str(OLD_W/'development-results.json'), original_rows_sha256=digest(original_rows),
                ported_rows_sha256=digest(results), native_receipts_keep_original_harness_identity=True,
                current_parent_binding='Only public API documentation/output destination changed; physics, VLA weights, perception and control unchanged'))
            status('existing_development_evidence_reused', expert=name, episodes=5, new_native_episodes=0)
            return results
        return super().execute_cases(harness, cases, cohort_root, output, expert=expert)

    def execute_batch(self, harness, cases, cohort_root, output, *, expert=None):
        ledger_path=O/'native-budget.json'
        ledger=read_json(ledger_path) if ledger_path.exists() else dict(maximum=protocol['maximum_native_evaluations'],requested=0,completed=0,batches=[])
        assert ledger['requested']+len(cases)<=ledger['maximum'], 'Stop before native evaluation cap'
        entry=dict(index=len(ledger['batches']),requested_utc=stamp(),count=len(cases),
            split=cases[0]['split'],expert=expert,harness_id=harness['id'],output=str(output),state='started')
        ledger['requested']+=len(cases)
        ledger['batches'].append(entry)
        atomic_json(ledger_path,ledger)
        status('native_batch_running',native_requested=ledger['requested'],native_completed=ledger['completed'],
            split=cases[0]['split'],expert=expert,harness_id=harness['id'],output=str(output))
        results=super().execute_batch(harness,cases,cohort_root,output,expert=expert)
        assert len(results)==len(cases)
        ledger['completed']+=len(results)
        entry.update(state='completed',finished_utc=stamp(),scores=[r['episode_score'] for r in results],
                     successes=[r['success'] for r in results])
        atomic_json(ledger_path,ledger)
        status('native_batch_completed',native_requested=ledger['requested'],native_completed=ledger['completed'],
            scores=entry['scores'],successes=entry['successes'],output=str(output))
        return results

profile=protocol['model_profile']
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

runtime=Runtime(configuration)
task=Task(read_json(O/'workflow-configuration.json'),O/'workspace',runtime,
    Proposer(LanguageModel(PinnedConfig(),transport=transport), isolation_runtime=configuration['policy_spec']['runtime']),rsi_plan={'scheme':'hybrid'})
if '--preflight' in sys.argv:
    report=runtime.check();assert report['ready'], report
    sample=[dict(task='classify_objects',split='development',state='completed',natural_terminal=True,
        episode_score=0.0,success=False,expert='pi05',revision='test',layout_sha256='0'*64,
        diagnostics={'action_count':1100,'step_limit':1100},evidence={'retained-example':'a'*64})]
    projected=project_feedback(sample)
    assert projected[0]['episode_score']==0 and projected[0]['success'] is False
    try:
        project_feedback([dict(sample[0],split='validation')])
    except ValueError:
        pass
    else:
        raise AssertionError('Validation feedback must be rejected')
    admission=runtime.admit(task._seed(),O/'offline-parent-admission');assert admission['accepted'],admission
    a=digest(task.identity());b=digest(task.identity());assert a==b
    atomic_json(O/'offline-preflight.json',dict(utc=stamp(),passed=True,runtime=report,
        task_identity_sha256=a,projection_metrics_preserved=True,validation_feedback_rejected=True,
        model_http_attempts=0,native_episodes=0,protocol_sha256=file_digest(O/'protocol.json')))
    print(json.dumps(dict(preflight=True,ready=True,task_identity_sha256=a)))
    sys.exit(0)

lock=(O/'controller.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert os.geteuid()==0
assert read_json(O/'offline-preflight.json')['passed']
assert not (O/'iteration-started.json').exists(), 'Reconcile all actual evidence before any recovery; no automatic resume'
atomic_json(O/'iteration-started.json',dict(utc=stamp(),pid=os.getpid(),rounds=protocol['maximum_rounds'],logical_total_rounds=1,native_evaluation_cap=protocol['maximum_native_evaluations'],
    controller_sha256=file_digest(Path(__file__)),protocol_sha256=file_digest(O/'protocol.json')))
# Verify the executed environment has only the registered non-physical changes.
old_cfg = read_json(PRIOR/'runtime.json')
# Compare copies, never alter live runtime configuration.
a, b = deepcopy(old_cfg), deepcopy(configuration)
for cfg in [a, b]:
    cfg.pop('skill_api')
    cfg['policy_spec']['configuration'].pop('output')
assert a == b, 'Development evidence reuse requires identical native execution settings'
for p, sha in dict(protocol['reuse_development']['files'], **protocol['completed_proposal']['files']).items():
    assert file_digest(Path(p)) == sha, p
start=time.monotonic();rounds=[]
try:
    for ROUND in range(protocol['maximum_rounds']):
        status('formal_round_started')
        began=time.monotonic()
        result=task.evolve()
        row=dict(index=ROUND,finished_utc=stamp(),elapsed_s=time.monotonic()-began,result=result,task_status=task.status())
        rounds.append(row)
        atomic_json(O/('round-%02d-result.json'%ROUND),row)
        status('formal_round_committed',result=result)
    atomic_json(O/'iteration-result.json',dict(utc=stamp(),logical_round_index=0,rounds=rounds,elapsed_s=time.monotonic()-start,
        task_status=task.status(),native_budget=read_json(O/'native-budget.json'),
        qualification='One GPT System2 model-swap pilot; verification and independent final-test claims require separate evidence'))
    status('complete',rounds_finished=len(rounds)); atomic_json(O/'completion.json',dict(complete=True,utc=stamp(),native_budget=read_json(O/'native-budget.json'),system2_rounds=1,new_proposals=1))
except BaseException as error:
    atomic_json(O/'iteration-failed.json',dict(utc=stamp(),round_index=ROUND,type=type(error).__name__,
        message=str(error),traceback=traceback.format_exc(),automatic_retry=False))
    status('formal_iteration_blocked',error_type=type(error).__name__,error=str(error))
    raise
