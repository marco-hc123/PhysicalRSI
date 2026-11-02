"""Freeze a bounded developmental catalogue-ablation protocol before dispatch."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from cloud_catalogue_common import sha256, write_json

root = Path('/mnt/data/physical-RSI')
result = root/'result'
prior = result/'18_experiment_suite_20261029T020602Z'
pointer = result/'CURRENT_CATALOGUE_STUDY.json'
assert not pointer.exists(), 'Existing catalogue study must be reconciled before a new launch'
gpu = subprocess.check_output(['nvidia-smi','--query-gpu=memory.used','--format=csv,noheader,nounits'],text=True).strip()
assert int(gpu) == 0, 'Expected idle GPU before preparing this new suite'
name = '19_catalogue_ablation_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
suite = result/name
suite.mkdir(exist_ok=False)
jobs = []
for repeat in range(1,4):
    for index,layout in enumerate(range(1,6)):
        order = ['projected','unprojected'] if (index+repeat-1)%2 == 0 else ['unprojected','projected']
        for condition in order:
            jobs.append(dict(name=f'r{repeat}_layout{layout:02d}_{condition}',condition=condition,layout=layout,
                             repeat=repeat,pair_id=f'r{repeat}_layout{layout:02d}',phase='pilot' if repeat==1 else 'repeat'))
protocol = dict(schema='physicalrsi.catalogue-ablation/v1',registered_utc=datetime.now(timezone.utc).isoformat(),
    task='general_pickup',layouts=[1,2,3,4,5],conditions=['projected','unprojected'],native_repetitions=3,
    native_cases=30,replay_cases=10,model='qwen3.7-plus',enable_thinking=True,temperature=0,
    max_tokens='Keep frozen planner/provider default; no new output limit',seed=0,step_limit=200,
    planner_sha256='d6f6936d5b57283c7c8affacd857356f9b1e8f8d5f54a7b6959a4e70c1cb25db',
    sole_treatment='Official _planner_catalogue projection vs identity/deepcopy, for available_compositions and operation_program only',
    selection_rule='First five numeric layouts used in prior suite, fixed before new outcomes; no success-based selection',
    scope='Developmental mechanism pilot and repeated same-layout evaluation; not independent held-out generalization',
    primary_metrics=['Native success per attempted case','Provider prompt and total tokens per attempted case'],
    secondary_metrics=['Strict plan validity','Selected skill','Cached/reasoning subsets','API latency','Native execution time','Cold startup'],
    failure_rule='Keep planning and execution failures in denominator; do not remap or retry semantic failures; preserve native transport retry policy up to3 with full ledger; infrastructure failure pauses controller for review',
    attempt_budget=dict(max_native_logical_plans=30,max_replay_logical_plans=10,max_transport_attempts_per_plan=3,max_total_transport_attempts=120),
    continuation_gate='After first10 cases, verify no infrastructure faults and unchanged sources, then execute two declared repeats irrespective of success direction',
    interpretation_notes=[
        'Full projection-off restores static implementation/source labels and operation stages; effect is not pure byte compression.',
        'Both VLA checkpoints and all22 operations remain available for both conditions.',
        'Same layout/seed/robot reset does not guarantee pixel-identical independently rendered RGB.',
        'Five layouts are the sampling units; repeats do not constitute15 independent layouts.',
        'Thinking was selected after prior exploration; this is a new developmental comparison.',
        'No online learning, System2 skill evolution, or comparison to an external project is included.',
        'Existing earlier 59-case suite remains immutable.'
    ],jobs=jobs)
write_json(suite/'protocol.json',protocol)
runtime = root/'code/RoboDojo/XPolicyLab/policy/physicalRSI/runtime'
files = []
for package in ['PhysicalRSI','PhysicalRSI_baselines','PhysicalRSI_core']:
    for pattern in ['*.py','*.json']:
        files.extend((runtime/package).rglob(pattern))
files += list(result.glob('cloud_catalogue_*.py'))
code_skills=root/'models/skill-assets/implementations/code-skills'
for pattern in ['*.py','*.json']:
    files.extend(p for p in code_skills.rglob(pattern) if '.git' not in p.parts)
files += [root/'models/skill-assets/assets.json',root/'models/skill-assets/assets.provenance.json']
for layout in range(1,6):
    request_path=prior/'new_layouts_agent/api'/f'call-{layout:03d}-request.json'
    files.append(request_path)
    document=json.loads(request_path.read_text())
    for message in document['messages']:
        if not isinstance(message['content'],list): continue
        for part in message['content']:
            if part['type']=='image_url': files.append(request_path.parent/part['image_url']['artifact'])
files += [result/'cloud_native_subset.py',prior/'new_layouts_agent/skills.json',root/'envs/run-native-simulator.sh']
for rel in ['src/eval_client/main.py','env/seed_manager/seed_manager.py','XPolicyLab/policy/physicalRSI/model.py','XPolicyLab/policy/physicalRSI/deploy.yml']:
    path = root/'code/RoboDojo'/rel
    assert path.is_file(), str(path)
    files.append(path)
assert sha256(runtime/'PhysicalRSI_baselines/robodojo/agent_planner.py') == protocol['planner_sha256']
pins = dict(verified=True,utc=datetime.now(timezone.utc).isoformat(),protocol_sha256=sha256(suite/'protocol.json'),
            files={str(p):sha256(p) for p in sorted(set(files))})
weight_paths=[p for p in (root/'models/skill-assets').rglob('*.safetensors') if '.venv' not in p.parts and '.git' not in p.parts]
pins['checkpoint_file_stats']={str(p):dict(bytes=p.stat().st_size,mtime_ns=p.stat().st_mtime_ns) for p in weight_paths}
assert weight_paths, 'Checkpoint identities must be recorded'
write_json(suite/'source-pins.json',pins)
(suite/'procedure-sources').mkdir()
for source in result.glob('cloud_catalogue_*.py'):
    shutil.copy2(source,suite/'procedure-sources'/source.name)
for name in ['source-versions.json','policy-packages.json','simulator-packages.json','environment.json']:
    if (prior/name).exists(): shutil.copy2(prior/name,suite/('prior-'+name))
write_json(pointer,dict(directory=str(suite),registered_utc=protocol['registered_utc']))
print(json.dumps(dict(directory=str(suite),planned_native=30,planned_api_only=10,pinned_files=len(pins['files']))))
