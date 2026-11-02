"""Explicit metadata recovery; run only the missing frozen candidate episode.

Original controller and raw native receipts remain unchanged. The original
parent checkpoint is retained before deriving a corrected protocol-label field.
This is a recorded recovery, not an uninterrupted stock SelfHarness run.
"""
from pathlib import Path
from copy import deepcopy
import fcntl, json, os, sys, traceback

R = Path('/mnt/data/physical-RSI')
O = R / 'result/25_system2_integration_20261030T050100Z'
A = O / 'attempt-04-validation-recovery'
P = O / 'attempt-03/workspace/rounds/round-000000'
W = A / 'workspace/rounds/round-000000'
Q = A / 'metadata-recovery'
cfg = json.loads((A / 'runtime.json').read_text())
os.environ.update(cfg['policy_environment'])
sys.path[:0] = cfg['policy_environment']['PYTHONPATH'].split(':')
from PhysicalRSI_core.infra.storage import atomic_json, read_json, digest, file_digest
from PhysicalRSI_core.self_harness import now
from PhysicalRSI_core.self_harness.artifacts import verify_harness
from PhysicalRSI_baselines.robodojo.workflow import RoboDojoTask, Selector
from PhysicalRSI_baselines.robodojo.native_runtime import NativeRuntime
from PhysicalRSI_baselines.robodojo import evidence

assert os.geteuid() == 0
lock = (A / 'controller.lock').open('a')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
round_lock = (W / '.run.lock').open('a')
fcntl.flock(round_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
Q.mkdir(exist_ok=True)
assert not (Q / 'started.json').exists(), 'Reconcile prior recovery before retry'

def status(stage, **extra):
    row = dict(stage=stage, utc=now(), pid=os.getpid(), complete=False, **extra)
    atomic_json(Q / 'controller-status.json', row)
    atomic_json(R / 'result/CURRENT_STEP4.json', dict(directory=str(A), recovery=str(Q), **row))
    print(json.dumps(row), flush=True)

def completed(name):
    row = read_json(W / (name + '.json'))
    assert row['state'] == 'completed' and digest(row['output']) == row['output_sha256']
    return row['output']

status('verifying_completed_parent_and_frozen_candidate')
prior = read_json(A / 'prior-evidence-verification.json')
for path, sha in prior['files'].items():
    assert file_digest(Path(path)) == sha, path
protocol = read_json(W / 'config.json')
anchor = read_json(W / 'parent.json')
parent = anchor['harness']
child, = completed('propose')
comparison, cohort = completed('freeze'), completed('validation')
pool = [parent, child]
assert {h['id']: verify_harness(h) for h in pool} == comparison['candidates']
assert comparison['protocol_sha256'] == digest(protocol['protocol'])
assert cohort['comparison_sha256'] == digest(comparison)
assert cohort['generated_at'] > comparison['frozen_at']
assert file_digest(W / 'validation-cases.json') == cohort['admission_evidence']['validation-cases.json']
cases = read_json(W / 'validation-cases.json')
assert len(cases) == 1
assert not ({c['layout_sha256'] for c in cases} &
            {c['layout_sha256'] for c in read_json(P / 'development-cases.json')})
for c in cases:
    evidence.verify_case(c, W / 'validation-layouts')
for h in pool:
    assert completed('admit_' + h['id'])['accepted'] is True

original = W / 'evaluate_initial.json'
raw = read_json(original)
parent_result = completed('evaluate_initial')
assert parent_result['evaluator_revision'] == digest(protocol['identities']['evaluator'])
assert parent_result['evaluator_revision'] != protocol['protocol']['identity']
assert parent_result['cohort_sha256'] == digest(cohort)
for row in parent_result['episodes']:
    for path, sha in row['evidence_sha256'].items():
        assert file_digest(W / path) == sha
leaf = W / 'evaluation/initial/batch-000000'
native_path = leaf / 'episodes/0.json'
native = read_json(native_path)
evidence.episode_receipt(native_path, directory=leaf, task=native['task'], split='validation',
    layout_sha256=native['layout_sha256'], expert=dict(name=native['expert'], revision=native['revision']),
    harness_sha256=verify_harness(parent))
assert not (W / 'evaluate_candidate_recovered.json').exists()
assert not (W / 'evaluation/candidate_recovered').exists()

class ProvenanceOnly:
    def identity(self):
        return dict(original=read_json(P / 'proposals/classify_objects/skill-proposal.json')['proposer'],
                    recovery='reuse exact completed model proposal; never call a model', prior_sha256=digest(prior))

runtime = NativeRuntime(cfg)
task = RoboDojoTask(read_json(A / 'workflow-configuration.json'), A / 'workspace', runtime,
                   ProvenanceOnly(), rsi_plan={'scheme': 'hybrid'})
assert task.identity() == protocol['identities']['evaluator']['task']
check = runtime.check()
atomic_json(Q / 'runtime-preflight.json', check)
assert check['ready'], check
fixed = {str(p): file_digest(p) for p in [W / 'config.json', A / 'runtime.json',
         A / 'workflow-configuration.json', R / 'result/step4_validation_recovery.py', Path(__file__)]}

def stable():
    for path, sha in {**prior['files'], **fixed}.items():
        assert file_digest(Path(path)) == sha, path
    assert {h['id']: verify_harness(h) for h in pool} == comparison['candidates']
    assert task.identity() == protocol['identities']['evaluator']['task']

# Preserve the incorrect outer checkpoint, then derive only its protocol label.
saved_raw = Q / 'evaluate_initial.original.json'
saved_raw.write_bytes(original.read_bytes())
correction = dict(utc=now(), original_path=str(saved_raw), original_sha256=file_digest(saved_raw),
    script=str(Path(__file__)), script_sha256=file_digest(Path(__file__)),
    changed_output_field='evaluator_revision', before=parent_result['evaluator_revision'],
    after=protocol['protocol']['identity'], raw_native_receipts_unchanged=True,
    explanation='Adapter returned its implementation digest instead of the registered protocol identity.',
    new_parent_episodes=0, new_model_calls=0, candidate_policy_changes=0)
atomic_json(W / 'protocol-label-correction.json', correction)
corrected = deepcopy(raw)
corrected['output']['evaluator_revision'] = protocol['protocol']['identity']
assert {k: v for k, v in corrected['output'].items() if k != 'evaluator_revision'} == {
    k: v for k, v in raw['output'].items() if k != 'evaluator_revision'}
corrected['output_sha256'] = digest(corrected['output'])
corrected['metadata_recovery'] = dict(receipt='protocol-label-correction.json', utc=now())
atomic_json(original, corrected)
atomic_json(Q / 'started.json', dict(utc=now(), pid=os.getpid(), fixed=fixed, new_model_calls=0,
    completed_parent_reused=True, maximum_remaining_episodes=1))

try:
    stable()
    status('evaluating_only_missing_frozen_candidate', parent_success=native['success'],
           parent_score=native['episode_score'])
    inputs = dict(comparison=comparison, cohort=cohort, candidate=verify_harness(child))
    cp = W / 'evaluate_candidate_recovered.json'
    start = dict(state='started', input_sha256=digest(inputs), started_at=now(),
                 explicit_recovery_script_sha256=file_digest(Path(__file__)))
    atomic_json(cp, start)
    outcomes = task.execute_cases(child, cases, W / 'validation-layouts', W / 'evaluation' / child['id'])
    rows = []
    for case, result in zip(cases, outcomes):
        artifacts = {str(Path(p).relative_to(W)): sha for p, sha in result['evidence'].items()}
        artifacts['prior-evidence.json'] = file_digest(W / 'prior-evidence.json')
        artifacts['protocol-label-correction.json'] = file_digest(W / 'protocol-label-correction.json')
        rows.append(dict(task=case['task'], layout_sha256=case['layout_sha256'], state='completed',
                         score=result['episode_score'], success=result['success'], evidence_sha256=artifacts))
    candidate_result = dict(candidate_id=child['id'], kind='robodojo_episode_evaluation', native_exit_code=0,
        comparison_sha256=digest(comparison), cohort_sha256=digest(cohort), freeze_sha256=verify_harness(child),
        evaluator_revision=protocol['protocol']['identity'], episodes=rows)
    stable()
    atomic_json(cp, dict(start, state='completed', output=candidate_result,
                        output_sha256=digest(candidate_result), finished_at=now()))
    results = [completed('evaluate_' + h['id']) for h in pool]
    selector = Selector()
    decision = selector.select(comparison, cohort, results, evidence_root=W)
    atomic_json(W / 'selection.json', dict(state='completed', started_at=now(), finished_at=now(),
        input_sha256=digest(dict(comparison=comparison, cohort=cohort, results=results)),
        output=decision, output_sha256=digest(decision)))
    retained = {str(p): file_digest(p) for p in W.rglob('*.json') if p.name != 'commit.json'}
    retained[str(saved_raw)] = file_digest(saved_raw)
    retained.update(fixed)
    for result in results:
        for episode in result['episodes']:
            for path, sha in episode['evidence_sha256'].items():
                assert file_digest(W / path) == sha
                retained[str(W / path)] = sha
    survivor = next(h for h in pool if h['id'] == decision['survivor_id'])
    committed = task.state.commit(anchor['revision'], survivor, evidence=retained, decision=decision,
                                  selector=selector, comparison_root=W)
    atomic_json(W / 'commit.json', committed)
    atomic_json(A / 'iteration-result.json', dict(utc=now(), result=committed, task_status=task.status(),
        qualification='Native integration, completed through recorded binding and protocol-label recovery; not a formal improvement campaign'))
    status('paired_validation_and_lineage_committed', action=committed['action'], revision=committed['revision'],
           decision=decision)
except BaseException as error:
    atomic_json(Q / 'failed.json', dict(utc=now(), type=type(error).__name__, message=str(error),
        traceback=traceback.format_exc(), automatic_retry=False))
    status('explicit_metadata_recovery_failed', error_type=type(error).__name__, error=str(error))
    raise
