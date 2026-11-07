"""Restore the missing project-local command and qualify the frozen video writer."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

R = Path('/mnt/data/physical-RSI')
O = R / 'result/31_rgb_supplement_20261105'
A = O / 'native-campaign/runs/pi05/attempt-001'
D = O / 'native-preparation/ffmpeg-entry-repair'
D.mkdir(parents=True, exist_ok=True)

def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()

def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')

observed = json.loads((A / 'native/run/observed.json').read_text())
assert not observed['outcomes']
assert len(observed['failures']) == 5
assert all("No such file or directory: 'ffmpeg'" in s for s in observed['failures'])
calls = [json.loads(p.read_text()) for p in (A / 'model/expert/calls').glob('*.json')]
assert len(calls) == 10 and all(c['method'] == 'reset' for c in calls)
assert not list((A / 'episodes').glob('*.json'))
binary = R / 'envs/simulator/lib/python3.11/site-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2'
entry = R / 'envs/simulator/bin/ffmpeg'
assert binary.is_file() and os.access(binary, os.X_OK)
if entry.is_symlink():
    assert entry.resolve() == binary.resolve()
else:
    assert not entry.exists()
    entry.symlink_to(binary)

smoke = D / 'verify_writer.py'
smoke.write_text('''import importlib.util,json,subprocess,shutil
from pathlib import Path
import numpy as np
r=Path('/mnt/data/physical-RSI')
d=r/'result/31_rgb_supplement_20261105/native-preparation/ffmpeg-entry-repair'
source=r/'result/25_system2_integration_20261030T050100Z/integration-sources/native-simulator/utils/save_file.py'
spec=importlib.util.spec_from_file_location('frozen_save_file',source)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
out=d/'writer-smoke.mp4'
assert not out.exists()
w=m.VideoStreamWriter(str(out),48,64,3,fps=10)
for i in range(6):
 frame=np.zeros((48,64,3),dtype=np.uint8);frame[:,:,i%3]=40+i*30
 w.append(frame)
w.close(announce=False)
decoded=subprocess.run(['ffmpeg','-v','error','-i',str(out),'-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True,check=True)
assert len(decoded.stdout)==6*48*64*3
result=dict(state='passed',frames=6,width=64,height=48,decoded_bytes=len(decoded.stdout),video_bytes=out.stat().st_size,ffmpeg=shutil.which('ffmpeg'),api_calls=0,gpu_used=False)
(d/'writer-result.json').write_text(json.dumps(result,indent=2)+'\\n')
print(json.dumps(result))
''')
if not (D / 'writer-result.json').exists():
    with (D / 'writer-smoke.log').open('w') as log:
        subprocess.run([str(R / 'envs/run-native-simulator.sh'), str(smoke)],
                       stdout=log, stderr=subprocess.STDOUT, check=True, timeout=60,
                       env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
result = json.loads((D / 'writer-result.json').read_text())
assert result['state'] == 'passed'
decoded = subprocess.run([str(binary), '-v', 'error', '-i', str(D / 'writer-smoke.mp4'),
                          '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                         capture_output=True, check=True, timeout=30)
assert len(decoded.stdout) == result['decoded_bytes'] == 6 * 48 * 64 * 3
version = subprocess.run([str(binary), '-version'], capture_output=True, text=True, check=True).stdout
(D / 'ffmpeg-version.txt').write_text(version)
receipt = dict(
    utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    state='project_local_entry_restored_and_writer_qualified',
    root_cause='ffmpeg executable was present in the frozen imageio-ffmpeg package but absent from PATH',
    change={'entry': str(entry), 'target': str(binary), 'target_sha256': sha(binary)},
    writer_smoke=result, writer_result_sha256=sha(D / 'writer-result.json'),
    frozen_source_or_package_versions_changed=False, global_environment_changed=False,
    historical_ffmpeg_binary_identity='not recorded; exact historical executable version is unknown',
    caveat='Video encoding executable is operational support; preserve this provenance instead of claiming an independently verified historical binary match.',
    invalid_attempt=str(A), native_policy_inference_calls=0, reset_calls=10,
    valid_native_cases=0, policy_zero_score=False, api_calls=0,
)
write(D / 'repair.json', receipt)
retry = dict(
    utc=receipt['utc'], reason='Documented missing ffmpeg command before any policy inference',
    excluded_attempts=[dict(
        condition='pi05', attempt=str(A), classification='invalid_deployment',
        failed_sha256=sha(A / 'failed.json'),
        observed_sha256=sha(A / 'native/run/observed.json'),
        simulator_log_sha256=sha(A / 'native/processes/simulator/process.log'),
        repair=str(D / 'repair.json'), repair_sha256=sha(D / 'repair.json'),
        valid_native_cases=0, policy_zero_score=False,
    )],
    source_algorithm_harness_layout_reward_or_timeout_changes=False,
    planned_logical_cases_unchanged=35, next_attempt='attempt-002',
)
write(O / 'native-campaign/deployment-retry-authorization.json', retry)
print(json.dumps({'state': receipt['state'], 'writer_smoke': result, 'retry': retry['next_attempt']}))
