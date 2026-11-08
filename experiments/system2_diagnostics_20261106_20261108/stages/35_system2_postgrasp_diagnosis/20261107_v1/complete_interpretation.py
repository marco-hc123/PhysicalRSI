from pathlib import Path
import json,datetime,hashlib,csv
L=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
s=read(L/'FINAL_SUMMARY.json');p=read(L/'goal-probes/summary.json');r=read(L/'goal-probes/results.json');assert p['state']=='completed' and len(r)==81
s['accounting'].update(offline_solver_calls=81,offline_new_native_cases=0,lab_gpu_used=True,lab_gpu_limit=1,invalid_deployment_attempts=1,invalid_deployment_valid_cases=0)
s['offline_probe_summary']=p;s['offline_probe_qualifications']=['Only3 recorded failures and9 settings per failure,3seeds within resident solver; no independent layouts','Height/yaw exploration does not prove physical manipulation or geometric impossibility']
s['diagnosis']={'native_failure':'All3 final rejected transport calls returned None before a path; no actuator steps executed for those rejected calls.','offline_corrobation':'All9 baseline solver calls fail; all45 baseline internal IK calls have zero success seeds.','bounded_recovery':'Only original layout0 has recovering settings: yaw+15deg atsameheight, or Z-4cm withany tested yaw;12/81totalprobes return trajectories. Layout1and4 all54probesfail.','contract_issue':'Frozen approach constructs each action from measured state, including gripper. After explicit close=0 while object blocks actual aperture~.44, subsequent motion commands measured aperture rather than retaining0. Released Motion separately retains self.grip. Physical benefit requires next matched native comparison.','scope':'Finding concerns frozen primitive execution contract used in this reproduction, not a blanket claim about all official versions or System2 algorithms.'}
s['next_stage']='/mnt/data/joey_tr/physical-RSI/result/36_system2_gripper_command_contract/20261107_v1'
(L/'FINAL_SUMMARY.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
with (L/'goal-probes/summary.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(p['groups'][0]));w.writeheader();w.writerows(p['groups'])
text='''闭爪后诊断结论（结合原始回执、真值旁路、源码和离线检查）

1. 新增3个有效原生回合，原布局0、1、4得分0、0、15/100，完整成功0/3。9段视频全部解码通过。新增日志只写旁路文件，未提供给候选。首次接入因新日志包装函数签名和钩子优先级错误中止，记录保留；0个有效回合，不计入策略0分。修复后3回合为正式诊断数据。
2. 三个停止点均是闭爪之后的运输approach，原始plan_pose返回None，尚未生成可执行轨迹；此失败调用本身动作数为0。native的1100步包含候选返回后的保持步骤，不能据此说候选持续执行了1100步。
3. 81次离线检查固定这3个真实失败调用的起始关节、目标XY、手臂和规划配置，探索Z变化0/-4/+4cm与世界Z轴yaw变化0/-15/+15度的9种组合，各3个seed。原始目标9/9失败；其中45次内部IK调用均为0个成功seed。仅布局0的4种设置返回轨迹，共12/81；布局1和4的54次均失败。不是81个机器人回合，也不能由有限求解失败证明几何绝对不可达。
4. IK的feasible和位姿误差需分别看：布局0原目标虽位置误差很小，但候选IK解feasible为False；其他布局常有明显位置误差。具体碰撞项/关节约束项尚未完整拆分，不能统一写成碰撞或单纯够不到。rawplan没有status枚举则记为未知，不能自造状态码。
5. 真值旁路显示布局0被操作物体根高度最高上升2.14cm，随后回到桌面；这不支持稳定抓起的结论。布局1和4有物体上升约10cm并移动到篮筐附近，但仍不满足完整任务评分。机器人到达lift目标和物体成功抓持是两个指标。
6. 新的执行契约疑点：gripper(close=0)之后，approach每步重新读实际gripper开度并作为动作输出。物体阻挡时实际开度不会为0，因而后续移动没有继续保持闭爪目标。发布Motion控制器则独立保存self.grip目标。下一轮只改变此目标保持行为；不同时改变运输目标、反馈、候选、评分或1100步上限。
7. 本轮属于人工诊断，没有新增System2候选，没有策略晋升，也没有证明System2已产生改进。下一轮若夹持改善而规划仍失败，应分别记录两个层面的结果，再推进可执行目标/动作恢复问题。

证据：native-validation/analysis/postgrasp-analysis.json及primitive-alignment.csv；native-validation/backend-traces-v2/；native-validation/sim-diagnostics/；goal-probes/中的protocol/results/probes/runtime/write-isolation/gpu-after；references/motion_planner.py；video-review/frame-index.json；figures/。
资源：离线检查只使用经空闲核查的GPU0；worker已退出，gpu-after记录本项目占用归零。没有修改项目文件夹外的实验室文件，没有付费API。
'''
(L/'INTERPRETATION.txt').write_text(text)
(L/'NEXT_EXPERIMENT.txt').write_text('已冻结并开展：相同capability_feedback_2与五个已暴露布局，measured_state_control和latched_command各5个新回合。只改变后续动作是否保留最近的显式gripper目标；保持测量观测、目标位姿、6步抓手命令、轨迹精简、1100步和评分不变。记录动作目标、物体抬升与运输、规划停止点和原生分数。新阶段独立记账，不能重计本轮3回合。\n')
print(json.dumps(dict(state='interpretation_written',native=3,solver_probes=81,video=9)))
