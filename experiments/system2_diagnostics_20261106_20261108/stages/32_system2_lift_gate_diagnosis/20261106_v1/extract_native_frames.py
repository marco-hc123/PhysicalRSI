"""Keep selected original decoded frames and explicit provenance, not illustrations."""
import hashlib,json,subprocess
from pathlib import Path
L=Path('/mnt/data/joey_tr/physical-RSI/result/32_system2_lift_gate_diagnosis/20261106_v1')
N=L/'native-validation';O=L/'video-review';O.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]
for condition,layout,frame in [('original',4,1100),('bypass_lift_guard',4,635),('bypass_lift_guard',4,942),('bypass_lift_guard',4,1100),('bypass_lift_guard',0,1100)]:
    videos=list((N/'native-campaign/runs'/condition).rglob(f'episode_{layout:07}_cam_head_*.mp4'));assert len(videos)==1
    video=videos[0];out=O/f'new_{condition}_layout{layout}_head_frame{frame:04}.png'
    assert not out.exists()
    subprocess.run(['ffmpeg','-v','error','-threads','1','-i',str(video),'-vf',f'select=eq(n\\,{frame})','-frames:v','1','-threads','1',str(out)],check=True)
    meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=avg_frame_rate,nb_frames,duration','-of','json',str(video)],text=True))
    rows.append(dict(condition=condition,task='classify_objects',layout=layout,frame=frame,camera='head',image=str(out),image_sha256=sha(out),video=str(video),video_sha256=sha(video),video_metadata=meta,
        note='Encoded frame index; selection near primitive step count is approximate, not separately calibrated physical time. Native official scoring unchanged.'))
(O/'new-frame-index.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows))
