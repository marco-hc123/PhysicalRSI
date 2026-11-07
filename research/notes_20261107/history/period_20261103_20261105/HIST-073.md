# HIST-073 · 原生动作序列、抬升门控与预算诊断

- 原始事件：2026-11-05（原生结果后的探索性分析），北京时间；未留存精确时间的事件只标日期，不从mtime推算。
- 登记：2026-11-05 16:46（北京时间）；本期科学证据截点：2026-11-05 16:15:35（北京时间）。
- 性质：35回合事后机制分析，不新增回合。周志：[EXP-2026W45-013](../../LOGS/2026-W45.md#exp-2026w45-013)

## 目的

解释为何增强候选更容易执行动作，却仍不能完成任务。

## 实际完成的工作

按process call_id数值顺序重建30个候选回合206次调用，比较首次目标与停止位置；逐项核对aug3源码、RGBReader和返回scene；将任务评分与对象消失、类别ID和API返回区别开。

## 指标及结果

首次approach拒绝baseline12/15、augmented0/15；已完成approach分别9/50，拒绝15/5。aug3五布局各完成3次approach后重看scene并正常return，无第四次搬运approach，也非RPC耗尽或规划拒绝。它要求观察高度升高>0.025m，而读取器用类别HEIGHT+固定桌面高度；5例最后scene均无法满足该谓词。aug1-layout4已进入第二物体，完成primitive948步=924 approach+24 gripper，占1100的86.2%。

## 解释与限制

反馈改变目标选择与动作推进有证据；aug3的抬升门控与当前观察接口能力不匹配有源码及原始返回支持。

固定/缺失的观测高度不能证明真实抓取失败；ID为类别加X，不是稳定跟踪ID，对象消失也不等于放入篮筐。948步之外还有未完成调用，预算瓶颈仍属机制假设；现有sim/planner均见0.004，不能直接称dt bug。目标XYZ、手臂和姿态多处同时改变，不能单因果归结于降低Z。事后ground truth仅作关联分析，未作为候选输入。

## 复核与下一步

本次没有重跑上述历史任务。冻结协议、源代码与原始执行回执是复现依据；历史脚本不能原地再次执行覆盖产物。

候选下一步可在独立方案中分别检验可观测抬升条件、首目标高度/姿态/手臂、有限恢复与控制预算；本次只记录，不实施修复。

## 原件与来源

- [ordered-call-traces.json](../../../../experiments/system2_followup_through_20261105/stages/31_rgb_validation/analysis/ordered-call-traces.json) — SHA256 `5c1014c9296cdb6e2a624713f48d8a7613020a4c8f836c364ab7587e3d27648d`
- [actor-diagnostics.csv](../../../../experiments/system2_followup_through_20261105/stages/31_rgb_validation/analysis/actor-diagnostics.csv) — SHA256 `572b206f33c3f8737f505a32f3b4e090c367fd71d3406e643f6f80a602dc267f`
- [lift-gate-diagnosis.json](../../../../experiments/system2_followup_through_20261105/stages/31_rgb_validation/analysis/lift-gate-diagnosis.json) — SHA256 `fb67f4ab6bd871d9d96bb5636a3001128c78b1cc6b27eab2c63c0246e0b91b7d`
- [case-study-augmented1-layout4.json](../../../../experiments/system2_followup_through_20261105/stages/31_rgb_validation/analysis/case-study-augmented1-layout4.json) — SHA256 `695474828ea67fcc1485af79839b571cfaf3ccde495d2b03b4a24a6cbfab9f3f`
- [first-target-contrasts.json](../../../../experiments/system2_followup_through_20261105/stages/31_rgb_validation/analysis/first-target-contrasts.json) — SHA256 `40030a7fbf5e34e7100d7effd36ea653f02b53c3bcc86f66eab83ef40dbe4a47`
- released_rgb_reader.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/31_system2_rgb_validation/20261105_v1/analysis/reference-contract/released_rgb_reader.py`） — SHA256 `1e6b77c65f24340423f7d0662bd467bad3dc25655980fb4312afda711d9420e6`
- [augmented_3.py](../../../../experiments/system2_followup_through_20261105/stages/29_feedback_generation/candidates/augmented_3/candidate.py) — SHA256 `c083d296b7708688356311749727ce410c8a0d09d2380f1722a94cea2bccd4db`
