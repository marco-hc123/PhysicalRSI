"""Analysis-only closest-object association for the first close/lift sequence."""
from pathlib import Path
import json,math,csv,os
L=Path(__file__).resolve().parent;N=L/'native-validation'
a=json.loads((N/'analysis/postgrasp-analysis.json').read_text());rows=[]
for actor in a['actors']:
 ps=[p for p in a['primitives'] if p['actor_episode_id']==actor['actor_episode_id'] and p['condition']==actor['condition']]
 close=next((p for p in ps if p['method']=='gripper' and p['kwargs'].get('command')==0),None)
 if close is None:continue
 previous=[p for p in ps if p['method']=='approach' and p['ordinal']<close['ordinal']];assert previous
 target=previous[-1]['kwargs']['position_m'];distances=sorted((math.dist(v['start_xyz'][:2],target[:2]),k) for k,v in close['objects'].items() if k.startswith('cat'))
 distance,label=distances[0];margin=distances[1][0]-distance if len(distances)>1 else None
 qualified=distance<.05 and margin is not None and margin>.01
 lift=next((p for p in ps if p['method']=='approach' and p['ordinal']>close['ordinal']),None)
 initial=actor['objects'][label]['initial_xyz'][2];end=lift['objects'][label]['end_xyz'][2] if lift and label in lift['objects'] else None
 rows.append(dict(condition=actor['condition'],layout_id=actor['source_layout_id'],candidate=actor['condition'],matched_label=label if qualified else None,nearest_label_diagnostic=label,match_qualified=qualified,xy_distance_m=distance,xy_margin_m=margin,first_lift_root_rise_m=end-initial if qualified and end is not None else None,final_root_rise_m=actor['objects'][label]['final_xyz'][2]-initial if qualified else None,max_root_rise_m=actor['objects'][label]['max_dz_m'] if qualified else None,close_action=close['end_action'],lift_action=lift['end_action'] if lift else None,score_100=actor['score']*100))
rows.sort(key=lambda x:(x['condition'],x['layout_id']))
out=dict(rows=rows,scope='Analysis-only privileged root pose, never fed to policy. Association is nearest XY at first close, qualified only under50mm and >10mm separation margin.',limits=['Root-height change is not a stable-grasp or grasp-force certificate.','First lift may improve while later planning or task score does not.','Frame/action indices are not wall-clock seconds.','Unqualified object identity remains unknown.'])
(L/'first-grasp-comparison.json').write_text(json.dumps(out,indent=2)+'\n')
with (L/'first-grasp-comparison.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
os.environ['MPLCONFIGDIR']=str(L/'analysis-cache/matplotlib')
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
fig,ax=plt.subplots(figsize=(7,4))
for name,offset in [('original_transport',-.18),('offset_transport',.18)]:
 r=[x for x in rows if x['condition']==name and x['first_lift_root_rise_m'] is not None]
 ax.bar([x['layout_id']+offset for x in r],[100*x['first_lift_root_rise_m'] for x in r],width=.35,label=name)
ax.set(xlabel='Previously exposed layout',ylabel='Matched object root height change (cm)',title='First close/lift: analysis-only object state',xticks=range(5));ax.legend(fontsize=8);fig.tight_layout()
for ext in ['png','svg']:fig.savefig(L/'figures'/('first_lift_height.'+ext),dpi=150)
plt.close(fig)
with (L/'REPORT.txt').open('a') as f:f.write('\n首个抓持动作的对象关联分析另见first-grasp-comparison.json/csv和figures/first_lift_height.svg。该表只在最近XY匹配距离<5cm且与第二候选间隔>1cm时给出对象抬升，未知项留空；它与原生分类得分分别报告。\n')
print(json.dumps(rows))
