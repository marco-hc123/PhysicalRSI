"""Cloud-only registration and native reset qualification for System 2 integration."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shlex
import sys

ROOT = Path('/mnt/data/physical-RSI')
REPO = ROOT/'code/PhysicalRSI'
SIM = ROOT/'code/RoboDojo'
OUT = Path(sys.argv[1]).resolve()
OUT.mkdir(exist_ok=False)
SRC = OUT/'integration-sources'
SRC.mkdir()

def write(p, v):
    p.write_text(json.dumps(v, ensure_ascii=False, indent=2)+'\n')

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

freeze = ROOT/'result/23_protocol_freeze_20261029T132917Z'
f = json.loads((freeze/'source-freeze.json').read_text())
for p, h in f['recorded_protocol_and_framework_hashes'].items():
    assert sha(p) == h, p
for row in f['deployment_files']:
    assert sha(row['path']) == row['sha256'], row['path']

protocol = dict(schema='physicalrsi.system2-native-integration/v1',
    registered_utc=datetime.now(timezone.utc).isoformat(), authorized_step=4,
    task='classify_objects', scheme='hybrid', seed_parent='official workflow initial pi05 seed',
    goal='Qualify actual fresh-scene, pinned-model, isolated-candidate and SelfHarness lifecycle',
    integration_development_episodes=1, integration_validation_episodes=1,
    maximum_integration_rounds=1, minimum_vla_score=0.6,
    step_limit=1100, num_envs=1, control_dt_seconds=0.04,
    amendment='Separate small integration cohort; does not replace step5 registered 5+5 episode rounds or final test. No performance claim from this smoke cohort.',
    constraints=['Original source/weights/reward immutable', 'Fresh official config-derived scenes only',
                 'No heldout reuse', 'Preserve failures and extra setup costs',
                 'No unrestricted generated Python fallback', 'No step5 iterative campaign'],
    raw_retention='cloud_only', previous_freeze=str(freeze))
write(OUT/'protocol.json', protocol)
pythonpath = ':'.join(map(str,[SRC,REPO,SIM,SIM/'XPolicyLab']))
os.environ['PYTHONPATH'] = pythonpath
sys.path[:0] = [str(SRC),str(REPO),str(SIM),str(SIM/'XPolicyLab')]
from PhysicalRSI_baselines.robodojo import layouts, native_execution, native_preflight
from PhysicalRSI_core.infra.storage import digest

sim_wrapper=SRC/'simulator-python'
sim_wrapper.write_text('#!/usr/bin/env bash\nset -euo pipefail\nexport PYTHONPATH='+shlex.quote(pythonpath)+'\nexec /mnt/data/physical-RSI/envs/run-native-simulator.sh "$@"\n')
sim_wrapper.chmod(0o755)
environment=dict(PYTHONPATH=pythonpath, PYTHONDONTWRITEBYTECODE='1',
                 CUDA_VISIBLE_DEVICES='0', OMNI_KIT_ALLOW_ROOT='1')
write(OUT/'environment.json',environment)
write(OUT/'source-verification.json',dict(passed=True, deployment_files=len(f['deployment_files']),
    framework_dependencies=len(f['recorded_protocol_and_framework_hashes']), original_files_changed=0))
write(OUT/'controller-status.json',dict(stage='client_preflight',pid=os.getpid(),complete=False))
write(ROOT/'result/CURRENT_STEP4.json',dict(directory=str(OUT),complete=False,stage='client_preflight',pid=os.getpid()))
client = native_preflight.inspect_client(SIM,python=sim_wrapper,environment=environment,
    output=OUT/'client-preflight',timeout_s=90)
assert client['ready'], client
write(OUT/'controller-status.json',dict(stage='generating_initialization_scene',pid=os.getpid(),complete=False))
layouts.generate_batch(SIM,SIM/'Assets',OUT/'initialization-layouts',tasks=['classify_objects'],
    count=1,split='development',seed=2026103004,timeout_s=180,workers=1)
batch=layouts.verify_batch(OUT/'initialization-layouts/manifest.json',split='development')
rows=[dict(task=e['task'],split='development',file=e['file'],layout_sha256=e['content_sha256']) for e in batch['entries']]
write(OUT/'controller-status.json',dict(stage='native_reset_calibration',pid=os.getpid(),complete=False))
request=dict(simulator_root=str(SIM),assets_root=str(SIM/'Assets'),task='classify_objects',
    split='development',layouts=rows,layout_root=str(OUT/'initialization-layouts'),gpu=0,seed=0,
    policy_name='physicalRSI',camera_calibration=True,robot_calibration=True,port=1,endpoint='ws://127.0.0.1:1')
receipt=native_execution.initialize(request,python=sim_wrapper,environment=environment,
    output=OUT/'initialization',timeout_s=600)
write(OUT/'initialization-result.json',dict(receipt=str(receipt),scene_hashes=[r['layout_sha256'] for r in rows],
    physical_actions=0,scope='native reset and calibration only'))
write(OUT/'controller-status.json',dict(stage='initialization_complete',pid=os.getpid(),complete=False,
    initialization_receipt=str(receipt),utc=datetime.now(timezone.utc).isoformat()))
print(json.dumps(dict(directory=str(OUT),initialization_receipt=str(receipt))))
