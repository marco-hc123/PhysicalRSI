"""CPU-only proposal audit on a saved, filtered and voxelized Nx3 cloud, in metres."""
import argparse
import json
from pathlib import Path

import numpy as np


def compare(points):
    points = np.asarray(points, dtype=float)
    if points.ndim != 2 or points.shape[1] != 3 or len(points) < 2 or not np.isfinite(points).all():
        raise ValueError("Expected a finite Nx3 fused target cloud in metres")
    xy = points[:, :2]
    median = np.median(points, axis=0)
    span = np.percentile(xy, [2, 98], axis=0).mean(axis=0)
    center = xy.mean(axis=0)
    eigenvalues, vectors = np.linalg.eigh(np.cov((xy - center).T))
    axis = vectors[:, -1]
    if axis[np.argmax(np.abs(axis))] < 0:
        axis = -axis
    short = np.array([-axis[1], axis[0]])
    t, v = (xy - center) @ axis, (xy - center) @ short
    low, high = np.percentile(t, [2, 98])
    mid = (low + high) / 2
    slices = []
    for left in np.arange(low, high, .015):
        right = min(left + .015, high)
        inside = (t >= left) & ((t <= right) if right == high else (t < right))
        if inside.sum() < 10:
            continue
        a, b = np.percentile(v[inside], [2, 98])
        tc = (left + right) / 2
        pos = center + tc * axis + (a + b) / 2 * short
        slices.append(dict(center_xy_m=pos.tolist(), width_m=b-a, n=int(inside.sum()),
                           top_z_p98_m=float(np.percentile(points[inside, 2],98)),
                           distance_to_middle_m=abs(tc-mid)))
    eligible = [s for s in slices if .012 <= s['width_m'] <= .048]
    long_shape = eigenvalues[-1] > 1.25**2 * max(eigenvalues[0], 1.e-15)
    waist = min(eligible, key=lambda s: (s['distance_to_middle_m'], -s['n'])) if eligible and long_shape else None
    positions = {'median':median[:2], 'span':span,
                 'waist':np.asarray(waist['center_xy_m']) if waist else span}
    return dict(n=len(points), fixed_z_m=float(median[2]), waist_uses_span=waist is None,
                slices=slices, candidates={
                    name:dict(xyz_m=[*pos, median[2]],
                              nearest_xy_sample_mm=float(1000*np.linalg.norm(xy-pos,axis=1).min()))
                    for name,pos in positions.items()})


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('fused_npy', type=Path)
    parser.add_argument('--reference-xy-m', type=float, nargs=2)
    parser.add_argument('--old-target-json', required=True, type=Path)
    args=parser.parse_args()
    result=compare(np.load(args.fused_npy, allow_pickle=False))
    original=json.loads(args.old_target_json.read_bytes())['point']
    if original is None or not np.allclose(result['candidates']['median']['xyz_m'],original,atol=1e-6,rtol=0):
        raise ValueError('Median does not reproduce the recorded target to 1 micrometre; inspect reconstruction')
    if args.reference_xy_m is not None:
        for c in result['candidates'].values():
            c['distance_to_reference_xy_mm']=float(1000*np.linalg.norm(np.array(c['xyz_m'][:2])-args.reference_xy_m))
    print(json.dumps(result, indent=2, allow_nan=False))
