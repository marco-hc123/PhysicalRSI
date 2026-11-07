"""Extract selected original video frames; leave native videos unchanged."""
import hashlib,json,subprocess
from pathlib import Path
R=Path('/mnt/data/physical-RSI/result/31_rgb_supplement_20261105')
D=R/'analysis';K=D/'keyframes';K.mkdir(exist_ok=True)
data=json.loads((D/'matrix-analysis.json').read_text())
ff='/mnt/data/physical-RSI/envs/simulator/bin/ffmpeg'
choices=[('augmented_1',4,[0,20,40]),('baseline_1',0,[40]),('baseline_1',4,[40]),('pi05',0,[40])]
records=[]
for condition,layout,times in choices:
    video=next(v for v in data['videos'] if (v['condition'],v['layout_id'],v['camera'])==(condition,layout,'head'))
    harness=R/'native-campaign/harnesses'/condition
    for seconds in times:
        out=K/f'{condition}_layout{layout}_head_t{seconds}.png'
        if not out.exists():
            p=subprocess.run([ff,'-v','error','-threads','1','-ss',str(seconds),'-i',str(R/video['file']),'-frames:v','1','-threads','1',str(out)],capture_output=True,text=True)
            assert p.returncode==0,p.stderr[-1000:]
        records.append(dict(task='classify_objects',condition=condition,layout_id=layout,camera='head',video_time_seconds=seconds,time_scope='encoded video timestamp; not physical simulation time or wall clock',source_video=video['file'],video_sha256=video['sha256'],image=str(out.relative_to(R)),image_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),policy_identity='Frozen native-campaign/campaign.json entry and harnesses/'+condition))
(D/'keyframe-index.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'keyframes':len(records),'index':str(D/'keyframe-index.json')}))
