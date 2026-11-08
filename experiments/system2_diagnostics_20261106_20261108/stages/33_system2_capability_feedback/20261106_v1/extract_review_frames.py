"""Keep six comparable final frames from verified layout4 native videos."""
import hashlib
import json
import subprocess
from pathlib import Path

L = Path('/mnt/data/joey_tr/physical-RSI/result/33_system2_capability_feedback/20261106_v1')
N = L / 'native-validation'
O = L / 'video-review'


def read(p):
    return json.loads(p.read_text())


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


assert read(N / 'migration/ARCHIVE_VERIFIED.json')['state'] == 'verified'
summary = read(L / 'FINAL_SUMMARY.json')
assert not O.exists(), 'Do not overwrite video review evidence'
O.mkdir()
rows = []
for candidate in summary['candidates']:
    name = candidate['candidate']
    case = next(c for c in summary['cases'] if c['candidate'] == name and c['layout'] == 4)
    videos = list((N / 'native-campaign/runs' / name).rglob('episode_0000004_cam_head_*.mp4'))
    assert len(videos) == 1
    video = videos[0]
    meta = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                                    '-show_entries', 'stream=nb_frames,r_frame_rate', '-of', 'json', str(video)],
                                   capture_output=True, text=True, check=True).stdout)['streams'][0]
    count = int(meta['nb_frames'])
    num, den = map(int, meta['r_frame_rate'].split('/'))
    frame = count - 1
    out = O / f'{name}_layout4_head_final.png'
    subprocess.run(['ffmpeg', '-v', 'error', '-threads', '1', '-i', str(video),
                    '-vf', f'select=eq(n\\,{frame})', '-frames:v', '1', '-threads', '1', str(out)], check=True)
    assert out.is_file()
    rows.append(dict(candidate=name, source_sha256=sha(L / 'candidates' / name / 'candidate.py'),
                     task='classify_objects', layout=4, camera='head', score_100=case['score_100'],
                     success=case['success'], stop_class=case['stop_class'],
                     encoded_frame=frame, encoded_time_s=frame * den / num,
                     encoded_fps=num / den, image=str(out.relative_to(L)), image_sha256=sha(out),
                     video=str(video.relative_to(L)), video_sha256=sha(video),
                     selection='Same previously exposed layout4 for all six candidates; not an unbiased sample of all layouts.',
                     limitation='Encoded time is not wall-clock or calibrated physical time. Native receipt is authoritative for success and score.'))
(O / 'frame-index.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(dict(frames=len(rows), directory=str(O))))
