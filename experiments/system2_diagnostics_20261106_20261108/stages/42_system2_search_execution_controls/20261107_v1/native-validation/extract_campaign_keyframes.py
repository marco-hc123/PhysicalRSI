"""Extract a few indexed frames from already validated videos; no new episodes."""
import hashlib,json,subprocess
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[1];K=O/'keyframes';K.mkdir(exist_ok=True)
specs=[('repair','target_offset',4,300),('round2','round2_01',4,300)]
for phase,condition,layout,frame in specs:
    P=O/phase;read=lambda p:json.loads(p.read_text());assert read(P/'analysis/independent-validation.json')['state']=='passed'
    m=read(P/'analysis/matrix-analysis.json');v=next(x for x in m['videos'] if x['condition']==condition and x['layout_id']==layout and x['camera']=='head')
    source=P/v['file'];assert hashlib.sha256(source.read_bytes()).hexdigest()==v['sha256']
    episode=next(x for x in m['episodes'] if x['condition']==condition and x['layout_id']==layout)
    e=next(x for x in read(P/'native-campaign/campaign.json')['entries'] if x['name']==condition)
    output=K/f'{phase}_{condition}_dev{layout}_step{frame}.png';assert not output.exists()
    command=[str(R/'envs/simulator/bin/ffmpeg'),'-v','error','-threads','1','-i',str(source),'-vf',f'select=eq(n\,{frame})','-frames:v','1','-threads','1',str(output)]
    result=subprocess.run(command,capture_output=True,text=True,timeout=90);assert result.returncode==0 and output.is_file(),result.stderr[-1000:]
    meta=dict(task='classify_objects',split='development',phase=phase,condition=condition,layout_id=layout,layout_sha256=episode['layout_sha256'],source_sha256=e['source_sha256'],runtime_sha256=e['runtime_sha256'],video=str(source.relative_to(O)),video_sha256=v['sha256'],camera='head',frame_index_zero_based=frame,native_action_step=frame,png_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),interpretation='One frame is illustrative only. Delivery/stability and task score require full native traces, physical diagnostics and receipts; no pixel edits or fabricated scene.')
    output.with_suffix('.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(dict(frame=str(output.relative_to(O)),source_video_sha256=v['sha256'])))
