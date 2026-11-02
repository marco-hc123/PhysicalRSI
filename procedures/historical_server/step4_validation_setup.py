"""Versioned binding repair. Does not rerun development or call a model."""
from pathlib import Path
import hashlib
import json
import shutil
import os
R=Path('/mnt/data/physical-RSI');O=R/'result/25_system2_integration_20261030T050100Z'
A=O/'attempt-04-validation-recovery';A.mkdir()
S=O/'integration-sources';old=S/'framework';new=S/'framework-validation-v2'
shutil.copytree(old,new)
p=new/'PhysicalRSI_baselines/robodojo/deployment.py'
before=p.read_text()
anchor='''        self._initialize(
            current=dict(
                harness=frozen,'''
replacement='''        if expert is None:
            # Validation resolves only the exact frozen task selection; never a
            # mutable current pointer or caller-supplied validation override.
            expert = read_json(Path(frozen["root"]) / "skill_selection.json")["skill_choices"][task]
            if (expert["name"], expert["revision"]) not in factories:
                raise ValueError("Frozen validation primary factory unavailable")
        self._initialize(
            current=dict(
                harness=frozen,'''
assert before.count(anchor)==1
p.write_text(before.replace(anchor,replacement))
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
entry=S/'isolated-sim-entry-validation-v2.py'
entry.write_text((S/'isolated-sim-entry.py').read_text().replace(str(old),str(new)))
wrapper=S/'simulator-python-validation-v2'
wrapper.write_text((S/'simulator-python-v2').read_text().replace(str(S/'isolated-sim-entry.py'),str(entry)))
wrapper.chmod(0o755)
replacements={str(old):str(new),str(S/'isolated-sim-entry.py'):str(entry),str(S/'simulator-python-v2'):str(wrapper)}
def remap(x):
    if isinstance(x,str):
        for a,b in replacements.items():x=x.replace(a,b)
        return x
    if isinstance(x,list):return [remap(y) for y in x]
    if isinstance(x,dict):return {remap(k):remap(v) for k,v in x.items()}
    return x
v=remap(json.loads((O/'attempt-03/runtime.json').read_text()))
for field in ['files','policy_files']:
    v[field]={k:sha(k) for k in v[field]}
v['policy_spec']['files']={k:sha(k) for k in v['policy_spec']['files']}
(A/'runtime.json').write_text(json.dumps(v,sort_keys=True))
(A/'workflow-configuration.json').write_bytes((O/'workflow-configuration.json').read_bytes())
record=dict(scope='Versioned validation interface repair; previous development/proposal immutable',
    original=str(old/'PhysicalRSI_baselines/robodojo/deployment.py'),original_sha256=sha(old/'PhysicalRSI_baselines/robodojo/deployment.py'),
    repaired=str(p),repaired_sha256=sha(p),change='Read exact frozen task skill selection when validation has no development override',
    no_new_model_call=True,no_repeat_of_completed_development=True,validation_actions_before_repair=0,
    recovery='Re-freeze metadata for the compatible adapter; preserve exact generated policy bytes and memory. Official SelfHarness selection with actual fresh paired native validation.',
    formal_step5=False)
(A/'binding-repair.json').write_text(json.dumps(record,sort_keys=True))
print(json.dumps(record))
