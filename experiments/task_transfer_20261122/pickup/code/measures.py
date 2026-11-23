import sys,json
from pathlib import Path
import teacher_kin as kin
from holding_windows import windows
from formal_queue import check,read
def measure(run,digest):
    res,=check(run,digest)['details'].values()
    stage=read(run/'stage2.json')
    phases={}
    for f in run.glob('cmd-*.json'):
        action=read(f)
        if 'action' in action:phases[int(f.stem[4:])]=action['phase']
    stop=read(run/'policy-stop.json')
    t=read(run/'target.json')
    gates=sorted(run.glob('preclose-*.json'))
    arm=read(gates[-1])['arm'] if gates else None
    closes=sorted(i for i,s in phases.items() if s=='close')
    lifts=sorted(i for i,s in phases.items() if s=='lift')
    peak=0.;held=False
    if arm:
        # Use contiguous lift windows, never join across a retreat.
        for begin in (i for i in lifts if i-1 not in lifts):
            end=begin
            while end in lifts:end+=1
            states=[read(run/f'obs-{j}.json')['state'] for j in range(begin,end+1)]
            ee=[s[arm+'_ee_joint_state'][0] for s in states]
            z=[kin.tcp(kin.fk(arm,s[arm+'_arm_joint_state']))[2] for s in states]
            peak=max(peak,float(max(z)-z[0]))
            held=bool(ee[-1]>=.05 and ee[-1]>=.5*ee[0])
    (run/'holding-windows.json').write_text(json.dumps(windows(run),indent=2))
    return dict(success=res['success'],score_native=res['score'],score_100=100*res['score'],steps=stage['steps'],stop=stop['reason'],target=t['description'],closed=bool(closes),auto_held=held,tcp_rise_cm=100*peak,receipt=stage['native_result'],run=str(run))
if __name__=='__main__': print(json.dumps(measure(Path(sys.argv[1]),sys.argv[2])))
