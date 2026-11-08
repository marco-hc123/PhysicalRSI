"""Observed stop patterns for saved candidates; not a causal failure classifier."""
from pathlib import Path
import json,collections
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
B=Path(__file__).resolve().parents[1];F=B/'figures';a=json.loads((B/'audit/multitask/mechanism-audit.json').read_text())
groups=[]
for task in ['classify_objects','general_pickup']:
 for cond in ['basic','execution_feedback']:
  rows=[x for x in a['actors'] if x['phase']==task+'-candidates' and '-'+cond+'-' in x['condition']];assert len(rows)==15
  groups.append(dict(task=task,condition=cond,n=len(rows),counts=dict(collections.Counter(x['observed_stop_class'] for x in rows))))
styles=[('program_returned_after_explicit_rejection','Returned after explicit rejection','#a85f42'),('program_returned_after_observation','Returned after observation','#c7a559'),('program_returned_other','Other normal return','#8a9fb2'),('native_success_terminated_active_call','Native success terminated action','#3e8f7c')]
plt.rcParams.update({'svg.fonttype':'none','font.family':'DejaVu Sans','font.size':11})
fig,ax=plt.subplots(figsize=(12.8,5.2));positions=list(range(4));left=[0]*4
for key,label,color in styles:
 vals=[g['counts'].get(key,0) for g in groups]
 ax.barh(positions,vals,left=left,color=color,label=label,height=.60)
 for i,v in enumerate(vals):
  if v:ax.text(left[i]+v/2,i,str(v),ha='center',va='center',color='white' if key not in ['program_returned_after_observation'] else '#243c50',fontweight='bold')
 left=[x+v for x,v in zip(left,vals)]
assert left==[15]*4
ax.set_yticks(positions,[g['task']+' / '+('Basic' if g['condition']=='basic' else 'Execution feedback') for g in groups]);ax.invert_yaxis();ax.set_xlim(0,15);ax.set_xticks([0,5,10,15]);ax.set_xlabel('Native candidate executions (3 candidates × 5 matched layouts per condition)');ax.set_title('Observed stopping patterns differ between tasks',pad=18,fontsize=17);ax.spines[['top','right']].set_visible(False)
ax.legend(loc='upper center',bbox_to_anchor=(.39,-.24),ncol=2,frameon=False,fontsize=10)
fig.text(.50,.025,'Posthoc patterns, not proven root causes. Repeated layouts and shared candidates are correlated.',ha='center',fontsize=10)
fig.subplots_adjust(left=.33,right=.98,top=.83,bottom=.34)
name='F09_multitask_stop_patterns';fig.savefig(F/(name+'.png'),dpi=180,bbox_inches='tight');fig.savefig(F/(name+'.svg'),bbox_inches='tight');plt.close(fig)
(F/(name+'.data.json')).write_text(json.dumps(dict(groups=groups,source='07_verification/multitask/mechanism-audit.json',meaning='Only development candidate episodes. Heldout interruptions and parents are excluded; program return does not imply task success.'),indent=2)+'\n')
index=json.loads((F/'figure-index.json').read_text());index=[x for x in index if x['id']!=name];index.append(dict(id=name,title='多任务候选的停止模式',source='B43原始RPC、native回执和同主机单调时间对应；见mechanism-audit.json',limitation='每组3候选×相同5开发布局；不是15个独立生成样本。正常return不等于成功，成功也会终止活动动作。这是停止现象，不是根因证明；未包含父策略及独立布局中断。',svg=name+'.svg',png=name+'.png',data=name+'.data.json'));(F/'figure-index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n');print('F09 and editable data generated')
