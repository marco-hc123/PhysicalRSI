# HIST-077 · 抬升门控消融、感知回放与撤离目标诊断

- 原始事件：本批最终状态生成于2026-11-06 12:02:56（北京时间）；事件范围依原协议和逐回合回执，未用文件mtime代替发生时间。
- 回溯登记：2026-11-08 19:54（北京时间）。科学材料观察截至2026-11-08 19:49:30（北京时间；科研档案快照，实验结果已于19:44检查）；不是11月8日全天预填。
- 性质：已执行实验及机制分析的回溯核对；周志[EXP-2026W45-015](../../LOGS/2026-W45.md#exp-2026w45-015)。本次整理没有重新执行。

## 目的与假设

检验固定高度判断之外的阻塞条件，以及能否把后续动作推进到任务得分。 删除单个高度判断或旁路整个抬升门控，能否让固定候选继续执行；撤离规划可行是否足以完成后续流程。

## 实际工作

固定augmented_3，比较五种guard版本的历史输入回放，原版/整项旁路原生对照，再做撤离目标对照。旁路和目标修改都是人工诊断。

## 指标与结论

20个新有评分回合。原guard五例全0；整项旁路[0,0,0,0,15]。原撤离/返回clearance两组也均[0,0,0,0,15]；完整成功均0。45前缀回放、63规划求解、24轨迹检查、4Reader和2检测探针另计。

单独去Z不足以解除类别、XY和exact-one门控；旁路能推进动作且出现局部分数，但未完成任务。撤离可规划后仍会用尽1100步。

## 解释与限制

探针/回放不是独立机器人回合。无轨迹不能等同绝对不可达；人工旁路不等于模型自改进，历史重放不证明新布局泛化。

不同任务、执行条件、重复布局、复用对照与生成样本分别计数。原报告是当时快照，若与后续契约更正冲突，以标有来源的更正解释为准，不改原分数。

## 复核与下一步

区分感知、候选门控与执行成本，后续结论分别连接批次33和34。 原始脚本与协议是复现依据，不能原地重跑覆盖结果。本批加入[整周执行账本](../../evidence/period_20261105_20261108/tables/native_episodes_all.json)，没有把旧回合重复计为新执行。

## 原件与来源

- [20261106_v1/protocol.json](../../evidence/period_20261105_20261108/stages/32/20261106_v1/protocol.json) — SHA256 `8253029899c6c8c084c7700693dbdc0304dfddbdf54e210a6efed74efd7ba9b6`；实验室原件 `/mnt/data/joey_tr/physical-RSI/result/32_system2_lift_gate_diagnosis/20261106_v1/protocol.json`。
- [20261106_v1/FINAL_SUMMARY.json](../../evidence/period_20261105_20261108/stages/32/20261106_v1/FINAL_SUMMARY.json) — SHA256 `aa618f551a9c843cd4a2b2e82af6def6b337615732dae288177ecc2ee805db00`；实验室原件 `/mnt/data/joey_tr/physical-RSI/result/32_system2_lift_gate_diagnosis/20261106_v1/FINAL_SUMMARY.json`。
- [20261106_v1/REPORT.txt](../../evidence/period_20261105_20261108/stages/32/20261106_v1/REPORT.txt) — SHA256 `e0f2c59a597b6864e6abbfff9b35911299487b7063be14553fc9d8500f57d95b`；实验室原件 `/mnt/data/joey_tr/physical-RSI/result/32_system2_lift_gate_diagnosis/20261106_v1/REPORT.txt`。

另见[独立原始回执与usage复算](../../evidence/period_20261105_20261108/audit/independent-recomputation.json)、[专项解释复核](../../evidence/period_20261105_20261108/audit/SCIENCE_REVIEW_ZH.md)。

## 具体复现入口补充

精确入口 `run_native.py`，SHA256 `2ff862a2b21488af81998c59f9275c4714f140a840a8807b2b70a452e11b9aa8`。lift_guard:运行ID[0,1,2,3,4]/源ID[0,1,2,3,4]；retreat_destination:运行ID[0,1,2,3,4]/源ID[0,1,2,3,4]；classify_objects原生1100步。

已读取3份本批native/request.json，记录原生执行seed=[0]；逐件路径/SHA见复现索引。这不是布局生成seed；场景以各阶段layout ID与SHA256绑定，不把求解器seed或重复布局当成独立场景。

原始源文件、原生子进程argv（若保存）、分开的软件版本及硬件事实见[批次32复现索引](../../evidence/period_20261105_20261108/reproduction/README.md#batch-32)。该索引区分已保存命令与无法确认项，本次不运行历史程序。
