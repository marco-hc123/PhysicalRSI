"""Analyze verified archive on CPU and provide evidence-linked interpretation."""
import json,hashlib,datetime,csv,statistics,os
from pathlib import Path
L=Path(__file__).resolve().parent;N=L/'native-validation'
os.environ.setdefault('MPLCONFIGDIR',str(L/'analysis-cache/matplotlib'))
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
archive=read(N/'migration/ARCHIVE_VERIFIED.json');assert archive['state']=='verified'
a=read(N/'analysis/postgrasp-analysis.json');m=read(N/'analysis/matrix-analysis.json');assert a['state']=='passed'
P=L.parent.parent/'33_system2_capability_feedback/20261106_v1';proposal=read(P/'candidates/capability_feedback_2/proposal.json')
checks=[]
for actor in m['actors']:
 p=(N/actor['process_record']).parents[2]/'root/input.json';packet=read(p)
 assert packet['source']==proposal['source'] and packet['memory']==proposal['memory']
 checks.append(dict(condition=actor['condition'],actor=actor['actor_episode_id'],source_exact=True,memory_exact=True,input_sha256=sha(p)))
rows=[]
for actor in sorted(a['actors'],key=lambda x:(x['condition'],x['source_layout_id'])):
 ps=[p for p in a['primitives'] if p['condition']==actor['condition'] and p['actor_episode_id']==actor['actor_episode_id']]
 close=[p for p in ps if p['method']=='gripper' and p['kwargs'].get('command')==0]
 failed=[p for p in ps if p.get('result',{}).get('primitive_error')]
 statuses=[dict(index=r['index'],status=r.get('result',{}).get('status'),success=r.get('result',{}).get('success'),available_attributes=r.get('available_attributes')) for r in actor['raw_planner_results']]
 row=dict(condition=actor['condition'],source_layout_id=actor['source_layout_id'],score_100=100*actor['score'],native_budget_cancel=actor['native_step_limit_cancelled'],closed_gripper_calls=len(close),failed_approaches=len(failed),last_failed_target=failed[-1]['kwargs'] if failed else None,solver_statuses=statuses,maximum_item_lift_m=max([v['max_dz_m'] for k,v in actor['objects'].items() if k.startswith('cat')],default=None),object_motion=actor['objects'])
 rows.append(row)
F=L/'figures';F.mkdir(exist_ok=True);figures=[]
for actor in a['actors']:
 condition=actor['condition'];idx=actor['layout_id'];sid=actor['source_layout_id'];samples=[]
 for p in (N/'sim-diagnostics'/condition).glob('*.jsonl'):
  samples += [x for line in p.read_text().splitlines() if (x:=json.loads(line)).get('event')=='snapshot' and x['layout_seed']==idx]
 samples.sort(key=lambda x:x['monotonic_ns']);labels=[k for k in actor['objects'] if k.startswith('cat')]
 fig,ax=plt.subplots(figsize=(8,4))
 for label in labels:
  initial=actor['objects'][label]['initial_xyz'][2]
  xy=[(x['native_action_count'],x['objects'].get(label,{}).get('position_world')) for x in samples]
  xy=[(n,pos) for n,pos in xy if isinstance(pos,list) and len(pos)==3]
  ax.plot([n for n,pos in xy],[(pos[2]-initial)*100 for n,pos in xy],label=label,linewidth=1)
 for p in [p for p in a['primitives'] if p['condition']==condition and p['layout_id']==idx]:
  if p['method']=='gripper' and p['kwargs'].get('command')==0:ax.axvline(p['end_action'],color='black',linestyle='--',alpha=.4)
  if p.get('result',{}).get('primitive_error'):ax.axvline(p['end_action'],color='red',linestyle=':',alpha=.7)
 ax.set(xlabel='Native action index (not seconds)',ylabel='Object root height change (cm)',title=f'{condition} | classify_objects | source layout {sid}')
 ax.legend(ncol=3,fontsize=6);ax.grid(alpha=.2);fig.tight_layout()
 name=f'{condition}_layout{sid}_object_height';fig.savefig(F/(name+'.png'),dpi=150);fig.savefig(F/(name+'.svg'));plt.close(fig)
 figures.append(dict(png='figures/'+name+'.png',svg='figures/'+name+'.svg',data='native-validation/sim-diagnostics/'+condition,scope='Analysis-only true object state; dashed=close, red dotted=planner rejection; not policy input'))
summary=dict(state='completed',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),accounting=dict(new_native_cases=archive['native_cases'],new_raw_videos=archive['videos'],new_api_calls=0,lab_gpu_used=False,policy_promotions=0,source_layouts=[0,1,4]),cases=rows,candidate_bindings=checks,logging_ms=a['logging_ms'],figures=figures,archive=archive,retained_policy='pi05',scope='Manual compatibility-contract diagnosis, not a new autonomous System2 improvement')
(L/'FINAL_SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
with (L/'episode-diagnosis.csv').open('w',newline='') as f:
 fields=list(rows[0]);w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
 for row in rows:w.writerow({k:json.dumps(v) if isinstance(v,(list,dict)) else v for k,v in row.items()})
text=['PhysicalRSI：闭爪后停止点诊断','',
'本轮问题：此前轨迹精简消除了活动执行中的步数耗尽，但5个布局仍在闭爪后出现规划拒绝。本轮固定同一候选、记忆与轨迹选择，在已暴露布局0、1、4旁路记录物体真实位姿、机械臂状态和原始规划结果。',
'实验只新增日志，没有把仿真真值提供给候选，没有改评分或1100步预算，没有新增API或自动策略晋升。新增诊断日志的墙钟开销不能作为速度提升证据。',
'子集运行编号0、1、2分别对应原布局0、1、4；请使用source_layout_id识别原始场景。','',
'逐布局原始摘要：']+[json.dumps(r,ensure_ascii=False) for r in rows]+['','日志开销（毫秒）：'+json.dumps(a['logging_ms']),
'','证据索引：native-validation/analysis/postgrasp-analysis.json；primitive-alignment.csv；backend-traces/；sim-diagnostics/；原生_result.json和9段原始视频；figures/。',
'','解释限制：物体根坐标上升不自动证明稳定抓持；单一末帧不能证明任务成功。规划器状态要结合目标、起始状态和原始日志判断，不能仅由no_collision_free_path断定发生碰撞。三场景均已暴露，没有独立泛化结论。候选代码与接口诊断的缺陷不能直接归为官方通用框架缺陷。',
'','进一步机制判断与后续单变量处理由INTERPRETATION.txt补充，先依据原始反馈核查。']
(L/'REPORT.txt').write_text('\n'.join(text)+'\n')
print(json.dumps(dict(state='completed',cases=[{k:v for k,v in r.items() if k not in ['object_motion','solver_statuses']} for r in rows]),ensure_ascii=False))
