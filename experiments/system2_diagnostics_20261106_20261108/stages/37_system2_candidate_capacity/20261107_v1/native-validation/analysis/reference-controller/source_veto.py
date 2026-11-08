"""Episode-local clear-view RGB veto; not a positive held-object certificate."""
import cv2
import numpy as np

class SourceAppearance:
 def __init__(self,rgb,box):
  h,w=rgb.shape[:2]
  self.lo=np.maximum([0,0],np.floor(np.asarray(box[:2])-3)).astype(int)
  self.hi=np.minimum([w,h],np.ceil(np.asarray(box[2:])+3)).astype(int)
  self.template=rgb[self.lo[1]:self.hi[1],self.lo[0]:self.hi[0]].copy()
 def check(self,rgb,source_confirmed=False):
  t=self.template;h,w=t.shape[:2]
  result=dict(stationary=False,state='unknown',correlation=None,shift_px=None,appearance_agreement=None)
  if min(h,w)<6 or np.std(t.astype(float))<12:return result
  lo=np.maximum([0,0],self.lo-24);hi=np.minimum([rgb.shape[1],rgb.shape[0]],self.hi+24)
  patch=rgb[lo[1]:hi[1],lo[0]:hi[0]]
  if patch.shape[0]<h or patch.shape[1]<w:return result
  corr=cv2.matchTemplate(patch,t,cv2.TM_CCOEFF_NORMED)
  _,score,_,pos=cv2.minMaxLoc(corr)
  shift=np.asarray(pos)+lo-self.lo
  candidate=patch[pos[1]:pos[1]+h,pos[0]:pos[0]+w]
  agreement=float((np.abs(candidate.astype(float)-t.astype(float)).mean(axis=2)<30).mean())
  stationary=bool(source_confirmed and score>=.70 and np.linalg.norm(shift)<=3 and agreement>=.85)
  result.update(stationary=stationary,state='stationary_source' if stationary else 'unknown',correlation=float(score),shift_px=shift.tolist(),appearance_agreement=agreement)
  return result
