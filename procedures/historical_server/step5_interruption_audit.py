"""Audit a preregistered stop without replaying any model or native operation."""
from pathlib import Path
from datetime import datetime, timezone
import csv
import fcntl
import json
import os
import subprocess
import sys

R = Path('/mnt/data/physical-RSI')
O = Path(sys.argv[1]).resolve()
assert O.parent == R / 'result'
assert (O / 'iteration-failed.json').exists()
assert not (O / 'iteration-result.json').exists()
cfg = json.loads((O / 'runtime.json').read_text())
os.environ.update(cfg['policy_environment'])
sys.path[:0] = cfg['policy_environment']['PYTHONPATH'].split(':')
from PhysicalRSI_core.infra.storage import atomic_json, read_json, file_digest, digest
from PhysicalRSI_baselines.robodojo import evidence

Z = O / 'interruption-audit'
Z.mkdir(exist_ok=True)
lock = (Z / 'audit.lock').open('a')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
assert not (Z / 'verification.json').exists(), 'Do not overwrite a completed audit'
failure = read_json(O / 'iteration-failed.json')
start = read_json(O / 'iteration-started.json')
assert not Path('/proc/' + str(start['pid'])).exists(), 'Wait for controller cleanup'
assert not subprocess.check_output(
    ['nvidia-smi', '--query-compute-apps=pid', '--format=csv,noheader'], text=True
).strip(), 'Wait for native GPU processes to finish'
protocol = read_json(O / 'protocol.json')
assert file_digest(O / 'runtime.json') == protocol['configuration_sha256']
assert file_digest(O / 'workflow-configuration.json') == protocol['workflow_configuration_sha256']
for name, sha in protocol['sources'].items():
    assert file_digest(Path(name)) == sha, name
freeze = read_json(R / 'result/23_protocol_freeze_20261029T132917Z/source-freeze.json')
for row in freeze['deployment_files']:
    assert file_digest(Path(row['path'])) == row['sha256'], row['path']
for name, sha in freeze['recorded_protocol_and_framework_hashes'].items():
    assert file_digest(Path(name)) == sha, name

budget = read_json(O / 'native-budget.json')
episodes, videos, incomplete = [], [], []
for batch in budget['batches']:
    leaf = Path(batch['output'])
    if batch['state'] != 'completed':
        assert not (leaf / 'episodes').exists(), 'Reconcile potentially completed native work first'
        incomplete.append(dict(batch=batch, counted_as_native_task_failure=False,
            artifacts={str(p): file_digest(p) for p in leaf.rglob('*') if p.is_file()}))
        continue
    paths = sorted((leaf / 'episodes').glob('*.json'))
    assert len(paths) == batch['count'] == 1
    for path in paths:
        row = read_json(path)
        evidence.episode_receipt(path, directory=leaf, task=row['task'], split=row['split'],
            layout_sha256=row['layout_sha256'], expert=dict(name=row['expert'], revision=row['revision']),
            harness_sha256=row['harness_sha256'])
        steps = row['diagnostics']['action_count']
        assert row['native_exit_code'] == 0 and row['natural_terminal'] and 0 <= steps <= 1100
        media = sorted(leaf.rglob('*.mp4'))
        assert len(media) == 3
        for p in media:
            info = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                '-count_frames', '-show_entries', 'stream=nb_read_frames', '-of', 'json', str(p)], text=True))
            frames = int(info['streams'][0]['nb_read_frames'])
            assert frames == steps + 1
            videos.append(dict(path=str(p), frames=frames, bytes=p.stat().st_size))
        episodes.append(dict(path=str(path), split=row['split'], expert=row['expert'],
            score=row['episode_score'], success=row['success'], steps=steps,
            layout_sha256=row['layout_sha256']))
assert len(episodes) == budget['completed']
assert len(episodes) + sum(r['batch']['count'] for r in incomplete) == budget['requested'] <= 50

calls = []
for path in sorted((O / 'proposal-api').glob('call-*/started.json')):
    directory = path.parent
    if not (directory / 'completed.json').exists():
        calls.append(dict(directory=str(directory), completed=False, usage_unknown=True))
        continue
    done = read_json(directory / 'completed.json')
    response = read_json(directory / 'response.json')
    usage = response['usage']
    assert usage == done['usage'] and usage['total_tokens'] == usage['prompt_tokens'] + usage['completion_tokens']
    assert done['http_attempts'] == 1
    round_index = read_json(path)['round_index']
    W = O / ('workspace/rounds/round-%06d' % round_index)
    raw = read_json(W / 'development-results.json')
    proposal = read_json(W / 'proposals/classify_objects/skill-proposal.json')
    generated = json.loads(response['choices'][0]['message']['content'])
    assert generated['source'] == proposal['source'] and generated['memory'] == proposal['memory']
    assert proposal['development_feedback_sha256'] == digest(raw)
    calls.append(dict(directory=str(directory), completed=True, http_attempts=1,
        input_tokens=usage['prompt_tokens'], output_tokens=usage['completion_tokens'], total_tokens=usage['total_tokens'],
        reasoning_tokens_subset_output=usage.get('completion_tokens_details', {}).get('reasoning_tokens'),
        elapsed_s=done['elapsed_s'], finish_reason=done['finish_reason'], source_sha256=proposal['source_sha256']))

secret = read_json(Path('/home/ecs-user/.config/physicalrsi/agent.json'))['api_key'].encode()
files_checked = 0
for path in O.rglob('*'):
    if path.is_file() and path.suffix in {'.json', '.jsonl', '.log', '.py', '.txt', '.csv'}:
        assert secret not in path.read_bytes(), 'Credential found in experiment artifacts'
        files_checked += 1
telemetry = list(csv.DictReader((O / 'gpu-telemetry.csv').open()))
utc = datetime.now(timezone.utc).isoformat()
result = dict(utc=utc, step=5, scientific_rounds_complete=False, audit_complete=True,
    stop=failure, committed_rounds=len(list(O.glob('round-*-result.json'))),
    completed_native_episodes=episodes, interrupted_native_batches=incomplete, model_calls=calls,
    video_count=len(videos), video_frames=sum(r['frames'] for r in videos),
    original_deployment_pins_verified=len(freeze['deployment_files']),
    original_framework_pins_verified=len(freeze['recorded_protocol_and_framework_hashes']),
    credential_matches=0, text_files_checked=files_checked, gpu_compute_processes=0,
    gpu_peak_memory_MiB=max(float(r['gpu_memory_MiB']) for r in telemetry),
    gpu_peak_util_percent=max(float(r['gpu_util_percent']) for r in telemetry),
    raw_retention='cloud_only', steps6_to8_started=False, no_model_or_native_retry=True,
    qualification='Preregistered failure stop audited; no score or completed-task failure imputed to interrupted work.',
    audit_source_sha256=file_digest(Path(__file__)))
atomic_json(Z / 'videos.json', videos)
atomic_json(Z / 'verification.json', result)
print(json.dumps(dict(audit_complete=True, scientific_rounds_complete=False,
    native_completed=len(episodes), native_interrupted=len(incomplete), proposal_calls=len(calls),
    videos=len(videos), gpu_compute_processes=0, verification=str(Z / 'verification.json'))))
