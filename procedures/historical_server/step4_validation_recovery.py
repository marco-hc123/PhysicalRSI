"""Finish a blocked integration with immutable prior evidence and no new proposal.

This explicit recovery port re-freezes adapter metadata only. It preserves the
actual Qwen policy and memory byte-for-byte and uses the official SelfHarness,
native evidence verifier and survivor selector for fresh paired validation.
"""
from pathlib import Path
from datetime import datetime,timezone
from copy import deepcopy
import fcntl,json,os,shutil,sys,traceback
R=Path('/mnt/data/physical-RSI');O=R/'result/25_system2_integration_20261030T050100Z'
P=O/'attempt-03';A=O/'attempt-04-validation-recovery'
cfg=json.loads((A/'runtime.json').read_text());os.environ.update(cfg['policy_environment']);sys.path[:0]=cfg['policy_environment']['PYTHONPATH'].split(':')
from PhysicalRSI_core.infra.storage import atomic_json,file_digest,digest,read_json
from PhysicalRSI_core.self_harness import SelfHarness,now
from PhysicalRSI_core.self_harness.artifacts import verify_harness
from PhysicalRSI_baselines.robodojo.native_runtime import NativeRuntime
from PhysicalRSI_baselines.robodojo.workflow import RoboDojoTask,Evaluation,Selector,manifest
from PhysicalRSI_baselines.robodojo import evidence

lock=(A/'controller.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert os.geteuid()==0 and not (A/'started.json').exists()
def status(stage,**extra):
    v=dict(stage=stage,pid=os.getpid(),utc=now(),complete=False,**extra)
    atomic_json(A/'controller-status.json',v);atomic_json(R/'result/CURRENT_STEP4.json',dict(directory=str(A),**v));print(json.dumps(v),flush=True)
status('verifying_prior_evidence_and_binding_repair')
old=P/'workspace/rounds/round-000000';old_parent=read_json(old/'parent.json')['harness'];old_child=read_json(old/'propose.json')['output'][0]
verify_harness(old_parent);verify_harness(old_child)
prior_files={str(p):file_digest(p) for p in [old/'parent.json',old/'propose.json',old/'development-results.json',old/'development-cases.json',P/'proposal-api/call-0001/request.json',P/'proposal-api/call-0001/response.json',P/'proposal-api/call-0001/completed.json',A/'binding-repair.json',Path(__file__)]}
for name in ['pi05','pi05-sparse-memory']:
    root=old/'development'/name/'batch-000000';p=root/'episodes/0.json';v=read_json(p)
    evidence.episode_receipt(p,directory=root,task=v['task'],split='development',layout_sha256=v['layout_sha256'],expert=dict(name=v['expert'],revision=v['revision']),harness_sha256=v['harness_sha256'])
    prior_files[str(p)]=file_digest(p)
prior=dict(files=prior_files,original_parent_sha256=verify_harness(old_parent),original_candidate_sha256=verify_harness(old_child),
    actual_model='qwen3.7-plus',actual_proposal_http_attempts=1,new_http_attempts=0,
    scope='Compatible validation-binding recovery, not an additional optimization round')
atomic_json(A/'prior-evidence-verification.json',prior)
runtime=NativeRuntime(cfg);check=runtime.check();atomic_json(A/'runtime-preflight.json',check);assert check['ready'],check

class ProvenanceOnly:
    def identity(self):
        return dict(original=read_json(old/'proposals/classify_objects/skill-proposal.json')['proposer'],
                    recovery='reuse exact completed model proposal; never call a model',prior_sha256=digest(prior))

task=RoboDojoTask(read_json(A/'workflow-configuration.json'),A/'workspace',runtime,ProvenanceOnly(),rsi_plan={'scheme':'hybrid'})

class RecoveredProposal:
    def identity(self):
        for p,sha in prior_files.items():
            if file_digest(Path(p))!=sha:raise ValueError('Prior completed evidence changed')
        return dict(kind='explicit_completed_proposal_recovery',prior=digest(prior),task=task.identity(),implementation=file_digest(Path(__file__)))
    def develop(self,parent,output):
        atomic_json(output/'prior-evidence.json',prior)
        return dict(split='evolve',evidence={'prior-evidence.json':file_digest(output/'prior-evidence.json')},
                    costs={'new_episodes':0,'verified_reused_development_episodes':2})
    def propose(self,parent,feedback,output):
        child=output/'candidate';shutil.copytree(Path(parent['root']),child)
        original=Path(old_child['root']);skills=read_json(original/'skills.json')
        for name in ['skills.json','skill_selection.json','memory_rules.json']:
            (child/name).write_bytes((original/name).read_bytes())
        for skill in skills.values():
            p=Path(skill['source']);(child/p).parent.mkdir(parents=True,exist_ok=True)
            (child/p).write_bytes((original/p).read_bytes());assert file_digest(child/p)==skill['revision']
        atomic_json(output/'candidate-content-preservation.json',dict(
            sources={s['source']:file_digest(child/s['source']) for s in skills.values()},
            source_matches_actual_model_response=True,
            memory_rules_sha256=file_digest(child/'memory_rules.json'),
            memory_matches_prior_candidate=file_digest(child/'memory_rules.json')==file_digest(original/'memory_rules.json'),
            metadata_refrozen_for_binding_repair=True))
        return [manifest(child,'candidate_recovered',parent_sha256=verify_harness(parent),
            method='actual_qwen_proposal_recovered_after_validation_binding_fix',
            changes={'skill_selection':'exact prior model-generated code and memory'},environment=runtime.identity(),
            evidence=feedback['evidence'],costs={'new_http':0,'original_http':1,'original_development_episodes':2})]

class PairedEvaluation(Evaluation):
    def identity(self):return dict(task=task.identity(),recovery=file_digest(Path(__file__)),prior=digest(prior))
    def validation(self,comparison,output):
        excluded=[r['layout_sha256'] for r in read_json(old/'development-cases.json')]
        # Failed prior validation startup had no actions; still exclude its scene.
        if (old/'validation-cases.json').exists():excluded += [r['layout_sha256'] for r in read_json(old/'validation-cases.json')]
        status('generating_fresh_paired_validation')
        cases=evidence.cases(runtime,tasks=task.tasks,count=1,split='validation',output=output/'validation-layouts',comparison=comparison,excluded=excluded)
        atomic_json(output/'validation-cases.json',cases)
        return dict(split='validation',comparison_sha256=digest(comparison),generated_at=now(),
            layouts={name:[r['layout_sha256'] for r in cases if r['task']==name] for name in task.tasks},
            admission_evidence={'validation-cases.json':file_digest(output/'validation-cases.json')})
    def evaluate(self,candidate,comparison,cohort,output):
        assert file_digest(output/'validation-cases.json')==cohort['admission_evidence']['validation-cases.json']
        status('evaluating_frozen_validation_policy',candidate=candidate['id'])
        cases=read_json(output/'validation-cases.json')
        results=task.execute_cases(candidate,cases,output/'validation-layouts',output/'evaluation'/candidate['id'])
        rows=[]
        for case,result in zip(cases,results):
            artifacts={str(Path(p).relative_to(output)):sha for p,sha in result['evidence'].items()}
            artifacts['prior-evidence.json']=file_digest(output/'prior-evidence.json')
            rows.append(dict(task=case['task'],layout_sha256=case['layout_sha256'],state='completed',
                score=result['episode_score'],success=result['success'],evidence_sha256=artifacts))
        return dict(candidate_id=candidate['id'],kind='robodojo_episode_evaluation',native_exit_code=0,
            comparison_sha256=digest(comparison),cohort_sha256=digest(cohort),freeze_sha256=verify_harness(candidate),
            evaluator_revision=digest(self.identity()),episodes=rows)

round_root=A/'workspace/rounds/round-000000'
profile=dict(tasks={'classify_objects':dict(weight=1,episodes=1,score_range=[0,1],maximum_regression=0)},minimum_gain=0,tie_tolerance=1e-10)
loop=SelfHarness(round_root,state=task.state,proposer=RecoveredProposal(),evaluator=PairedEvaluation(task),selector=Selector(),
    profile=profile,protocol=dict(identity=digest(prior),evaluation_kind='robodojo_episode_evaluation',
        recovery='Exact completed proposal; explicit adapter metadata re-freeze, no new development/model call'),
    scope=runtime.identity()['scope'],max_candidates=1)
task.state.initialize(task._seed(),policy=loop.config,scope=loop.config['scope'])
atomic_json(A/'started.json',dict(utc=now(),pid=os.getpid(),prior=digest(prior),new_model_calls=0,maximum_candidates=1))
try:
    status('recovered_one_iteration_running')
    result=loop.run()
    atomic_json(A/'iteration-result.json',dict(utc=now(),result=result,task_status=task.status(),
        qualification='Native integration with an explicit compatibility recovery; not a formal improvement campaign'))
    status('recovered_one_iteration_finished',action=result['action'],revision=result['revision'])
except BaseException as error:
    atomic_json(A/'iteration-failed.json',dict(utc=now(),type=type(error).__name__,message=str(error),traceback=traceback.format_exc(),automatic_retry=False))
    status('recovered_one_iteration_failed',error_type=type(error).__name__,error=str(error));raise
