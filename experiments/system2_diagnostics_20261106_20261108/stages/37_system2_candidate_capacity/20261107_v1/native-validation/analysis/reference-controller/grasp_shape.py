"""RGB silhouette PCA estimates closing direction and visible shape height."""
import cv2
import numpy as np
from scipy.spatial.transform import Rotation
from .perception import HEIGHT,ray

def grasp(rgb,obj):
 if 'current_rgb_grasp' in obj:
  cached=obj['current_rgb_grasp'];return np.asarray(cached['contact']),np.asarray(cached['quaternion']),cached['shape']
 box=np.asarray(obj['box']);lo=np.maximum(0,np.floor(box[:2]-6)).astype(int);hi=np.minimum([rgb.shape[1],rgb.shape[0]],np.ceil(box[2:]+6)).astype(int)
 crop=rgb[lo[1]:hi[1],lo[0]:hi[0]].copy();h,w=crop.shape[:2];mask=np.zeros((h,w),np.uint8)
 cv2.grabCut(crop,mask,(3,3,w-6,h-6),np.zeros((1,65)),np.zeros((1,65)),3,cv2.GC_INIT_WITH_RECT)
 fg=(mask==1)|(mask==3)
 basket_boxes=obj.get('current_rgb_basket_boxes',[])
 if basket_boxes:
  yy,xx=np.mgrid[:h,:w]
  for b in basket_boxes:
   fg&=~((xx+lo[0]>=b[0])&(xx+lo[0]<=b[2])&(yy+lo[1]>=b[1])&(yy+lo[1]<=b[3]))
  if int(fg.sum())<8:return None
 yy,xx=np.where(fg)
 if len(xx)<8:yy,xx=np.mgrid[3:h-3,3:w-3];yy=yy.reshape(-1);xx=xx.reshape(-1)
 pixels=np.column_stack([xx+lo[0],yy+lo[1]]).astype(float);center=pixels.mean(0)
 hsv=cv2.cvtColor(crop,cv2.COLOR_RGB2HSV);wood=(hsv[:,:,0]>=5)&(hsv[:,:,0]<=30)&(hsv[:,:,1]<110)&(hsv[:,:,2]>140)
 fraction=float(wood[fg].mean()) if fg.any() else 0.
 height=HEIGHT[obj['category']]
 if obj['category']=='toy_car' and fraction>.40:height=.07
 _,vectors=np.linalg.eigh(np.cov(pixels.T));axis=vectors[:,-1]
 p0=ray(center-10*axis,.765+height/2);p1=ray(center+10*axis,.765+height/2)
 heading=np.arctan2(*(p1-p0)[[1,0]]);yaw=(heading+np.pi/2+np.pi/2)%np.pi-np.pi/2
 rotation=Rotation.from_rotvec([0,0,yaw])*Rotation.from_quat([-.5,.5,.5,.5]);q=rotation.as_quat()[[3,0,1,2]]
 contact=ray(center,.765+height/2);contact[2]=.765+height*.65
 return contact,q,dict(yaw_rad=float(yaw),height_prior_m=height,wood_pixel_fraction=fraction,foreground_pixels=len(pixels),center_uv=center)
