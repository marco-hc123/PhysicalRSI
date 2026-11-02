from pathlib import Path
import shutil, hashlib, json, os, sys, shlex
R=Path('/mnt/data/physical-RSI'); O=R/'result/25_system2_integration_20261030T050100Z'; S=O/'integration-sources'; B=R/'code/PhysicalRSI'; D=R/'code/RoboDojo'; N=S/'native-simulator'; F=S/'framework'
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not N.exists() and not F.exists()
N.mkdir(); F.mkdir()
for name in ['env','env_cfg','src','task','utils']:
 shutil.copytree(D/name,N/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
for name in ['Assets','third_party']:(N/name).symlink_to(D/name,target_is_directory=True)
(N/'XPolicyLab/policy').mkdir(parents=True)
for parent in ['XPolicyLab','XPolicyLab/policy']:
 p=D/parent/'__init__.py'
 if p.exists():shutil.copy2(p,N/parent/'__init__.py')
for name in ['PhysicalRSI_baselines','PhysicalRSI_core','PhysicalRSI']:
 shutil.copytree(B/name,F/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc','XPolicyLab','build','.git'))
patches=[]
def change(path,a,b):
 old=path.read_text(); assert a in old, (path,a)
 path.write_text(old.replace(a,b)); patches.append(dict(file=str(path),original_sha256=hashlib.sha256(old.encode()).hexdigest(),sha256=sha(path),before=a,after=b))
change(N/'src/eval_client/main.py','AppLauncher(args_cli)','AppLauncher(args_cli, multi_gpu=False)')
for p in [N/'src/eval_client/main.py',N/'src/eval_client/eval_env.py']:
 change(p,'"eval_result",','os.environ.get("ROBODOJO_RESULT_ROOT", "eval_result"),')
# The released preflight accidentally aliases the policy-service verifier to the
# code-policy verifier. Keep distinct schema verifiers in this isolated copy.
p=F/'PhysicalRSI_baselines/robodojo/native_runtime.py'
change(p,'verify_policy = verify_policy_assembly\n','')
change(p,'verify_policy(self._assembly_spec())','verify_policy_assembly(self._assembly_spec())')
sys.path.insert(0,str(F))
from PhysicalRSI_baselines.robodojo.xpolicy_package import install
install(N,native_client=True)
pp=':'.join(map(str,[S,F,N,N/'XPolicyLab',D/'XPolicyLab']))
env=dict(PYTHONPATH=pp,PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='0',OMNI_KIT_ALLOW_ROOT='1')
wrapper=S/'simulator-python-v2'
# prepend isolated code after the original Isaac dependency launcher has set its paths
inner=S/'isolated-sim-entry.py'
inner.write_text('import sys,runpy\nsys.path[:0]='+repr([str(S),str(F),str(N),str(N/'XPolicyLab'),str(D/'XPolicyLab')])+'\nmodule=sys.argv[1];sys.argv=sys.argv[1:];runpy.run_module(module,run_name="__main__",alter_sys=True)\n')
wrapper.write_text('#!/usr/bin/env bash\nset -euo pipefail\nif [[ "$1" != "-m" ]]; then exit 64; fi\nshift\nexec /mnt/data/physical-RSI/envs/run-native-simulator.sh '+shlex.quote(str(inner))+' "$@"\n')
wrapper.chmod(0o755)
dump(O/'isolated-patches.json',dict(scope='Step4 isolated integration compatibility; original deployment unchanged',files=patches))
dump(O/'environment-v2.json',env)
dump(O/'client-preflight-failure.json',dict(state='failed_before_API_and_simulation',process=44334,returncode=1,reason='Original client lacks required native result-root and single-GPU adaptations',next='Isolated source variant preflight and native reset'))
dump(O/'controller-status.json',dict(stage='isolated_sources_prepared',complete=False,pid=os.getpid()))
print(json.dumps(dict(simulator=str(N),framework=str(F),wrapper=str(wrapper))))
