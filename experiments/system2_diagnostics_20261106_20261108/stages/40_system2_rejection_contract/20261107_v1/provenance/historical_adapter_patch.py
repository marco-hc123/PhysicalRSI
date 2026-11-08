"""Versioned repair of the documented no-path RuntimeError contract."""
from pathlib import Path
import hashlib, json, shutil
from datetime import datetime, timezone

R=Path('/mnt/data/physical-RSI');O=R/'result/25_system2_integration_20261030T050100Z'
S=O/'integration-sources';A=O/'attempt-05-planning-contract'
A.mkdir()
old=S/'framework-validation-v2';new=S/'framework-validation-v3'
shutil.copytree(old,new)
p=new/'PhysicalRSI_baselines/robodojo/code_execution.py';before=p.read_text()
anchor="""                if reply.get('id') == index:
                    return reply['value']"""
replacement="""                if reply.get('id') == index:
                    value = reply['value']
                    # Only a trusted, completed pre-action planner rejection is
                    # recoverable. Transport/partial-action failures still abort.
                    if isinstance(value, dict) and value.get('primitive_error') == 'no_collision_free_path':
                        raise RuntimeError('No collision-free path; no action executed by this call')
                    return value"""
assert before.count(anchor)==1;p.write_text(before.replace(anchor,replacement))
primitive=S/'step4_native_primitives_v3.py'
source=(S/'step4_native_primitives.py').read_text()
source=source.replace('class Backend:', 'class PlanningRejected(RuntimeError):\n    pass\n\nclass Backend:')
source=source.replace("raise RuntimeError('Released CuRobo found no path')", "raise PlanningRejected('Released CuRobo found no path')")
subclass='''class ContractPrimitives(RoboDojoPrimitives):
    def approach(self, *, arm, position_m, quaternion_wxyz):
        try:
            return super().approach(arm=arm, position_m=position_m, quaternion_wxyz=quaternion_wxyz)
        except PlanningRejected:
            # Raised exclusively by Backend.plan before a trajectory is returned,
            # so the parent approach has not issued a channel.step for this call.
            return dict(state=self._state(time.monotonic()+self.timeout_s),
                        action_steps=0, primitive_error='no_collision_free_path')
    def bindings(self, *, revision, actor):
        bindings=super().bindings(revision=revision, actor=actor)
        base=bindings['approach']['project_output']
        def project(result):
            value=base(result)
            if result.get('primitive_error') == 'no_collision_free_path':
                if result.get('action_steps') != 0:
                    raise ValueError('A partial action cannot be a recoverable planner rejection')
                value['primitive_error']='no_collision_free_path'
            return value
        bindings['approach']['project_output']=project
        return bindings

'''
source=source.replace('def assemble(',subclass+'def assemble(')
source=source.replace('return RoboDojoPrimitives(observe=', 'return ContractPrimitives(observe=')
primitive.write_text(source)

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

entry=S/'isolated-sim-entry-validation-v3.py'
entry.write_text((S/'isolated-sim-entry-validation-v2.py').read_text().replace(str(old),str(new)))
wrapper=S/'simulator-python-validation-v3'
wrapper.write_text((S/'simulator-python-validation-v2').read_text().replace(str(S/'isolated-sim-entry-validation-v2.py'),str(entry)))
wrapper.chmod(0o755)
replacements={str(old):str(new),str(S/'isolated-sim-entry-validation-v2.py'):str(entry),
    str(S/'simulator-python-validation-v2'):str(wrapper),str(S/'step4_native_primitives.py'):str(primitive),
    'step4_native_primitives:assemble':'step4_native_primitives_v3:assemble'}
def remap(value):
    if isinstance(value,str):
        for a,b in replacements.items():value=value.replace(a,b)
        return value
    if isinstance(value,list):return [remap(v) for v in value]
    if isinstance(value,dict):return {remap(k):remap(v) for k,v in value.items()}
    return value
v=remap(json.loads((O/'attempt-04-validation-recovery/runtime.json').read_text()))
for field in ['files','policy_files']:
    v[field]={k:sha(k) for k in v[field]}
v['policy_spec']['files']={k:sha(k) for k in v['policy_spec']['files']}
v['policy_spec']['configuration']['output']=str(A/'primitive-services')
(A/'runtime.json').write_text(json.dumps(v,sort_keys=True))
(A/'workflow-configuration.json').write_bytes((O/'workflow-configuration.json').read_bytes())
record=dict(utc=datetime.now(timezone.utc).isoformat(),
    scope='Step4 native integration adapter repair, not an optimization round or step5',
    diagnosis='Documented no-path RuntimeError was lost through RPC/mailbox, aborting native episode.',
    changed={str(p):sha(p),str(primitive):sha(primitive)},
    semantic_change='Return a completed zero-action planner rejection and re-raise RuntimeError inside isolated candidate so its existing handler works.',
    transport_partial_action_timeout_errors_remain_fatal=True, automatic_rpc_retries=0,
    original_framework_and_all_previous_sources_unchanged=True,
    protocol_amendment=dict(reason='Prior validation candidate interrupted by no-path contract violation.',
        additional_fresh_paired_validation_scenes=1, additional_parent_episodes=1, additional_candidate_episodes=1,
        max_generated_candidates=1,new_model_calls=0,new_development_episodes=0,
        previously_completed_parent_retained_as_separate_evidence_not_relabelled=True),
    qualifications=['Fresh independent compatibility validation after full metadata freeze.',
        'No path finding fallback, modified candidate, task/reward changes, or improvement claim.'])
(A/'binding-repair.json').write_text(json.dumps(record,sort_keys=True))

# Keep original recovery implementation immutable; run a corrected version in a
# new workspace, recording the extra integration-only validation budget first.
controller=(R/'result/step4_validation_recovery.py').read_text()
controller=controller.replace("A=O/'attempt-04-validation-recovery'", "A=O/'attempt-05-planning-contract'")
controller=controller.replace('evaluator_revision=digest(self.identity())','evaluator_revision=digest(prior)')
controller=controller.replace("prior=dict(files=prior_files", "prior_files[str(O/'attempt-04-validation-recovery/metadata-recovery/failed.json')]=file_digest(O/'attempt-04-validation-recovery/metadata-recovery/failed.json')\nprior=dict(files=prior_files")
anchor="""        status('generating_fresh_paired_validation')"""
controller=controller.replace(anchor,"""        excluded += [r['layout_sha256'] for r in read_json(O/'attempt-04-validation-recovery/workspace/rounds/round-000000/validation-cases.json')]
        status('generating_fresh_paired_validation')""")
(R/'result/step4_validation_recovery_v3.py').write_text(controller)
print(json.dumps(dict(attempt=str(A),framework=str(new),new_model_calls=0,
    additional_paired_validation_scenes=1,changed_files=2)))
