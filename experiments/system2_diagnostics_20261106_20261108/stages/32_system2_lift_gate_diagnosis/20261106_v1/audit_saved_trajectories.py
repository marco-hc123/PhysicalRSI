"""Check saved solver outputs against static primitive admission constraints, CPU only."""
import datetime,hashlib,json
from pathlib import Path
import numpy as np
L=Path('/mnt/data/joey_tr/physical-RSI/result/32_system2_lift_gate_diagnosis/20261106_v1')
cfg=json.loads((L/'native-validation/analysis/frozen-runtime.json').read_text())['policy_spec']['configuration'];rows=[]
for sub in ['planning-recovery','planning-return']:
    O=L/sub;results=json.loads((O/'results.json').read_text())
    for r in results:
        if not r['trajectory_returned']:continue
        p=O/f'trajectories/job{r["job_id"]:02}.npy';v=np.load(p,allow_pickle=False);limits=cfg['joint_limits'][r['action']['arm']]
        initial=np.asarray(r['start']);delta=np.diff(np.vstack([initial,v]),axis=0)
        checks=dict(shape=v.ndim==2 and v.shape[1]==6,waypoints=1<=len(v)<=500,finite=bool(np.isfinite(v).all()),
            joint_limits=bool(((v>=np.asarray(limits['low']))&(v<=np.asarray(limits['high']))).all()),max_joint_step=bool(np.abs(delta).max()<=.25))
        rows.append(dict(study=sub,job_id=r['job_id'],layout=r['layout'],seed=r['seed'],path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),waypoints=len(v),max_abs_joint_step=float(np.abs(delta).max()),checks=checks,passed=all(checks.values())))
out=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),saved_trajectories_checked=len(rows),passed=sum(r['passed'] for r in rows),rows=rows,
    scope='Static pre-execution shape, joint limit, step bound and finite-value checks using logged initial joints. No simulation, no additional solver calls, no GPU, no success assertion.',
    unresolved='Online observed-state divergence, scene collisions beyond robot/table and remaining native steps still require execution evidence.')
(L/'planning-contract-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='rows'}))
assert all(r['passed'] for r in rows)
