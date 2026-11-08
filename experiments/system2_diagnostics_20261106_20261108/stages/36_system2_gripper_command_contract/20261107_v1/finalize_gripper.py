"""CPU-only analysis of the verified10case command contract archive."""
from pathlib import Path
import json,hashlib,datetime,csv,math,os
L=Path(__file__).resolve().parent;N=L/'native-validation'
def read(p):return json.loads(p.read_text())
def lines(p):return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
v=read(N/'migration/ARCHIVE_VERIFIED.json');assert v['state']=='verified' and v['native_cases']==10
m=read(N/'analysis/matrix-analysis.json');a=read(N/'analysis/postgrasp-analysis.json');assert a['state']=='passed'
proposal=read(L.parent.parent/'33_system2_capability_feedback/20261106_v1/candidates/capability_feedback_2/proposal.json')
rows=[];bindings=[]
for actor in m['actors']:
 p=(N/actor['process_record']).parents[2]/'root/input.json';packet=read(p)
 assert packet['source']==proposal['source'] and packet['memory']==proposal['memory']
 bindings.append(dict(condition=actor['condition'],actor=actor['actor_episode_id'],source_exact=True,memory_exact=True,input_sha256=sha(p)))
 condition=actor['condition'];i=actor['mapped_layout_id'];assert actor['mapping_qualified']
 path=N/'backend-traces'/condition/actor['actor_episode_id']/'0/applied-actions.jsonl'
 actions=lines(path);comparisons=0;mismatches=0;closed_comparisons=0;closed_mismatches=0;changed=0
 for x in actions:
  changed+=x['input_action']!=x['applied_action']
  for arm,value in x['last_explicit_commands'].items():
   vals=x['applied_action'][arm+'_ee_joint_state'];different=any(abs(t-value)>1e-6 for t in vals)
   comparisons+=1;mismatches+=different
   if value==0:closed_comparisons+=1;closed_mismatches+=different
 if condition=='latched_command':assert mismatches==0
 outcome=next(x for x in m['episodes'] if x['condition']==condition and x['layout_id']==i)
 sim=next(x for x in a['actors'] if x['condition']==condition and x['actor_episode_id']==actor['actor_episode_id'])
 primitives=[x for x in a['primitives'] if x['condition']==condition and x['actor_episode_id']==actor['actor_episode_id']]
 failures=[x for x in primitives if (x.get('result') or {}).get('primitive_error')]
 rows.append(dict(condition=condition,layout_id=i,score_100=100*outcome['normalized_score'],success=outcome['success'],native_actions=outcome['native_action_count'],completed_approaches=actor['accepted_approach_calls'],rejected_approaches=actor['rejected_approach_calls'],active_budget_cancel=actor['native_step_limit_cancelled'],completed_applied_actions=len(actions),command_comparisons=comparisons,command_mismatches=mismatches,closed_command_comparisons=closed_comparisons,closed_command_mismatches=closed_mismatches,actions_changed=changed,maximum_any_object_root_lift_m=max(x['max_dz_m'] for k,x in sim['objects'].items() if k.startswith('cat')),last_failed_target=failures[-1]['kwargs'] if failures else None,actor=actor['actor_episode_id']))
rows.sort(key=lambda x:(x['condition'],x['layout_id']));groups=[]
for name in ['measured_state_control','latched_command']:
 r=[x for x in rows if x['condition']==name];assert len(r)==5
 groups.append(dict(condition=name,cases=5,successes=sum(x['success'] for x in r),scores_by_layout_100=[x['score_100'] for x in r],mean_score_100=sum(x['score_100'] for x in r)/5,completed_approaches=sum(x['completed_approaches'] for x in r),rejected_approaches=sum(x['rejected_approaches'] for x in r),active_budget_cancels=sum(x['active_budget_cancel'] for x in r),closed_command_mismatches=sum(x['closed_command_mismatches'] for x in r),closed_command_comparisons=sum(x['closed_command_comparisons'] for x in r)))
pairs=[]
for i in range(5):
 control=next(x for x in rows if x['condition']=='measured_state_control' and x['layout_id']==i);treatment=next(x for x in rows if x['condition']=='latched_command' and x['layout_id']==i)
 pairs.append(dict(layout_id=i,control_score=control['score_100'],treatment_score=treatment['score_100'],score_delta=treatment['score_100']-control['score_100'],control_max_any_object_lift=control['maximum_any_object_root_lift_m'],treatment_max_any_object_lift=treatment['maximum_any_object_root_lift_m']))
summary=dict(state='completed',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),accounting=dict(new_native_cases=10,new_raw_videos=30,new_api_calls=0,new_generated_candidates=0,lab_gpu_used=False,policy_promotions=0),groups=groups,cases=rows,pairs=pairs,source_memory_bindings=bindings,archive=v,retained_policy='pi05',interpretation=dict(command_retention_verified=groups[1]['closed_command_mismatches']==0,score_improved_in_any_pair=any(x['score_delta']>0 for x in pairs),mean_score_delta=groups[1]['mean_score_100']-groups[0]['mean_score_100'],full_success_delta=groups[1]['successes']-groups[0]['successes']),limits=['Manual primitive contract correction, not newly generated System2 self-improvement.','Five previously exposed layouts; no independent generalization.','Maximum height of any object is descriptive and does not prove selected-object stable grasp or task success.','Both conditions retain measured observations; only explicit command retention changes.','Native action count includes idle hold after candidate return; completed primitive actions exclude unfinished calls.'])
(L/'FINAL_SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
for name,data in [('episode-results.csv',rows),('paired-layouts.csv',pairs),('group-summary.csv',groups)]:
 with (L/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows({k:json.dumps(v) if isinstance(v,(dict,list)) else v for k,v in r.items()} for r in data)
os.environ['MPLCONFIGDIR']=str(L/'analysis-cache/matplotlib')
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
F=L/'figures';F.mkdir(exist_ok=True);fig,ax=plt.subplots(figsize=(7,4))
for offset,g in [(-.18,groups[0]),(.18,groups[1])]:ax.bar([i+offset for i in range(5)],g['scores_by_layout_100'],width=.35,label=g['condition'])
ax.set(xticks=range(5),xlabel='Previously exposed layout',ylabel='Native score / 100',ylim=(0,100),title='Same candidate; explicit gripper command retention');ax.legend(fontsize=8);fig.tight_layout()
for ext in ['png','svg']:fig.savefig(F/('paired_scores.'+ext),dpi=150)
plt.close(fig)
text=['抓手命令保持对照：最终分析','', '研究问题：显式闭爪后，后续机械臂动作是否继续保持闭爪目标？本轮固定候选、记忆、感知、规划目标、6步抓手命令、轨迹精简、1100步和原生评分。原方式与目标保持方式各5个新回合。','', '组别结果：']+[json.dumps(x,ensure_ascii=False) for x in groups]+['','逐布局分数差：'+json.dumps(pairs,ensure_ascii=False),'','执行接口结论：处理组所有已完成动作均保持最近的显式抓手命令；观测仍返回实测开度。原方式的目标偏差计数见表。抓手目标修正与物体抓持成功、分类得分是三个不同层面。','任务结论：'+('至少一对布局出现分数增加，应按逐布局表描述，尚不足以证明稳定泛化。' if summary['interpretation']['score_improved_in_any_pair'] else '本轮没有任何配对布局的得分增加；接口修正未转化为该候选的任务得分改善。'),'','下一步：在相同布局运行原有完整分类控制器，区分生成候选的任务覆盖/恢复逻辑与已有技能执行能力。另做理想接口下的循环上限审计；其输出不计为仿真成绩。','', '限制：'+ '\n'.join(summary['limits']),'','证据：native-validation/analysis/；backend-traces/中的applied-actions.jsonl；sim-diagnostics/；30段原始视频；episode-results.csv、paired-layouts.csv、figures/。']
(L/'REPORT.txt').write_text('\n'.join(text)+'\n')
print(json.dumps(dict(state='completed',groups=groups,interpretation=summary['interpretation']),ensure_ascii=False))
