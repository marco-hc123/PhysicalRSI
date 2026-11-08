"""Four matched final-frame references; all original videos remain archived."""
import hashlib,json,subprocess
from pathlib import Path
L=Path('/mnt/data/joey_tr/physical-RSI/result/34_system2_trajectory_contract/20261106_v1');N=L/'native-validation';O=L/'video-review'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert read(N/'migration/ARCHIVE_VERIFIED.json')['state']=='verified';s=read(L/'FINAL_SUMMARY.json');assert not O.exists();O.mkdir();rows=[]
for group in s['groups']:
 for layout in [1,4]:
  name=group['condition'];case=next(c for c in s['cases'] if c['condition']==name and c['layout']==layout)
  videos=list((N/'native-campaign/runs'/name).rglob(f'episode_{layout:07d}_cam_head_*.mp4'));assert len(videos)==1;v=videos[0]
  meta=json.loads(subprocess.run(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=nb_frames,r_frame_rate','-of','json',str(v)],capture_output=True,text=True,check=True).stdout)['streams'][0]
  frame=int(meta['nb_frames'])-1;num,den=map(int,meta['r_frame_rate'].split('/'));p=O/f'{name}_layout{layout}_head_final.png'
  subprocess.run(['ffmpeg','-v','error','-threads','1','-i',str(v),'-vf',f'select=eq(n\\,{frame})','-frames:v','1','-threads','1',str(p)],check=True)
  rows.append(dict(condition=name,candidate='capability_feedback_2',source_sha256=sha(L/'inputs/candidate.py'),task='classify_objects',layout=layout,camera='head',score_100=case['score_100'],success=case['success'],stop_class=case['stop_class'],encoded_frame=frame,encoded_time_s=frame*den/num,encoded_fps=num/den,image=str(p.relative_to(L)),image_sha256=sha(p),video=str(v.relative_to(L)),video_sha256=sha(v),selection='Matched layouts1and4: prior budget cancellation and partial-score examples; not unbiased across all layouts.',limitation='Encoded time is not wall time. Single final frames do not establish manipulation success; native receipt controls scoring.'))
(O/'frame-index.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(frames=len(rows),directory=str(O))))
