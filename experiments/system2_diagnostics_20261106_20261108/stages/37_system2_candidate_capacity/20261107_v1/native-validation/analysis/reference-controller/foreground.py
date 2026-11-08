"""Appearance-only foreground components in the observed tabletop band."""
import cv2
import numpy as np

def boxes(rgb,ymax=325):
 hsv=cv2.cvtColor(rgb,cv2.COLOR_RGB2HSV);h,s,v=cv2.split(hsv)
 fg=((s<60)&(v>125))|((v<75)&((s<80)|(h>35)))|(((h<5)|(h>35))&(s>50)&(v>80))|((h<30)&(s<125)&(v>190))
 roi=np.zeros(fg.shape,np.uint8);roi[212:ymax,85:555]=fg[212:ymax,85:555]
 roi=cv2.morphologyEx(roi,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
 n,labels,stats,centers=cv2.connectedComponentsWithStats(roi)
 result=[]
 for x,y,w,h,area in stats[1:]:
  if area<35 or max(w,h)>110 or min(w,h)<3 or area>6500:continue
  result.append(np.array([x-2,y-2,x+w+2,y+h+2],float))
 return result

def covered(dino,fg):
 inter=np.maximum(0,np.minimum(dino[2:],fg[2:])-np.maximum(dino[:2],fg[:2])).prod()
 fa=(fg[2:]-fg[:2]).prod();da=(dino[2:]-dino[:2]).prod()
 return inter/max(1,min(fa,da))>.6 and fa<2.5*da
