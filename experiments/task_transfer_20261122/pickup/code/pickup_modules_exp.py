import numpy as np
from teacher_functions import world_points, voxel_downsample_3d
from PIL import Image

NAMES=('cam_head','cam_left_wrist','cam_right_wrist')
def views_from(path):
    with np.load(path,allow_pickle=False) as a:
        return {n:{k:a[n+'_'+k] for k in ('color','depth','extrinsic_matrix','intrinsic_matrix')} for n in NAMES}

def extract(views,sam,prompt,f8=False,overlay=None):
    def compute(text):
        batch=[]
        for name,view in views.items():
            seg=sam.segment(view['color'],text_prompt=text,min_score=0 if f8 else .2)
            pts=np.empty((0,3))
            if seg.found:
                pts,_=world_points(view,*np.nonzero(seg.mask))
                pts=pts[np.isfinite(pts).all(1)&(abs(pts[:,0])<.6)&(pts[:,1]>-.5)&(pts[:,1]<.3)&(pts[:,2]>=.765)]
            batch.append((name,text,seg,pts))
        return batch
    rows=compute(prompt)
    good=[r for r in rows if r[2].found and r[2].score>=.2]
    if f8 and all((r[2].score or 0)<.2 for r in rows):
        words=prompt.split()
        while len(words)>1 and words[0].lower() in {'white','black','plastic','metal','metallic'}:
            words.pop(0)
        simple=' '.join(words)
        if simple!=prompt:
            other=compute(simple)
            rows+=other
            good=[r for r in other if r[2].found and r[2].score>=.2]
        if not good:
            r=max(rows,key=lambda r:r[2].score or 0)
            seg=r[2]
            if seg.found and seg.score>=.10 and 200<=seg.mask.sum()<=40000 and len(r[3])>=50:good=[r]
    if overlay:
        overlay.mkdir(exist_ok=True,parents=True)
        for name,text,seg,pts in good:
            img=views[name]['color'].copy()
            img[seg.mask]=(img[seg.mask]*.55+np.array([240,20,30])*.45).astype(np.uint8)
            Image.fromarray(img).save(overlay/(name+'.jpg'))
    pts=[r[3] for r in good if len(r[3])]
    return (voxel_downsample_3d(np.concatenate(pts)) if pts else None),[dict(camera=n,prompt=t,score=s.score,points=len(p),selected=any(r[2] is s for r in good)) for n,t,s,p in rows]
