"""Verify recorded MP4 metadata and consistency across the three camera views."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess

root = Path('/mnt/data/physical-RSI/result')
suite = Path(json.loads((root/'CURRENT_EXPERIMENT_SUITE.json').read_text())['directory'])
videos = json.loads((suite/'video-manifest.json').read_text())
expected = json.loads((suite/'audit.json').read_text())['native_episodes_verified']


def inspect(relative):
    path = suite/relative
    result = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=codec_name,width,height,nb_frames,r_frame_rate,duration',
        '-of', 'json', str(path)], capture_output=True, text=True, check=True, timeout=30)
    stream = json.loads(result.stdout)['streams'][0]
    frames = int(stream['nb_frames'])
    assert frames > 1 and stream['width'] > 0 and stream['height'] > 0
    return dict(path=relative, bytes=path.stat().st_size, frames=frames, **stream)


with ThreadPoolExecutor(max_workers=4) as executor:
    rows = list(executor.map(inspect, videos))
groups = {}
for row in rows:
    key = row['path'].split('_cam_')[0]
    groups.setdefault(key, []).append(row)
assert len(groups) == expected
for key, group in groups.items():
    assert len(group) == 3, (key, 'Expected three camera videos')
    assert len({row['frames'] for row in group}) == 1, (key, 'Camera frame counts differ')
report = dict(passed=True, episodes=expected, video_files=len(rows),
               total_frames=sum(r['frames'] for r in rows),
               check='MP4 stream metadata, nonempty videos, three views with matching frame counts',
               videos=rows)
(suite/'video-audit.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='videos'}))
