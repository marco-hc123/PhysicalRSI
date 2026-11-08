import json,datetime
from pathlib import Path
L=Path('/mnt/data/joey_tr/physical-RSI/result/33_system2_capability_feedback/20261106_v1')
assert not (L/'EVIDENCE_INDEX.json').exists()
s=json.loads((L/'execution-analysis/summary.json').read_text()); assert sum(g['error_events'] for g in s['groups'])==24
p=L/'INTERPRETATION.txt'; assert not p.exists()
text='''逐动作核查后的结论（补充主报告）
1. 6个新生成候选在同5个布局的得分均为[0,0,0,0,15]/100，均无完整成功。明确接口能力反馈没有在本轮带来分数改善。两组都收到相同的最新失败源码和停止事实；这里的对照并非旧的原始简短反馈baseline。
2. 24次明确的规划错误中，12次位于已完成闭爪命令后、下一次开爪命令前；12次位于闭爪再开爪之后。没有一次位于首次闭爪之前，且24次错误后都没有继续调用approach。处理组增加的接触前换臂分支没有覆盖实际失败阶段。命令上下文不等于真实接触或抓取状态。
3. 两组各3次、共6次在活动动作未完成时被1100步上限终止；其余24次为候选遇到规划拒绝后返回。候选返回后评估器仍可能保持姿态至步数上限，不能把所有1100步回合都称为执行预算耗尽。
4. 当前兼容层把规划器非Success统一投影为no_collision_free_path，因此仅凭这个名称无法区分IK失败、碰撞约束或其他规划失败。不得据此断言全部是碰撞，更不能断言PhysicalRSI核心框架有错误。
5. 代码对照发现，发布技能使用thin_native_path筛选规划waypoint，当前兼容执行逐点发送全部采样。接下来的10个回合将固定capability_feedback_2、同5布局、1100步、评分和感知，比较全部点与发布的有界筛选函数；不增加API调用。筛选同时改变控制时序和插值，保留端点不等于连续运动完全相同；这属于人工兼容层诊断，不是System2自动改进结果。
6. 抽查layout4的legacy_feedback_1与capability_feedback_2末帧，画面完整、物体仍散布桌面；权威回执均是15/100且success=false。静态图只作现象展示，不能推断完整搬运轨迹。6个候选同布局末帧与时间/版本索引保存在video-review，90段原视频已完整解码。
7. 本轮6次API估算0.1846203美元，累计已核查0.3778452美元；费用非发票实扣。原生30回合无语言模型API调用。仍保留pi05，未做新候选晋升或独立布局验收。
8. 回传时一次SSH流中断，保留部分文件并按哈希补传，最终23146个文件全部匹配；此为迁移事件，不是实验失败，不重复计算实验回合。记录见transfer-recovery/recovery-report.json。
'''
p.write_text(text)
with (L/'REPORT.txt').open('a') as f:f.write('\n九、已核实的机制解释\n'+text)
v=dict(state='reviewed',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),frames=['legacy_feedback_1_layout4_head_final.png','capability_feedback_2_layout4_head_final.png'],finding='Intact frames; several objects remain on table. Receipts show15/100 and false success; no complete manipulation inferred from single frames.')
(L/'video-review/visual-review.json').write_text(json.dumps(v,indent=2)+'\n')
status=dict(state='completed_pending_seal',native_cases=30,videos=90,archive_verified=True,next_stage='34_system2_trajectory_contract/20261106_v1',api_calls=6,active_experiment_processes=[])
(L/'coordination-status.json').write_text(json.dumps(status,indent=2)+'\n')
with (L/'CONTINUATION.txt').open('a') as f:f.write('\n'+json.dumps(status,ensure_ascii=False)+'\n')
print(json.dumps(status))
