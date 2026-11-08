import hashlib,json,subprocess
from pathlib import Path
L=Path('/mnt/data/joey_tr/physical-RSI/result/32_system2_lift_gate_diagnosis/20261106_v1')
N=L/'retreat-followup/native-validation';O=L/'video-review';rows=[]
assert json.loads((N/'migration/ARCHIVE_VERIFIED.json').read_text())['state']=='verified'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for condition in ['bypass_lift_guard','return_to_clearance']:
    for layout in [1,4]:
        videos=list((N/'native-campaign/runs'/condition).rglob(f'episode_{layout:07}_cam_head_*.mp4'));assert len(videos)==1
        video=videos[0];out=O/f'retreat_{condition}_layout{layout}_head_frame1100.png';assert not out.exists()
        subprocess.run(['ffmpeg','-v','error','-threads','1','-i',str(video),'-vf','select=eq(n\\,1100)','-frames:v','1','-threads','1',str(out)],check=True)
        rows.append(dict(condition=condition,layout=layout,task='classify_objects',camera='head',encoded_frame=1100,encoded_time_s=44.,image=str(out),image_sha256=sha(out),video=str(video),video_sha256=sha(video),note='Final encoded frame at25fps. Encoded time is not wall-clock or calibrated physical time. Native score remains the authoritative outcome.'))
(O/'retreat-frame-index.json').write_text(json.dumps(rows,indent=2)+'\n');print('Saved4 final frames with provenance.')
