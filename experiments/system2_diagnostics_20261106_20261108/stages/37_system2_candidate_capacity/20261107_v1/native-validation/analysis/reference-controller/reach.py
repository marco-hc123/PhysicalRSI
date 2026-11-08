"""Exact public-URDF endpoint qualification; only RGB poses and proprioception."""
import numpy as np
import pinocchio as pin
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from . import axis_ik

def exact(arm,pose,current):
 if axis_ik._MODEL is None:axis_ik._MODEL=pin.buildModelFromUrdf(str(axis_ik.URDF))
 model=axis_ik._MODEL;data=model.createData();fid=model.getFrameId('link6')
 base=pin.SE3(Rotation.from_quat([0,0,.707,.707]).as_matrix(),np.array([-.3 if arm=='left' else .3,-.45,.765]))
 target=base.inverse()*pin.SE3(Rotation.from_quat(np.asarray(pose)[[4,5,6,3]]).as_matrix(),np.asarray(pose[:3]))
 def fk(q):
  full=pin.neutral(model);full[:6]=q;pin.framesForwardKinematics(model,data,full);return data.oMf[fid]
 def residual(q):
  actual=fk(q);return np.r_[actual.translation-target.translation,.12*pin.log3(target.rotation.T@actual.rotation)]
 for seed in [np.asarray(current),np.zeros(6),np.array([0.,1.,-1.,0.,1.,0.])]:
  opt=least_squares(residual,np.clip(seed,model.lowerPositionLimit[:6]+1e-6,model.upperPositionLimit[:6]-1e-6),bounds=(model.lowerPositionLimit[:6],model.upperPositionLimit[:6]),max_nfev=120)
  actual=fk(opt.x);pe=float(np.linalg.norm(actual.translation-target.translation));re=float(np.linalg.norm(pin.log3(target.rotation.T@actual.rotation)))
  if pe<.003 and re<.03:return opt.x
 return None

def qualify(arm,grasp,q,current,validator=None):
 for angle in [0.,np.pi]:
  quat=(Rotation.from_rotvec([0,0,angle])*Rotation.from_quat(np.asarray(q)[[1,2,3,0]])).as_quat()[[3,0,1,2]]
  joints={};last=current
  for stage,dz in [('approach',.07),('contact',0.),('capture_lift',.008),('lift',.08)]:
   result=exact(arm,[*(grasp+[0,0,dz]),*quat],last)
   if result is None:break
   joints[stage]=result;last=result
  if len(joints)==4:
   candidate=dict(q=quat,joints=joints,grasp=grasp)
   if validator is None or validator(candidate):return candidate
 return None
