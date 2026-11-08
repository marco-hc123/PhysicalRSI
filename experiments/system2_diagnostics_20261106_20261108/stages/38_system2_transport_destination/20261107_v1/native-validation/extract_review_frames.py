"""Use exact action-index frames; original videos remain unchanged."""
import json,subprocess,hashlib
from pathlib import Path
L=Path(__file__).resolve().parent;N=L/'native-validation';O=L/'video-review';O.mkdir(exist_ok=False)
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
a=read(N/'analysis/postgrasp-analysis.json');m=read(N/'analysis/matrix-analysis.json');rows=[]
for actor in a['actors']:
 if actor['source_layout_id'] not in (0,4):continue
 ps=[p for p in a['primitives'] if p['actor_episode_id']==actor['actor_episode_id']]
 close=next((p for p in ps if p['method']=='gripper' and p['kwargs'].get('command')==0),None)
 fail=next((p for p in ps if p.get('result',{}).get('primitive_error')),None)
 lift=next((p for p in ps if close and p['ordinal']>close['ordinal'] and p['method']=='approach'),None)
 choices=[('first_close',close),('first_lift',lift),('rejected_transport',fail)]
 v=next(v for v in m['videos'] if v['condition']==actor['condition'] and v['layout_id']==actor['layout_id'] and v['camera']=='head')
 video=N/v['file'];meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=r_frame_rate,nb_frames','-of','json',str(video)],text=True))['streams'][0];num,den=map(int,meta['r_frame_rate'].split('/'))
 for phase,primitive in choices:
  if primitive is None:continue
  frame=primitive['end_action'];name=f"{actor['condition']}_layout{actor['source_layout_id']}_{phase}.png";target=O/name
  subprocess.run(['ffmpeg','-v','error','-threads','1','-i',str(video),'-vf',f'select=eq(n\\,{frame})','-frames:v','1','-threads','1',str(target)],check=True)
  rows.append(dict(condition=actor['condition'],task='classify_objects',candidate=actor['condition'],source_layout_id=actor['source_layout_id'],runtime_layout_id=actor['layout_id'],phase=phase,frame=frame,encoded_time_s=frame*den/num,encoded_time_is_not_wall_time=True,image='video-review/'+name,image_sha256=sha(target),video='native-validation/'+v['file'],video_sha256=sha(video),score_100=actor['score']*100,source='monotonic primitive alignment; use original video for continuity'))
(O/'frame-index.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(dict(frames=len(rows))))
