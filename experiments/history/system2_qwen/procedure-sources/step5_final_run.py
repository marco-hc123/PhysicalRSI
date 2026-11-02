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
    atomic_json(R/'result/CURRENT_STEP5.json',dict(directory=str(O),**row))
    print(json.dumps(row),flush=True)

class Runtime(NativeRuntime):
    def identity(self):
        return dict(super().identity(), campaign_adapter_sha256=file_digest(Path(__file__)),
            historical_exclusions_sha256=protocol['historical_exclusions_sha256'])

    def cases(self, **kwargs):
        status('generating_and_native_resetting_'+kwargs['split'], count=kwargs['count'])
        if ROUND == 0 and kwargs['split'] == 'development':
            assert kwargs['count'] == 5 and kwargs['tasks'] == ['classify_objects']
            rows = read_json(OLD_W/'development-cases.json')
            shutil.copytree(OLD_W/'development-layouts', kwargs['output'], copy_function=os.link, dirs_exist_ok=True)
            for case in rows:
                evidence.verify_case(case, Path(kwargs['output']))
            atomic_json(Path(kwargs['output'])/'reused-cohort.json', dict(
                source=str(OLD_W/'development-layouts'), reused=True, new_native_resets=0,
                original_case_manifest_sha256=file_digest(OLD_W/'development-cases.json')))
            status('verified_existing_development_cohort', reused_layouts=len(rows), new_native_resets=0)
            return rows
        rows = super().cases(**kwargs)
        path=O/'observed-layout-hashes.json'
        observed=read_json(path) if path.exists() else read_json(O/'historical-exclusions.json')['hashes']
        fresh=[row['layout_sha256'] for row in rows]
        assert len(fresh)==len(set(fresh)) and not set(fresh).intersection(observed), 'Reused geometry blocks dispatch'
        atomic_json(path, sorted(set(observed+fresh)))
        atomic_json(Path(kwargs['output'])/'global-exclusion-check.json',dict(
            passed=True,utc=stamp(),new_hashes=fresh,previous_hash_count=len(observed),
            original_exclusions_sha256=protocol['historical_exclusions_sha256']))
        return rows

class Proposer(CheckedCodeProposer):
    def identity(self):
        return dict(super().identity(), feedback_projection_sha256=file_digest(O/'procedure-sources/step5_feedback.py'),
            campaign_adapter_sha256=file_digest(Path(__file__)),model_feedback='all development metrics plus full-row evidence digest')

    def propose(self, *, feedback, output, **kwargs):
        projected=project_feedback(feedback)
        for original, compact in zip(feedback,projected):
            assert {k:v for k,v in original.items() if k!='evidence'} == {k:v for k,v in compact.items() if k!='evidence_receipt'}
        atomic_json(output/'feedback-projection.json',dict(utc=stamp(),raw_feedback_sha256=digest(feedback),
            projected_feedback_sha256=digest(projected),episodes=len(feedback),
            verified_artifacts=sum(len(row['evidence']) for row in feedback),
            raw_characters=len(json.dumps(feedback,ensure_ascii=False)),projected_characters=len(json.dumps(projected,ensure_ascii=False)),
            projection='Only replace verbose verified artifact inventory; retain every metric and native completion field',
            projection_implementation_sha256=file_digest(O/'procedure-sources/step5_feedback.py')))
        if ROUND == 0:
            completed = Path(protocol['completed_proposal']['directory'])
            previous = completed/'workspace/rounds/round-000001/proposals/classify_objects'
            request = read_json(previous/'request.json')
            def metrics(rows):
                return [{k:v for k,v in row.items() if k!='evidence_receipt'} for row in rows]
            assert metrics(request['development_feedback']) == metrics(projected)
            assert request['primitive_api'] == runtime.skill_api()
            response = read_json(completed/'proposal-api/call-0001/response.json')
            text = response['choices'][0]['message']['content']
            candidate = json.loads(text)
            atomic_json(output/'request.json', request)
            atomic_json(output/'response.json', dict(text=text,calls=[]))
            atomic_json(output/'completed-proposal-reuse.json', dict(
                original_directory=str(completed), original_request_sha256=file_digest(previous/'request.json'),
                actual_response_sha256=file_digest(completed/'proposal-api/call-0001/response.json'),
                source_sha256=digest(candidate['source']),memory_sha256=digest(candidate['memory']),
                development_metrics_unchanged=True, primitive_api_unchanged=True,
                new_http_attempts=0, original_http_attempts=1))
            status('checking_completed_model_proposal_against_native_contract')
            semantic_gate(candidate['source'],candidate['memory'],runtime=configuration['policy_spec']['runtime'],
                output=output/'cpu-contract-gate')
            return candidate
        return super().propose(feedback=projected,output=output,**kwargs)

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
            shutil.copytree(OLD_W/'development'/name, output, copy_function=os.link)
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

private = read_json(Path('/home/ecs-user/.config/physicalrsi/agent.json'))
assert private['model']=='qwen3.7-plus' and private['endpoint'].endswith('/chat/completions')
profile=protocol['model_profile']
class PinnedConfig:
    def __init__(self):
        self.base=ModelConfig(model=private['model'],base_url=private['endpoint'][:-len('/chat/completions')],timeout_s=600)
    def __getattr__(self,key):
        return getattr(self.base,key)
    def public(self):
        value=self.base.public();value.pop('max_output_tokens')
        return dict(value,actual_transport_profile=profile,controller_sha256=file_digest(Path(__file__)))

def transport(suffix, body):
    raise RuntimeError('No new HTTP: only the retained completed model response is permitted')
    assert suffix=='/chat/completions'
    body=dict(body);body.pop('max_completion_tokens',None);body.pop('tools',None)
    body.update(temperature=0,enable_thinking=True,response_format={'type':'json_object'})
    chars=sum(len(message.get('content','')) for message in body['messages'])
    assert chars<=profile['maximum_prompt_characters'], 'Input exceeds fixed preflight limit; no HTTP attempted'
    calls=O/'proposal-api';calls.mkdir(exist_ok=True)
    number=len(list(calls.glob('call-*')))+1
    assert number<=protocol['proposal_http_attempts_maximum']
    dest=calls/('call-%04d'%number);dest.mkdir()
    atomic_json(dest/'request.json',body)
    atomic_json(dest/'started.json',dict(utc=stamp(),round_index=ROUND,model=private['model'],retry=False,prompt_characters=chars))
    status('calling_code_proposal_api',call=number,prompt_characters=chars)
    start=time.monotonic()
    request=urllib.request.Request(private['endpoint'],data=json.dumps(body).encode(),method='POST',
        headers={'Authorization':'Bearer '+private['api_key'],'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(request,timeout=600) as response:
            result=json.loads(response.read())
        atomic_json(dest/'response.json',result)
        atomic_json(dest/'completed.json',dict(utc=stamp(),elapsed_s=time.monotonic()-start,
            usage=result.get('usage'),finish_reason=result['choices'][0]['finish_reason'],http_attempts=1))
        status('code_proposal_api_completed',call=number,usage=result.get('usage'))
        return result
    except BaseException as error:
        atomic_json(dest/'failed.json',dict(utc=stamp(),elapsed_s=time.monotonic()-start,
            error_type=type(error).__name__,retry=False,usage_unknown=True))
        raise RuntimeError('Code proposal HTTP failed; preserve uncertain call without retry') from None

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
atomic_json(O/'iteration-started.json',dict(utc=stamp(),pid=os.getpid(),rounds=protocol['maximum_rounds'],logical_total_rounds=2,native_evaluation_cap=protocol['maximum_native_evaluations'],
    controller_sha256=file_digest(Path(__file__)),protocol_sha256=file_digest(O/'protocol.json')))
plan=read_json(R/'result/CURRENT_REPRODUCTION_PLAN.json')
plan.update(updated_utc=stamp(),active_controller_pid=os.getpid(),current_controller_running=True,
    active_tmux_session='physicalrsi-step5-final',next_action='Complete the remaining second-round paired validation; audit both rounds and the explicit interface-inspection policy bridge')
plan['steps'][4]['state']='running final second-round validation; completed first round, second-round development and model response retained'
atomic_json(R/'result/CURRENT_REPRODUCTION_PLAN.json',plan)
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
    atomic_json(O/'iteration-result.json',dict(utc=stamp(),logical_round_index=1,rounds=rounds,elapsed_s=time.monotonic()-start,
        task_status=task.status(),native_budget=read_json(O/'native-budget.json'),
        qualification='Scientific iterations finished; final evidence, lineage, usage and source audits still required'))
    status('remaining_round_finished_awaiting_combined_audit',rounds_finished=len(rounds))
except BaseException as error:
    atomic_json(O/'iteration-failed.json',dict(utc=stamp(),round_index=ROUND,type=type(error).__name__,
        message=str(error),traceback=traceback.format_exc(),automatic_retry=False))
    status('formal_iteration_blocked',error_type=type(error).__name__,error=str(error))
    raise
