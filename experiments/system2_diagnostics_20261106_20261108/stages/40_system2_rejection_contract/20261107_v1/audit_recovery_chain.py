"""Locate every explicit rejection in the unchanged candidate's action sequence."""
import csv,json
from pathlib import Path
L=Path(__file__).resolve().parent;N=L/'native-validation'
read=lambda p:json.loads(p.read_text());rows=[];episodes=[]
for a in read(N/'analysis/matrix-analysis.json')['actors']:
    calls=read(N/a['process_record'])['calls'];phase='before_scene';cycle=0;fallback_in_cycle=False;events=[]
    for i,c in enumerate(calls):
        q=c['request'];method=q['method'];kw=q['kwargs'];v=c.get('response',{}).get('value',{});error=v.get('primitive_error') if isinstance(v,dict) else None
        if method in ['scene','reobserve']:phase='pregrasp_clearance';cycle+=1;fallback_in_cycle=False
        elif method=='gripper':phase='contact' if kw['command']==1 and phase=='pregrasp_clearance' else ('lift' if kw['command']==0 else 'released')
        elif method=='approach':
            if error:
                nxt=calls[i+1]['request'] if i+1<len(calls) else None
                is_fallback=bool(nxt and nxt['method']=='approach' and nxt['kwargs'].get('arm')!=kw['arm'] and nxt['kwargs'].get('position_m')==kw['position_m'])
                row=dict(layout_id=a['mapped_layout_id'],actor=a['actor_episode_id'],scene_ordinal=cycle-1,call_id=q['id'],phase=phase,arm=kw['arm'],target=kw['position_m'],primitive_error=error,alternate_arm_requested=is_fallback,earlier_fallback_in_this_cycle=fallback_in_cycle,final_recorded_call=i==len(calls)-1)
                rows.append(row);events.append(row)
                if is_fallback:fallback_in_cycle=True
            elif phase=='contact':phase='contact_completed'
            elif phase=='lift':phase='transport'
            elif phase=='transport':phase='transport_completed'
    episodes.append(dict(layout_id=a['mapped_layout_id'],final_phase=phase,explicit_rejections=events))
out=dict(state='completed',new_native_cases=0,api_calls=0,gpu_used=False,rows=rows,episodes=episodes,scope='Action-sequence phases of this fixed candidate only; a phase label is not proof of grasp success or a collision-free path.')
(L/'recovery-chain-audit.json').write_text(json.dumps(out,indent=2)+'\n')
if rows:
    with (L/'recovery-chain-audit.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print(json.dumps(rows))
