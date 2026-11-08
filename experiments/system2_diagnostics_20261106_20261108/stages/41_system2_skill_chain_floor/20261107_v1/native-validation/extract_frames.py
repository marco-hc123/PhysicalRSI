"""Extract unmodified native video frames for representative chain review."""
import hashlib,json,subprocess
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[1]
read=lambda p:json.loads(p.read_text())
d=read(O/'chain-analysis.json');rows=d['cases'];selected=[]
for condition in ['single_cycle','released_first_basket_cycle']:
    group=[r for r in rows if r['condition']==condition]
    positive=next((r for r in group if r.get('complete_chain_proxy')),None)
    negative=next((r for r in group if not r.get('complete_chain_proxy')),None)
    for row in [positive,negative]:
        if row is not None:selected.append(row)
out=O/'keyframes';out.mkdir(exist_ok=True);index=[]
videos=read(O/'analysis/matrix-analysis.json')['videos']
reference=read(O/'reference/analysis/video-decode-validation.json')
for row in selected:
    condition=row['condition'];i=row['layout_id'];arm=row.get('arm') or 'left'
    sources=[dict(file=v['file'],camera=v['camera'],sha256=v['sha256']) for v in videos if v['layout_id']==i] if condition=='single_cycle' else [dict(file='reference/'+v['file'],camera=Path(v['file']).name.split('_cam_',1)[1].rsplit('_',1)[0],sha256=v['sha256']) for v in reference if v['layout']==i]
    times=dict(row.get('phase_action_indices',{}),final=1100)
    for camera in ['head',arm+'_wrist']:
        video=next(v for v in sources if camera in v['camera']);source=O/video['file']
        for phase,frame in times.items():
            dest=out/f'{condition}_layout{i}_{phase}_{camera}_{frame:04d}.png'
            assert not dest.exists()
            p=subprocess.run([str(R/'envs/simulator/bin/ffmpeg'),'-v','error','-threads','1','-i',str(source),'-vf',f'select=eq(n\\,{frame})','-frames:v','1','-vsync','0','-threads','1',str(dest)],capture_output=True,text=True,timeout=45)
            assert p.returncode==0 and dest.exists(),p.stderr
            index.append(dict(condition=condition,layout_id=i,phase=phase,native_action_frame=frame,camera=camera,path=str(dest.relative_to(O)),sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),source_video=video['file'],source_sha256=video['sha256'],selection='First qualifying complete-chain proxy and first non-qualifying case in each condition; descriptive examples only'))
(out/'frame-index.json').write_text(json.dumps(index,indent=2)+'\n')
print(json.dumps(dict(state='frames_extracted',cases=len(selected),frames=len(index))))
