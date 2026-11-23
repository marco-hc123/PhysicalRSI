"""Bind public image pairs to actual action stages for score-blind holding review."""
import hashlib,json
from pathlib import Path

CAMS=('cam_head','cam_left_wrist','cam_right_wrist')
def capture(run,label):
    state=run/(label+'-state.json')
    images=[]
    for camera in CAMS:
        f=run/(label+'-'+camera+'.png')
        if f.exists():
            images.append({'camera':camera,'file':f.name,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
    return {'stage':label,'images':images,'public_state':json.loads(state.read_bytes()) if state.exists() else None}
def windows(run):
    phases=[json.loads(p.read_bytes())['phase'] for p in sorted(run.glob('cmd-*.json'),key=lambda p:int(p.stem[4:])) if 'action' in json.loads(p.read_bytes())]
    out=[]
    for phase,start,end in [('close','before-close','before-lift'),('lift','before-lift','after')]:
        observed=phase in phases
        image_pair=[capture(run,k) for k in (start,end)]
        full=observed and all(len(x['images'])==3 and x['public_state'] is not None for x in image_pair)
        out.append({'phase':phase,'status':('ready_for_blind_visual_review' if full else 'incomplete_window' if observed else 'action_not_reached'),'endpoints':image_pair if observed else [],'before_held':None,'after_held':None,'retained':None})
    return out
if __name__=='__main__':
    d=Path(__file__).resolve().parent
    for staged in sorted((d/'runs').glob('*/*/*/stage2.json')):
        if json.loads(staged.read_bytes()).get('status')!='passed':continue
        run=staged.parent
        p=run/'holding-windows.json';v={'windows':windows(run),'role':'offline diagnostic; no access to scoring and no effects on actions'}
        p.write_text(json.dumps(v,indent=2))
        print(run.relative_to(d),[x['status'] for x in v['windows']])
