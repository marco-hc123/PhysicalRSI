"""Extract unaltered native frames at matched physical stages, no video edits."""
from pathlib import Path
import json,subprocess,hashlib
L=Path(__file__).resolve().parent;N=L/'native-validation';O=L/'transport-video-review';O.mkdir(exist_ok=False)
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
m=read(N/'analysis/matrix-analysis.json');a=read(L/'transport-tracking-audit.json');index=[]
for layout in [0,2,4]:
    rows=[x for x in a['rows'] if x['condition']=='offset_transport' and x['layout_id']==layout]
    first=min(rows,key=lambda x:x['cycle']) if rows else None
    video=next(x for x in m['videos'] if x['condition']=='offset_transport' and x['layout_id']==layout and x['camera']=='head')
    path=N/video['file'];meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=r_frame_rate,nb_frames','-of','json',str(path)],text=True))['streams'][0]
    num,den=map(int,meta['r_frame_rate'].split('/'));end=int(meta['nb_frames'])-1
    frames=[('final',end)]
    if first:
        frames=[(phase,first[key]) for phase,key in [('first_lift','lift_end_action'),('first_transport','transport_end_action'),('first_release','open_end_action')] if first[key] is not None]+frames
    for phase,frame in frames:
        target=O/f'offset_layout{layout}_{phase}.png';assert 0<=frame<=end
        subprocess.run(['ffmpeg','-v','error','-threads','1','-i',str(path),'-vf',f'select=eq(n\\,{frame})','-frames:v','1','-threads','1',str(target)],check=True)
        index.append(dict(task='classify_objects',layout_id=layout,condition='offset_transport',candidate_sha256=sha(L/'candidates/offset_transport/candidate.py'),phase=phase,frame=frame,encoded_time_s=frame*den/num,encoded_time_is_not_wall_time=True,image=str(target.relative_to(L)),image_sha256=sha(target),video='native-validation/'+video['file'],video_sha256=sha(path),matched_first_object=first['matched_label'] if first else None,source='Original encoded video, frame matched to sidecar native action index'))
(O/'frame-index.json').write_text(json.dumps(index,indent=2)+'\n');print(json.dumps(dict(frames=len(index))))
