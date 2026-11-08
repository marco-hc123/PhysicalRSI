"""Track analysis-only matched object during each saved close/lift/transport."""
from pathlib import Path
import json,csv,math
L=Path(__file__).resolve().parent;N=L/'native-validation'
d=json.loads((N/'analysis/postgrasp-analysis.json').read_text());rows=[]
for actor in d['actors']:
    ps=sorted([x for x in d['primitives'] if x['condition']==actor['condition'] and x['actor_episode_id']==actor['actor_episode_id']],key=lambda x:x['ordinal'])
    closes=[p for p in ps if p['method']=='gripper' and p['kwargs']['command']==0]
    for cycle,close in enumerate(closes,1):
        arm=close['kwargs']['arm'];prior=[p for p in ps if p['method']=='approach' and p['ordinal']<close['ordinal'] and p['arm']==arm]
        if not prior:continue
        contact=prior[-1];target=contact['kwargs']['position_m']
        choices=sorted((math.dist(target[:2],v['start_xyz'][:2]),k) for k,v in close['objects'].items() if k.startswith('cat'))
        if not choices:continue
        dist,label=choices[0];margin=choices[1][0]-dist if len(choices)>1 else None;qualified=dist<.05 and margin is not None and margin>.01
        subsequent=[p for p in ps if p['ordinal']>close['ordinal'] and p['arm']==arm]
        segment=[]
        for p in subsequent:
            segment.append(p)
            if p['method']=='gripper':break
        approaches=[p for p in segment if p['method']=='approach'];lift=approaches[0] if approaches else None;transport=approaches[1] if len(approaches)>1 else None
        opened=next((p for p in segment if p['method']=='gripper' and p['kwargs']['command']==1),None)
        def obj(p):return p['objects'][label]['end_xyz'] if p and label in p['objects'] and qualified else None
        def ee(p):
            a=p.get('actual_ee_pose_world') if p else None
            return a[:3] if isinstance(a,list) and len(a)==7 else None
        op0,op1=obj(lift),obj(transport);ep0,ep1=ee(lift),ee(transport)
        do=[y-x for x,y in zip(op0,op1)] if op0 and op1 else None;de=[y-x for x,y in zip(ep0,ep1)] if ep0 and ep1 else None
        residual=math.dist(do,de) if do and de else None
        rows.append(dict(condition=actor['condition'],layout_id=actor['source_layout_id'],cycle=cycle,arm=arm,matched_label=label if qualified else None,association_qualified=qualified,xy_distance_m=dist,xy_margin_m=margin,close_action=close['end_action'],lift_end_action=lift['end_action'] if lift else None,transport_end_action=transport['end_action'] if transport else None,open_end_action=opened['end_action'] if opened else None,lift_root_rise_m=op0[2]-actor['objects'][label]['initial_xyz'][2] if op0 else None,transport_error=(transport.get('result') or {}).get('primitive_error') if transport else None,object_transport_delta_m=do,ee_transport_delta_m=de,relative_translation_change_m=residual,transport_end_root_xyz=op1,after_open_root_xyz=obj(opened),after_open_ee_xyz=ee(opened),final_root_xyz=actor['objects'][label]['final_xyz'] if qualified else None,native_score_100=actor['score']*100))
rows.sort(key=lambda x:(x['condition'],x['layout_id'],x['cycle']))
out=dict(state='completed',new_native_cases=0,new_api_calls=0,gpu_used=False,rows=rows,method='Nearest object XY to contact target at each close; association qualified only under50mm with >10mm margin. Root and end-effector translation compared between completed lift and completed transport.',limits=['Relative-translation change is a grasp-tracking diagnostic, not a grasp-force/contact certificate.','A rotating object can change root-to-gripper offset, so review video before attributing slip.','No matched identity is assigned when ambiguous.','Completed motion primitive does not certify its endpoint or object delivery.','Truth poses are analysis-only and never fed to policy.'])
(L/'transport-tracking-audit.json').write_text(json.dumps(out,indent=2)+'\n')
with (L/'transport-tracking-audit.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows({k:json.dumps(v) if isinstance(v,(list,dict)) else v for k,v in r.items()} for r in rows)
print(json.dumps(dict(cycles=len(rows),qualified=sum(x['association_qualified'] for x in rows),offset_rows=[x for x in rows if x['condition']=='offset_transport']),ensure_ascii=False))
