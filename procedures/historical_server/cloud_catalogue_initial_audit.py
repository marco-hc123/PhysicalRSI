"""Compare actual saved initial robot states and RGB within every native pair."""
import argparse
import json
from pathlib import Path
import numpy as np
from cloud_catalogue_common import sha256,write_json

parser=argparse.ArgumentParser()
parser.add_argument('--suite',type=Path,required=True)
args=parser.parse_args()
suite=args.suite
protocol=json.loads((suite/'protocol.json').read_text())
controller=json.loads((suite/'controller-status.json').read_text())
assert controller['finished'] and len(controller['jobs'])==30
pairs={}
for job in protocol['jobs']:
    pairs.setdefault(job['pair_id'],{})[job['condition']]=job
rows=[]
for pair_id,jobs in pairs.items():
    files={c:suite/j['name']/'observation-000.npz' for c,j in jobs.items()}
    row=dict(pair_id=pair_id,layout=jobs['projected']['layout'],repeat=jobs['projected']['repeat'],
             observation_files={c:str(p.relative_to(suite)) for c,p in files.items()})
    if not all(p.is_file() for p in files.values()):
        row.update(available=False,reason='A planned case has no initial observation; do not substitute another case')
        rows.append(row);continue
    row['available']=True
    row['sha256']={c:sha256(p) for c,p in files.items()}
    with np.load(files['projected'],allow_pickle=False) as a,np.load(files['unprojected'],allow_pickle=False) as b:
        assert set(a.files)==set(b.files)
        row['instruction_identical']=str(a['instruction'])==str(b['instruction'])
        states={key:bool(np.array_equal(a[key],b[key])) for key in a.files if key.startswith('state__')}
        row['robot_state_fields_identical']=states
        row['all_robot_states_identical']=all(states.values())
        cameras=[]
        for key in a.files:
            if not key.startswith('camera__'):continue
            x,y=a[key],b[key]
            assert x.shape==y.shape
            cameras.append(dict(camera=key,shape=list(x.shape),pixel_identical=bool(np.array_equal(x,y)),
                                mean_absolute_difference=float(np.abs(x.astype(np.float32)-y.astype(np.float32)).mean())))
        row['cameras']=cameras
    rows.append(row)
summary=dict(pair_count=len(rows),available_pairs=sum(r['available'] for r in rows),
    all_available_instructions_identical=all(r.get('instruction_identical') for r in rows if r['available']),
    all_available_robot_states_identical=all(r.get('all_robot_states_identical') for r in rows if r['available']),
    maximum_camera_mae=max((c['mean_absolute_difference'] for r in rows for c in r.get('cameras',[])),default=None),
    scope='Observed equality/variation; same seed is not an assertion of pixel-identical re-rendering',pairs=rows)
write_json(suite/'native-initial-observation-audit.json',summary)
print(json.dumps({k:v for k,v in summary.items() if k!='pairs'}))
