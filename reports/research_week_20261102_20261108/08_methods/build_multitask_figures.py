"""Final frozen per-layout results; no best-heldout candidate selection."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
B=Path(__file__).resolve().parents[1];F=B/'figures';O=B/'evidence/result/43_system2_multitask/20261108_v1/native-validation'
def read(p):return json.loads(p.read_text())
s=read(O/'FINAL_SUMMARY.json');assert s['state']=='completed'
plt.rcParams.update({'svg.fonttype':'none','font.family':'DejaVu Sans','font.size':11})
index=read(F/'figure-index.json');index=[r for r in index if not r['id'].startswith(('F07_','F08_'))]
def label(name):
 if name=='parent':return 'Frozen code parent'
 if name=='pi05_reference':return 'Pretrained pi05 reference'
 return ('Feedback ' if 'execution_feedback' in name else 'Basic ')+name.rsplit('-',1)[-1]
for num,task in enumerate(['classify_objects','general_pickup'],7):
 rows=[]
 for role in ['parent','candidates','heldout']:
  for r in read(O/(task+'-'+role)/'analysis/summary.json')['summaries']:
   rows.append(dict(split='heldout' if role=='heldout' else 'development',condition=r['condition'],label=label(r['condition']),scores_100=[x*100 if x is not None else None for x in r['scores']],successes=r['complete_successes'],n=r['n'],planned_n=r.get('planned_n',r['n']),source_sha256=r.get('source_sha256'),source=f'{task}-{role}/analysis/summary.json'))
 dev=[r for r in rows if r['split']=='development'];held=[r for r in rows if r['split']=='heldout']
 fig,axes=plt.subplots(1,2,figsize=(14.5,6.2),gridspec_kw={'width_ratios':[1.15,1]})
 for ax,rs,title in zip(axes,[dev,held],['Development: select here','Heldout: frozen strategies only']):
  a=np.array([r['scores_100'] for r in rs],dtype=float);im=ax.imshow(np.ma.masked_invalid(a),vmin=0,vmax=100,cmap='Blues',aspect='auto')
  ax.set_xticks(range(5),[str(i) for i in range(5)]);ax.set_xlabel('Layout ID (different scenes in each split)')
  ax.set_yticks(range(len(rs)),[r['label']+f"  [{r['successes']}/{r['n']} success]" for r in rs]);ax.set_title(title,pad=14)
  for i in range(len(rs)):
   for j in range(5):ax.text(j,i,f'{a[i,j]:g}' if np.isfinite(a[i,j]) else 'N/A',ha='center',va='center',color='white' if a[i,j]>55 else '#122d44')
  ax.set_xticks(np.arange(-.5,5,1),minor=True);ax.set_yticks(np.arange(-.5,len(rs),1),minor=True);ax.grid(which='minor',color='white',linewidth=1.6);ax.tick_params(which='minor',bottom=False,left=False)
 fig.suptitle(task+' | native score (0–100)',fontsize=17,y=.98)
 choices=s['tasks'][task]['heldout_selected_views']
 choice='; '.join(('feedback' if k=='execution_feedback' else k)+' → '+label(v['selected_source']) for k,v in choices.items())
 fig.text(.5,.075,'Frozen selection: '+choice,ha='center',fontsize=10)
 fig.text(.5,.025,'Five planned layouts per split. N/A = interrupted; not zero. Shared parent views are not extra executions.',ha='center',fontsize=10)
 fig.subplots_adjust(left=.20,right=.98,wspace=.95,top=.86,bottom=.2)
 name=f'F{num:02d}_{task}_multitask'
 fig.savefig(F/(name+'.png'),dpi=180,bbox_inches='tight');fig.savefig(F/(name+'.svg'),bbox_inches='tight');plt.close(fig)
 data=dict(task=task,rows=rows,selection=s['tasks'][task]['selection'],heldout_views=choices,score_unit='native per-episode score multiplied by100; full success is separately shown',limitation='Small single-round two-task feedback pilot; different tasks and split distributions are not pooled.')
 (F/(name+'.data.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 index.append(dict(id=name,title=('分类任务' if num==7 else '抓取任务')+'的开发与独立布局结果',source='B43 FINAL_SUMMARY and each phase analysis/summary.json',limitation='每split计划五布局。N/A为中断缺失原生终态分数，不填0；success分母仅完整评分回合。独立布局不用于选策略，共享父策略不重复执行。抓取要求抬升10cm，不等于分类搬运。',svg=name+'.svg',png=name+'.png',data=name+'.data.json'))
(F/'figure-index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(figures=2,total=len(index))))
