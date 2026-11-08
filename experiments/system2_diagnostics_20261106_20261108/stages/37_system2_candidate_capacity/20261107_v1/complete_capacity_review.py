from pathlib import Path
import json,datetime
L=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
s=read(L/'FINAL_SUMMARY.json');p=read(L/'destination-probes/execution/summary.json');v=read(L/'destination-probes/execution/ARCHIVE_VERIFIED.json');assert p['solver_calls']==18 and v['state']=='verified'
mechanism=read(L/'reference-mechanism.json');s['accounting'].update(offline_solver_calls=18,lab_gpu_precheck_executed_solver_calls=0,invalid_controller_setups=2,invalid_controller_native_cases=0)
s['destination_feasibility']=p;s['reference_stops']=mechanism['rows'];s['next_stage']='/mnt/data/joey_tr/physical-RSI/result/38_system2_transport_destination/20261107_v1'
s['interpretation']={'candidate_mean_score_100':3.,'reference_mean_score_100':17.,'reference_full_successes':0,'reference_n':5,'not_a_system2_improvement':True,'capability_gap_audit':'CAPABILITY_GAP_AUDIT.txt','reference_layout4':'Score40; two pens remain outside intended basket; trace reports stationary source and both attempts exhausted, then return-home. complete_hold is not native success.','offline_original_paths':'0/9','offline_offset_paths':'9/9','offline_not_physical_success':True}
(L/'FINAL_SUMMARY.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
t='''阶段37：机制判断与后续动作

已有完整分类控制器在同一5个暴露布局上的得分为0、15、15、15、40/100，平均17分，完整成功0/5。此前生成候选配合抓手目标保持为0、0、0、0、15，平均3分。差异属于不同控制器的描述性能力参照；完整控制器拥有更多感知、抓取和规划机制，不能把14分均值差归因于单个修改，更不能写成System2新改进。

布局0、1、2、3均在执行了轨迹之后，末端位置未满足1cm的原始到位门槛而停止。对应最后位置误差约1.046、2.367、1.498、1.028cm，旋转误差均小于原0.1rad门槛。末10次等待误差变化很小，单纯继续等待未被证明有效；也不能直接认定阈值错误、碰撞或动力学模型错误。没有改阈值，没有把消除异常当成成功。

布局4程序走到complete_hold并已归位，但原生仍只有40分。终帧可见两支笔没有全部落入指定蓝筐；trace的pen分支记录source visually stationary和all current RGB sources used both attempts。因此这是达到当前重试上限后的收尾，不应写成感知确认了全部成功，也不是完整成功。

起始候选另有两层不足：CPU理想接口下的6循环上限使8/7物体布局留下2/1个物体；真实候选可用的四接口也比完整控制器少RGB形状、实际末端pose和其他规划能力。详见CAPABILITY_GAP_AUDIT.txt。不能将低分直接归为LLM或PhysicalRSI通用框架本身不行。

进一步完成18次离线规划对照：固定3个历史真实失败的起始关节、手臂、姿态和求解器，原目标9次均未返回轨迹，发布技能的第一放置点偏移9次均返回轨迹。3个seed属于同一驻留求解器的重复检查，不是独立场景；它只支持目标可执行性假设，尚未证明抓持/搬运/得分。

据此已启动下一阶段10个新原生回合：原运输目标5个、目标偏移5个；两组都保留已修正的抓手命令、相同轨迹精简与候选其余逻辑。评分、1100步、6次循环和缺少归位这些条件不改，以免混入多个变量。下一阶段看规划停止是否减少、实际对象移动是否改善、原生部分得分及完整成功；没有新模型生成，没有自动策略晋升。

账目：本阶段5个原生回合、15视频、10次CPU抽象覆盖检查、18次离线求解。实验室GPU忙碌检查在CUDA初始化前退出，执行0次求解、占用0张卡；求解在后续空闲执行服务器完成并迁回。两次新启动脚本接入失败均为0个原生回合，分别保留，不作策略0分。

证据：native-validation/；reference-stop-details.csv；endpoint-error-series.csv；reference-mechanism.json；video-review/frame-index.json；destination-probes/execution/；symbolic-capacity-results.json；recent-experiment-ledger.csv。
'''
(L/'INTERPRETATION.txt').write_text(t)
with (L/'REPORT.txt').open('a') as f:f.write('\n最终机制补充和18次离线结果见INTERPRETATION.txt；已开展的下一阶段为38_system2_transport_destination/20261107_v1。\n')
print(json.dumps(dict(state='completed',native_cases=5,offline_solver_calls=18,reference_scores=[0,15,15,15,40],next_stage=s['next_stage'])))
