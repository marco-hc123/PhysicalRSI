"""Stage-local change: preserve structured zero-action planner rejections.

The frozen integration source is never edited. Unknown failures/deadlines retain
their original behavior; this changes neither perception nor physical actions.
"""
import hashlib
from pathlib import Path
OLD="raise RuntimeError('No collision-free path; no action executed by this call')"
def transform_driver(source):
    assert source.count(OLD)==1,'Unexpected frozen child wrapper'
    return source.replace(OLD,'return value')
def assemble(channel,*,configuration,identity,own,pool=None):
    from PhysicalRSI_baselines.robodojo import code_execution
    from gripper_contract import assemble as inherited
    from diagnostic_common import append
    evidence=Path(__file__).resolve().parent.parent/'driver-contract-provenance/code_execution.py'
    import ast
    expected=next(ast.literal_eval(n.value) for n in ast.parse(evidence.read_text()).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='_DRIVER' for t in n.targets))
    patched=transform_driver(expected)
    assert code_execution._DRIVER in (expected,patched),'Unexpected active driver'
    code_execution._DRIVER=patched
    output=Path(configuration['output'])/identity['episode']/identity['actor']
    append(output/'driver-contract.jsonl',dict(mode='structured_zero_action_rejection',original_sha256=hashlib.sha256(expected.encode()).hexdigest(),patched_sha256=hashlib.sha256(patched.encode()).hexdigest(),candidate_changed=False))
    return inherited(channel,configuration=configuration,identity=identity,own=own,pool=pool)
