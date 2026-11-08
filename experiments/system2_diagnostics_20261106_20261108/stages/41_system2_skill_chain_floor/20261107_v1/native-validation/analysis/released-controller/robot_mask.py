"""Public X5 meshes projected from the official joint proprioception."""
from pathlib import Path
import cv2
import numpy as np
import pinocchio as pin
from scipy.spatial.transform import Rotation

GEOMETRY = np.load(Path(__file__).with_name('robot_geometry.npz'))
MODEL = pin.buildModelFromUrdf(str(Path(__file__).parent/'assets/x5/X5A.urdf'))
FOCAL = 640 * 10 / 22.212


def project(points):
    x, y, z = np.asarray(points).T
    distance = .5 * (y + .41) - .866025403784 * (z - 1.308)
    return np.column_stack((320 + FOCAL*x/distance,
        240 - FOCAL*(.866025403784*(y+.41)+.5*(z-1.308))/distance))


def robot_mask(state, shape):
    mask = np.zeros(shape[:2], np.uint8)
    for arm in ('left', 'right'):
        joints = pin.neutral(MODEL)
        joints[:6] = np.asarray(state[arm+'_arm_joint_state'])
        joints[6:] = .044 * float(np.asarray(state[arm+'_ee_joint_state']).flat[0])
        data = MODEL.createData()
        pin.framesForwardKinematics(MODEL,data,joints)
        base = pin.SE3(Rotation.from_quat([0,0,.707,.707]).as_matrix(),
            np.array([-.3 if arm=='left' else .3,-.45,.765]))
        for link in GEOMETRY.files:
            pose = base * data.oMf[MODEL.getFrameId(link)]
            uv = project(GEOMETRY[link] @ pose.rotation.T + pose.translation)
            hull = cv2.convexHull(np.round(np.clip(uv,-2000,2000)).astype(np.int32))
            cv2.fillConvexPoly(mask, hull, 1)
    return mask


def robot_fraction(mask, box):
    lo = np.maximum(0, np.floor(box[:2])).astype(int)
    hi = np.minimum([mask.shape[1],mask.shape[0]], np.ceil(box[2:])).astype(int)
    crop = mask[lo[1]:hi[1],lo[0]:hi[0]]
    return float(crop.mean()) if crop.size else 0.
