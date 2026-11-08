"""Evidence-linked retrospective, derived from sealed prior stages and stage38."""
from pathlib import Path
import csv, json, datetime
L=Path(__file__).resolve().parent
R=L.parent.parent
def read(p):return json.loads(p.read_text())
d=read(L/'FINAL_SUMMARY.json');assert d['state']=='completed'
old=R/'37_system2_candidate_capacity/20261107_v1'
ledger=list(csv.DictReader((old/'recent-experiment-ledger.csv').open()))
assert sum(int(x['cases']) for x in ledger)==113
for g in d['groups']:
    ledger.append(dict(stage='38',condition=g['condition'],cases=str(g['cases']),successes=str(g['successes']),mean_score_100=str(g['mean_score_100']),source='38_system2_transport_destination/20261107_v1/FINAL_SUMMARY.json',role='Manual transport destination, fresh paired control; no System2 generation',scores_100=json.dumps(g['scores_by_layout_100'])))
with (L/'recent-experiment-ledger.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(ledger[0]));w.writeheader();w.writerows(ledger)
total=sum(int(x['cases']) for x in ledger)
assert total==123
cases=d['cases'];groups=d['groups'];pairs=d['pairs']
review={
 'state':'completed','updated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'scope':'Stages31 through38: feedback generation, manual mechanism diagnosis and released-skill reference. Earlier reproduction studies remain separate.',
 'actual_new_native_executions':total,'unique_previously_exposed_layouts':5,
 'full_successes':sum(int(x['successes']) for x in ledger),
 'current_stage':d['interpretation'],
 'key_distinctions':['Repeated executions/candidates are not independent layouts.','Manual changes and different-controller references are not automatic System2 gains.','No_path is a solver outcome, not a certificate of geometric impossibility.','Offline solver, symbolic fixture, native execution and evidence reuse are separate accounts.'],
 'current_retained_policy':'pi05','new_api_calls_this_stage':0,
 'failure_attribution':[
  {'issue':'Dynamic height used to gate lift','scope':'Generated candidate assumption versus frozen reproduction perception contract','evidence':'32_system2_lift_gate_diagnosis/20261106_v1/FINAL_SUMMARY.json','established':'Bypassing guard changed one of five scores0to15; dynamicZ is unavailable in current interface','not_established':'All PhysicalRSI versions have this fault'},
  {'issue':'Dense trajectory consumes budget','scope':'Frozen primitive execution adaptation','evidence':'34_system2_trajectory_contract/20261106_v1/FINAL_SUMMARY.json','established':'Completed approaches18to35 and active cancels3to0,scoreunchanged','not_established':'Task success or overall wall-clock speedup'},
  {'issue':'Explicit gripper command not retained','scope':'Frozen primitive adaptation; measured observations distinct from actuator targets','evidence':'36_system2_gripper_command_contract/20261107_v1/FINAL_SUMMARY.json','established':'Closed-command mismatch72of152to0of152,scoreunchanged','not_established':'Stable grasp or later manipulation success'},
  {'issue':'Postgrasp transport destination','scope':'Specific generated candidate target choice in current robot/task configuration','evidence':'38_system2_transport_destination/20261107_v1/FINAL_SUMMARY.json','established':d['interpretation'],'not_established':'Global optimal target or independent generalization'},
  {'issue':'Candidate coverage and capability gap','scope':'Specific saved program and exposed primitive interfaces','evidence':'37_system2_candidate_capacity/20261107_v1/CAPABILITY_GAP_AUDIT.txt','established':'Six-turn ceiling, no explicit home, smaller sensory/action interface than complete released controller','not_established':'LLM or general System2 algorithm intrinsically cannot improve'},
  {'issue':'Released complete skill endpoint/attempt failure','scope':'Observed reference behavior under frozen reproduction conditions','evidence':'37_system2_candidate_capacity/20261107_v1/reference-stop-details.csv','established':'Four endpoint gates stop; remaininglayoutendsretrylimitedwith40/100;0/5fullsuccess','not_established':'Upstream algorithm inherently defective or physics cause isolated'}
 ]}
(L/'RESEARCH_PROGRESS_REVIEW.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
sections=[
 'PhysicalRSI System2：近期改进实验整体审查',
 '',
 '一、先回答有没有进展',
 '有局部得分变化，也有多项执行层面的修复；截至本轮的完整任务成功数应以文末账目为准。不能写成“一点改进都没有”，也不能写成“已经验证System2稳定自改进”。生成、执行、评分和选择是不同环节。',
 '',
 '二、这些实验在回答什么',
 'System2依据旧执行反馈生成候选程序；候选调用感知和动作接口进入原生仿真；原生评估器给分；只有依据冻结的选择规则胜过父策略且通过独立验收，才有理由晋升。本阶段先诊断为什么候选不能完成任务，人工修正不是System2本身的新能力。',
 '',
 '三、按问题递进解释已有结果',
 '1. 反馈是否充分（阶段31，35个回合）。父pi05及三条baseline候选各5布局全部0分；三条augmented候选中，两条在同一个布局各15分，另一条仍全0。增强信息出现局部部分分，但没有完整成功，不能仅凭一次布局结果宣布稳定提升。',
 '2. 是否存在错误的终止判断（阶段32，20个新回合）。一个候选使用当前接口无法给出的真实动态高度来判断抓起，导致提前退出；原版5布局全0，绕过该判断后为0、0、0、0、15。另一组回撤目标修正得分不变，并出现3次活动执行中的预算耗尽。绕过错误判断不是获得了可靠抓取判据。',
 '3. 把能力/错误契约告诉模型是否足够（阶段33，6次生成、30个新回合）。legacy和capability反馈各3候选，各跑5布局，每条都是0、0、0、0、15。增强反馈确实生成了初始规划拒绝后的有限替代手臂逻辑，但真实拒绝多出现在闭爪后，恢复分支没有覆盖该阶段。提示词改变了代码行为，未改变成绩。',
 '4. 动作执行是否浪费步数（阶段34，10个新回合）。固定候选，稠密轨迹与发布技能的轨迹精简方式比较，完成approach从18到35，活动执行的预算取消从3到0，已完成动作数4096到418；两组成绩同为0、0、0、0、15。完整墙钟仍约1029秒和1013秒，不能把动作数下降直接写成整体十倍加速。',
 '5. 具体停在什么位置（阶段35，3个新回合、81次离线求解）。记录闭爪、抬升、运输和求解器输出，发现三例最后的运输调用在产生轨迹前即返回None，失败调用自身执行0步。None只说明此配置下没返回路径，不能编造碰撞原因。81次局部高度/姿态探查仅12次返回路径，不计为机器人成功。',
 '6. 抓手命令是否持续生效（阶段36，10个新回合）。原执行方式把实测开度带入后续动作；保持最近显式命令后，闭爪目标不一致检查从72/152到0/152，两组仍都是0、0、0、0、15。修复目标命令并未证明物体一直抓稳。152是动作×手臂检查次数，不是样本数。',
 '7. 起始对象本身是否太弱（阶段37，5个新回合、10个理想接口检查、18次离线求解）。完整已有分类控制器在同5布局得0、15、15、15、40，平均17分，但完整成功0/5。与平均3分的生成候选相比，它有更多RGB形状、实际末端状态和规划/恢复能力，因此是能力参照，不能归因于单一修复或模型推理差异。四个布局在末端到位门槛停止；最后一个布局因笔未分类且达到重试上限而停在40分。理想接口检查另确认6次循环对8/7物体布局存在覆盖上限，候选也缺少显式归位。',
 '8. 运输目标点是否不合适（阶段38，本轮10个新回合）。固定已修正抓手与轨迹方式，原目标与偏移目标各5。偏移取发布技能的第一放置点惯例，先在3个历史失败状态×3seed中将离线路径0/9变9/9，再进行本轮原生对照；两层证据分别报告。',
 json.dumps(groups,ensure_ascii=False,indent=2),
 '逐布局得分变化：'+json.dumps(pairs,ensure_ascii=False),
 '',
 '四、现在能否归咎于PhysicalRSI本身',
 '不能把所有问题归于官方通用框架，也不能把一切归为个人操作错误。需要区分本次复现接口的执行契约、某一生成程序的具体选择、完整已有技能的环境表现、以及System2生成与选择机制。上面每项都有对应证据范围。没有在相同能力接口和任务条件下排除这些因素前，不能断言LLM太弱或System2机制不成立。',
 '',
 '五、当前结论与后续判据',
 json.dumps(d['interpretation'],ensure_ascii=False),
 '下一轮应由本轮真实失败阶段决定：若运输拒绝解除却仍低分，优先核查搬运后的物体位置、放置和重试；若仍拒绝，检查实际起始关节与离线状态是否相同、失败是否移到另一子阶段。只有最小搬运契约稳定后，再让System2使用同一能力接口，比较反馈/改写机制。最后单独使用未暴露布局验收，不把这5个开发布局的多次复跑称为泛化。',
 '',
 '六、账目及证据',
 f'阶段31至38累计{total}个实际原生执行回合；完整成功合计{review["full_successes"]}。主要重复使用5个开发布局，并非123个独立场景。离线求解、理想接口检查、API生成和历史复用不混入此分母。无新策略晋升，保留pi05。',
 '本轮无API调用、无训练、无实验室GPU使用；此前离线GPU仅在空闲卡上运行一张。最新忙碌检查未启动CUDA，不影响他人进程。',
 '逐组入口见recent-experiment-ledger.csv；问题归因表见RESEARCH_PROGRESS_REVIEW.json。每阶段FINAL_SUMMARY.json、原始native-validation/和EVIDENCE_INDEX.json提供原始回执、视频、执行日志和归档校验。',
 ]
(L/'RESEARCH_PROGRESS_REVIEW.txt').write_text('\n'.join(sections)+'\n')
print(json.dumps(dict(total_native_cases=total,full_successes=review['full_successes'],current_stage=d['interpretation'])))
