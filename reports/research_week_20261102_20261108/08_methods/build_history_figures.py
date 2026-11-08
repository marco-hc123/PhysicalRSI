"""Scientific figures from verified historical records; no experiment mutation."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

B=Path(__file__).resolve().parents[1];O=B/'figures';O.mkdir(exist_ok=True)
rows=json.loads((B/'derived/cohort_results_pre43.json').read_text())
api=json.loads((B/'derived/api_by_condition.json').read_text())
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':180})
index=[]
def save(fig,name,title,source,limitation,data):
 fig.savefig(O/(name+'.svg'),bbox_inches='tight');fig.savefig(O/(name+'.png'),bbox_inches='tight');plt.close(fig)
 (O/(name+'.data.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 index.append(dict(id=name,title=title,source=source,limitation=limitation,svg=name+'.svg',png=name+'.png',data=name+'.data.json'))

rs=[r for r in rows if r['batch']==31 and r['condition']!='pi05']
rs.sort(key=lambda r:(r['condition'].startswith('aug'),r['condition']))
fig,ax=plt.subplots(figsize=(8.4,4.5));v=[r['mean_score_100'] for r in rs]
ax.bar(range(6),v,color=['#72849a']*3+['#247b93']*3,width=.65)
for i,r in enumerate(rs):ax.text(i,v[i]+.18,f"{v[i]:g}",ha='center')
ax.set(xticks=range(6),xticklabels=['Basic 1','Basic 2','Basic 3','Aug. 1','Aug. 2','Aug. 3'],ylabel='Mean native score (0–100)',ylim=(0,4.5),title='Feedback changed execution, with limited partial credit')
fig.text(.12,-.01,'5 exposed layouts per candidate; 0/30 full successes. Both positive episodes used layout 4.',fontsize=9)
save(fig,'F01_feedback_partial','增强反馈出现有限部分分','B31; derived/cohort_results_pre43.json','每候选仅5个已暴露布局，不能视为独立泛化。',rs)

data=[]
for batch in [34,36,40]:
 root=next((B/'evidence/result').glob(str(batch)+'*'));d=json.loads(next(root.glob('*/FINAL_SUMMARY.json')).read_text())
 if batch==34:g=d['groups']; vals=[x['completed_approaches'] for x in g]; metric='Completed approach calls';names=['Dense','Thinned']
 elif batch==36:g=d['groups'];vals=[x['closed_command_mismatches'] for x in g];metric='Closed-command mismatches / 152';names=['Measured','Latched']
 else:g=[d['reused_control'],d['new_group']];vals=[x['completed_approaches'] for x in g];metric='Completed approach calls';names=['Exception','Structured']
 data.append(dict(batch=batch,metric=metric,names=names,values=vals,mean_scores=[x['mean_score_100'] for x in g],n=[x['cases'] for x in g]))
fig,axs=plt.subplots(1,3,figsize=(12,4.5))
for ax,d in zip(axs,data):
 ax.bar([0,1],d['values'],color=['#72849a','#247b93'],width=.6)
 for i,v in enumerate(d['values']):ax.text(i,v+max(d['values'])*.03,f'{v}',ha='center')
 title={34:'B34: Trajectory sampling\nCompleted approach calls',36:'B36: Gripper command\nMismatches / 152 checks',40:'B40: Rejection contract\nCompleted approach calls'}[d['batch']]
 ax.set(xticks=[0,1],xticklabels=d['names'],title=title,ylim=(0,max(d['values'])*1.3))
 ax.text(.5,-.18,'Score: 3 → 3; full success: 0/5 → 0/5',ha='center',transform=ax.transAxes,fontsize=9)
fig.suptitle('Verified process repairs did not raise the matched task score',y=1.05)
save(fig,'F02_process_vs_score','过程修正与任务得分分开报告','B34/B36/B40 FINAL_SUMMARY.json','三个面板属于不同阶段，单位与执行条件不同；B40对照复用B39。',data)

rs=[r for r in rows if r['batch']==42]
orders={'parent':0,'sampling':1,'repair':2,'round2':3,'heldout':4};rs.sort(key=lambda r:(orders[r['phase']],r['condition']))
matrix=np.array([json.loads(r['scores_100']) for r in rs]);fig,ax=plt.subplots(figsize=(8.6,6.5))
im=ax.imshow(matrix,cmap='Blues',vmin=0,vmax=15,aspect='auto')
for i in range(len(rs)):
 for j in range(5):ax.text(j,i,f'{matrix[i,j]:g}',ha='center',va='center',color='white' if matrix[i,j]>7 else '#183047')
ax.set(xticks=range(5),xticklabels=['0','1','2','3','4'],yticks=range(len(rs)),yticklabels=[r['phase']+' / '+r['condition'] for r in rs],xlabel='Within-split layout ID (heldout IDs refer to different layouts)',title='Nov 7: search, manual repair and independent evaluation')
ax.axhline(8.5,color='#bf6344',linewidth=2)
fig.colorbar(im,ax=ax,label='Native score (0–100; displayed values 0 or 15)',shrink=.7)
fig.text(.02,-.035,'Two other round-2 candidates failed admission: no native score, not zero. All shown episodes: success=false.',fontsize=9)
save(fig,'F03_nov7_score_matrix','11月7日逐布局结果','B42 original native receipts; derived/cohort_results_pre43.json','独立布局与开发ID相同但场景不同；未准入候选不填0。',rs)

rs=[r for r in api if r['batch'] in [29,33,42,43]]
fig,ax=plt.subplots(figsize=(10,5))
labels=[]
for r in rs:
 s=f"B{r['batch']} / {r['condition']}"
 if r['batch']==43:s+=' / '+('pickup' if r['task']=='general_pickup' else 'classify')
 labels.append(s)
vals=[r['mean_input_tokens'] for r in rs]
ax.barh(range(len(rs)),vals,color='#247b93')
ax.set(yticks=range(len(rs)),yticklabels=labels,xlabel='Mean input tokens per generation',title='More execution evidence increased generation input')
ax.invert_yaxis();ax.set_xlim(0,max(vals)*1.18)
for i,v in enumerate(vals):ax.text(v+100,i,f'{v:,.0f}',va='center',fontsize=9)
fig.text(.02,-.025,'Different batches are not matched ablations. Cached input is included in input; native validation cost is separate.',fontsize=9)
save(fig,'F04_generation_input','候选生成输入Token','derived/api_by_condition.json; provider usage','跨批次反馈、模型推理设置与协议有差异；不可按时间作因果趋势。',rs)

fig,ax=plt.subplots(figsize=(12,4.8));ax.set_xlim(0,12);ax.set_ylim(0,4.8);ax.axis('off')
boxes=[(0.1,2.7,'Failure evidence\ncode + observations'),(2.5,2.7,'System 2\nAPI generation'),(4.9,2.7,'Admission\ncode / API contract'),(7.3,2.7,'Native execution\nRGB + physics'),(9.7,2.7,'Score + selection\nretain or replace')]
for x,y,label in boxes:
 ax.add_patch(FancyBboxPatch((x,y),2.1,1.1,boxstyle='round,pad=.06',facecolor='#e8f1f5',edgecolor='#247b93'))
 ax.text(x+1.05,y+.55,label,ha='center',va='center',fontsize=11)
for i in range(4):ax.add_patch(FancyArrowPatch((boxes[i][0]+2.15,3.25),(boxes[i+1][0]-.07,3.25),arrowstyle='-|>',mutation_scale=15,color='#43566a'))
ax.text(1.3,1.4,'What did the model see?',ha='center',fontsize=11)
ax.text(5.9,1.4,'What did the candidate receive?',ha='center',fontsize=11)
ax.text(10.1,1.4,'Did the object move?\nDid the native task succeed?',ha='center',fontsize=11)
ax.text(6,.4,'Freeze the selected policy before independent layouts. Count API, native executions and reused evidence separately.',ha='center',fontsize=10)
ax.set_title('System 2 evidence chain and the three verification levels',fontsize=15,pad=14)
save(fig,'F05_system2_evidence_chain','System2证据链','Frozen protocols B29/B42/B43','概念流程图；不是声称已完成官方全量benchmark。',dict(nodes=[x[2] for x in boxes]))

fig,ax=plt.subplots(figsize=(11.2,4.2));ax.axis('off');ax.set_xlim(0,11);ax.set_ylim(0,4)
labels=[('Planner backend','zero-action rejection dictionary'),('Study wrapper','RuntimeError (historical)'),('Candidate','outer except → return')]
for i,(title,desc) in enumerate(labels):
 x=.2+i*3.7;ax.add_patch(FancyBboxPatch((x,2.2),3.1,1.1,boxstyle='round,pad=.05',facecolor='#f9eee9',edgecolor='#b66944'));ax.text(x+1.55,2.9,title,ha='center',weight='bold');ax.text(x+1.55,2.5,desc,ha='center',fontsize=10)
 if i<2:ax.add_patch(FancyArrowPatch((x+3.2,2.75),(x+3.6,2.75),arrowstyle='-|>',mutation_scale=14))
ax.text(5.5,1.4,'B40 correction: return the structured rejection → existing alternate-arm branch executes',ha='center',fontsize=12,color='#247b93')
ax.text(5.5,.6,'3 recovery approaches completed; matched native score unchanged. This conversion was in the study adapter.',ha='center',fontsize=10)
ax.set_title('A confirmed interface mismatch, with a bounded causal conclusion',fontsize=15)
save(fig,'F06_wrapper_correction','已确认的适配层问题','B40 HISTORICAL_CONTRACT_CORRECTION.txt and FINAL_SUMMARY.json','修复恢复分支不等于完成抓取，也不证明PhysicalRSI通用框架有同一错误。',dict(batch=40,recovery_approaches=3,score_before=3,score_after=3,full_success_before=0,full_success_after=0))
(O/'figure-index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(figures=len(index))))
