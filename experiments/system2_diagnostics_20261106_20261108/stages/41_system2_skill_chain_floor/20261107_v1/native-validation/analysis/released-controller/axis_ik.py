"""Public X5 kinematics: exact basket XYZ within a 20-degree approach cone, free axial rotation."""
from pathlib import Path
import numpy as np
import pinocchio as pin
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

URDF=Path(__file__).resolve().parent/'assets/X5A.urdf'
_MODEL=None

def axis_ik(arm, target_pose, current_joint):
    global _MODEL
    if _MODEL is None:
        _MODEL=pin.buildModelFromUrdf(str(URDF))
    model=_MODEL
    data=model.createData()
    fid=model.getFrameId('link6')
    base=pin.SE3(Rotation.from_quat([0,0,.707,.707]).as_matrix(),np.array([-.3 if arm=='left' else .3,-.45,.765]))
    target=base.inverse()*pin.SE3(Rotation.from_quat(np.asarray(target_pose)[[4,5,6,3]]).as_matrix(),np.asarray(target_pose[:3]))
    desired_axis=target.rotation[:,0]
    def fk(q):
        full=pin.neutral(model);full[:6]=q
        pin.framesForwardKinematics(model,data,full)
        return data.oMf[fid]
    def residual(q):
        actual=fk(q)
        delta=actual.rotation[:,0]-desired_axis
        cone=max(0.0, np.cos(np.deg2rad(20))-actual.rotation[:,0]@desired_axis)
        return np.r_[actual.translation-target.translation, .01*delta, 10*cone]
    records=[]
    # Fixed numerical IK seeds; no policy/configuration sweep.
    for seed in [np.asarray(current_joint)[:6],np.zeros(6),np.array([0.,1.,-1.,0.,1.,0.])]:
        seed=np.clip(seed,model.lowerPositionLimit[:6]+1e-6,model.upperPositionLimit[:6]-1e-6)
        opt=least_squares(residual,seed,bounds=(model.lowerPositionLimit[:6],model.upperPositionLimit[:6]),max_nfev=160)
        actual=fk(opt.x)
        pe=float(np.linalg.norm(actual.translation-target.translation))
        ae=float(np.degrees(np.arccos(np.clip(actual.rotation[:,0]@desired_axis,-1,1))))
        world=base*actual
        quat=Rotation.from_matrix(world.rotation).as_quat()[[3,0,1,2]]
        record={'status':'Success' if pe<.003 and ae<=20.1 else 'Fail', 'joint_value':opt.x.tolist(),
                'position_error_m':pe,'axis_error_deg':ae,'target_pose':list(target_pose[:3])+quat.tolist()}
        records.append(record)
        if record['status']=='Success': return record
    return min(records,key=lambda x:x['position_error_m']+np.deg2rad(x['axis_error_deg']))
