# 11月6–8日：System 2诊断、受控干预与两任务试验

这里归档实验室批次32–43，接续[截至11月5日的批次27–31](../system2_followup_through_20261105/README.md)。范围是11月8日本次取证时已完成、可由原件确认的实验，不是提前封存当日尚未发生的工作。本次整理没有运行新实验、请求模型或重新选择策略。

## 从研究问题到证据

研究链条由“为何提前退出”推进到“为什么完成更多动作却未提高整任务分数”，再以冻结的执行接口测试候选数量、执行反馈和第二种任务。完整过程见[本周阶段报告](../../reports/research_week_20261102_20261108/01_阶段研究报告.txt)，结论见[RESULTS](../../docs/RESULTS.md)，研究日志见[11月5–8日记录](../../research/notes_20261108/HISTORY_2026-11-05_to_2026-11-08.md)。

| 完成日期 | 批次 | 实验内容 | 新增有终态评分执行 | 核心结果与原件 |
|---|---|---|---:|---|
| 11-06 | 32 | 抬升guard、撤离目标与预算诊断 | 20 | 整项guard旁路五例出现一例15分；撤离目标修正后两组分数仍相同。[汇总](../../reports/research_week_20261102_20261108/06_batch_evidence/32_system2_lift_gate_diagnosis/20261106_v1/FINAL_SUMMARY.json) |
| 11-06 | 33 | 原反馈/能力说明各3候选 | 30 | 六候选均为`[0,0,0,0,15]`；原接口说明后来被证实不一致，解释需收窄。[汇总](../../reports/research_week_20261102_20261108/06_batch_evidence/33_system2_capability_feedback/20261106_v1/FINAL_SUMMARY.json) |
| 11-06 | 34 | dense/发布waypoint筛选 | 10 | 完成approach增加、活动预算中止减少；整任务得分不变。[汇总](../../reports/research_week_20261102_20261108/06_batch_evidence/34_system2_trajectory_contract/20261106_v1/FINAL_SUMMARY.json) |
| 11-07 | 35 | 三布局旁路物体日志与求解诊断 | 3 | 得分`[0,0,15]`，抬升、稳定抓持、物体送达分开解释。[汇总](../../reports/research_week_20261102_20261108/06_batch_evidence/35_system2_postgrasp_diagnosis/20261107_v1/FINAL_SUMMARY.json) |
| 11-07 | 36 | 实测夹爪开度/最近闭爪命令保持 | 10 | 修正命令语义，配对分数没有提高。[汇总](../../reports/research_week_20261102_20261108/06_batch_evidence/36_system2_gripper_command_contract/20261107_v1/FINAL_SUMMARY.json) |
| 11-07 | 37 | 抽象覆盖检查与发布完整技能参照 | 5 | 发布参照均分17、成功0/5；能力与接口不同，不作单因素排名。[汇总](../../reports/research_week_20261102_20261108/06_batch_evidence/37_system2_candidate_capacity/20261107_v1/FINAL_SUMMARY.json) |
| 11-07 | 38 | 运输目标偏移 | 10 | 规划拒绝5→0、动作推进增加；两组仍`[0,0,0,0,15]`。[汇总](../../reports/research_week_20261102_20261108/06_batch_evidence/38_system2_transport_destination/20261107_v1/FINAL_SUMMARY.json) |
| 11-07 | 39 | 固定六次选物循环 | 5 | 对照复用38，不增算；多完成两次运输，分数未变。[汇总](../../reports/research_week_20261102_20261108/06_batch_evidence/39_system2_observation_loop/20261107_v1/FINAL_SUMMARY.json) |
| 11-07 | 40 | 零动作规划拒绝的包装返回修正 | 5 | 对照复用39；3次换臂分支完成，分数未提高。[汇总](../../reports/research_week_20261102_20261108/06_batch_evidence/40_system2_rejection_contract/20261107_v1/FINAL_SUMMARY.json) |
| 11-07 | 41 | 单周期搬运能力下限与发布首周期参照 | 10 | 物体送达代理与原生整任务评分不同，发布参照部分送达发生在异常清理中。[汇总](../../reports/research_week_20261102_20261108/06_batch_evidence/41_system2_skill_chain_floor/20261107_v1/FINAL_SUMMARY.json) |
| 11-07 | 42 | 5候选池、人工XY对照、第二轮3生成、独立布局 | 60 | 2份第二轮候选未准入且无分数；所有自动搜索选择保留父策略。[汇总](../../reports/research_week_20261102_20261108/06_batch_evidence/42_system2_search_execution_controls/20261107_v1/FINAL_SUMMARY.json) |
| 11-08 | 43 | 分类/抓取两任务basic与执行反馈比较 | 89 | 88正式评分＋1准备smoke；另2中断无评分；两任务两条件均保留parent。[汇总](../../reports/research_week_20261102_20261108/06_batch_evidence/43_system2_multitask/20261108_v1/native-validation/FINAL_SUMMARY.json) |

日期按原汇总和执行回执确定，不依据文件修改时间。批次32–34共60、35–42共108、43共89，合计257个新有评分执行。完整周账目另包含11月2日20个和11月5日35个，共312。此总数用于检查是否遗漏，不是可比较的成功率分母。

## 最晚一轮实际得到什么

11月8日每任务五个开发布局、两条件各三个独立生成候选。分类父策略及六候选均0分；抓取父策略3/5成功、均分60，basic候选均分60/60/40，执行反馈40/60/60。没有候选满足“平均分严格提高且成功数不减”，所以两任务的两条件都保留父策略。

选择冻结后每任务准备五个新布局，源码相同的父策略视图只执行一次。分类父策略为`[15,未完成,15,0,0]`，抓取父策略为`[0,未完成,100,0,0]`；各只有4个有效评分。两次未完成均为冻结轨迹跟踪检查中断，分数保持未知，没有重试、放宽阈值或填0。pi05抓取独立参照0/5；神经参照与可编辑代码的接口不同。

抓取候选存在原生成功，证明部分指定物体抬升可执行；它不证明稳定运输或分类完成，也没有超过该任务的代码父策略。分类增强反馈的15次执行均在第四个运输approach收到明确拒绝后返回；前三个调用返回不等同于稳定抓持。更细证据见[停止原因与记录](../../reports/research_week_20261102_20261108/07_verification/multitask/)。

## 原始代码、历史适配与更正

`stages/`保存按批次选出的协议、源码、候选、运行/分析程序和关键结果；深层重复文本由公开来源索引映射到精确文件或无损对象。检索完整来源使用：

```bash
python3 -B tools/read_week_evidence.py --search '40_system2_rejection_contract'
python3 -B tools/read_week_evidence.py --search '43_system2_multitask'
```

生成候选、人工诊断副本、发布技能及部署适配各按原来源和哈希区分。代码里的原绝对路径、服务端口和防重跑断言保留其历史意义；这些程序不是新的启动指令，也不应在已完成目录原地重跑。原始上游和旧冻结集成目录未被后续修正倒写。

[历史契约更正](../../reports/research_week_20261102_20261108/06_batch_evidence/40_system2_rejection_contract/20261107_v1/HISTORICAL_CONTRACT_CORRECTION.txt)必须随旧报告阅读：后台的零动作拒绝字典曾在本研究包装层变为RuntimeError；能力说明与CPU夹具没有完整覆盖候选实际收到的行为。批次39旧“精确终止回放”遗漏这一包装，并且停止边界可被候选捕获；后续版本修正解释，不改分数。不能把这项适配问题归给冻结官方源码，也不能因修复后分数仍低就否定一致接口下的所有反馈方法。

批次42第二轮两份含`nonlocal`的候选被研究准入层拒绝，而原请求没有告知该禁令；保存生成原件、拒绝原因和无评分状态。人工重写这些代码后产生的结果若将来测试，应另立干预，不能冒充原轮次。

## Token与核验边界

本目录新增付费生成为批次33的6次、42的8次、43的12次，共26次、375,220 Token，保存费率估算$1.4614855。费用不是实扣；缓存是输入子集，reasoning包含在输出。执行冻结代码、VLA和本次整理没有新增高层请求，本地仿真与推理仍消耗计算和墙钟。

完整周包可由下列只读工具核验，源路径覆盖及综合结果另外保存；各检查有重叠，不能相加计数：

```bash
python3 -B tools/verify_weekly_package.py --package reports/research_week_20261102_20261108
```

[来源覆盖](../../provenance/week-coverage-20261108.json) · [本次核验](../../provenance/week-verification-20261108.json) · [逐回合表](../../reports/research_week_20261102_20261108/03_data/native_episodes_all.csv) · [API逐次账目](../../reports/research_week_20261102_20261108/03_data/api_requests.csv) · [中断独立表](../../reports/research_week_20261102_20261108/03_data/interrupted_native_attempts_batch43.csv)

完整原视频、逐帧观测、权重、安装环境和敏感私密运行配置继续保留实验室。公开周包中的精选媒体用于说明，不是独立抽样或评分依据。下一步研究需要新协议，本次不启动训练、补跑或新增候选生成。
