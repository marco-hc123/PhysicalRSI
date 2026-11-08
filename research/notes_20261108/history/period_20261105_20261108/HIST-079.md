# HIST-079 · 轨迹采样执行契约的匹配对照

- 原始事件：本批最终状态生成于2026-11-06 15:17:08（北京时间）；事件范围依原协议和逐回合回执，未用文件mtime代替发生时间。
- 回溯登记：2026-11-08 19:54（北京时间）。科学材料观察截至2026-11-08 19:49:30（北京时间；科研档案快照，实验结果已于19:44检查）；不是11月8日全天预填。
- 性质：已执行实验及机制分析的回溯核对；周志[EXP-2026W45-017](../../LOGS/2026-W45.md#exp-2026w45-017)。本次整理没有重新执行。

## 目的与假设

判断逐个发送dense轨迹点是否造成不必要的执行预算消耗。 固定候选后采用发布waypoint筛选，能否减少预算中止并改善整任务评分。

## 实际工作

固定capability_feedback_2、评分和1100步，对照dense与发布筛选函数，各五布局。未移植完整发布控制器。

## 指标与结论

10新回合；两组各[0,0,0,0,15]、成功0/5。完成approach18→35，活动调用预算中止3→0，已完成primitive步数4096→418；整组墙钟约1029→1013秒。

轨迹筛选改善动作推进并消除这组预算中止，未增加配对分数。

## 解释与限制

primitive计数不含取消动作与所有保持步，不能说总动作或墙钟缩短十倍。发布技能其他到位、抓持和IK机制不在此处理内。

不同任务、执行条件、重复布局、复用对照与生成样本分别计数。原报告是当时快照，若与后续契约更正冲突，以标有来源的更正解释为准，不改原分数。

## 复核与下一步

检查推进后的下一失败调用与真实抓持状态。 原始脚本与协议是复现依据，不能原地重跑覆盖结果。本批加入[整周执行账本](../../evidence/period_20261105_20261108/tables/native_episodes_all.json)，没有把旧回合重复计为新执行。

## 原件与来源

- [20261106_v1/protocol.json](../../evidence/period_20261105_20261108/stages/34/20261106_v1/protocol.json) — SHA256 `64150745266c14c1406b842ad592576a461f8c6f228cb7af94461d958eaf4d32`；实验室原件 `/mnt/data/joey_tr/physical-RSI/result/34_system2_trajectory_contract/20261106_v1/protocol.json`。
- [20261106_v1/FINAL_SUMMARY.json](../../evidence/period_20261105_20261108/stages/34/20261106_v1/FINAL_SUMMARY.json) — SHA256 `de68c4ab8989da27c8fa645d6bd103f912bb6e4e335e46c0e947a74c805360ee`；实验室原件 `/mnt/data/joey_tr/physical-RSI/result/34_system2_trajectory_contract/20261106_v1/FINAL_SUMMARY.json`。
- [20261106_v1/REPORT.txt](../../evidence/period_20261105_20261108/stages/34/20261106_v1/REPORT.txt) — SHA256 `01a2b58916b2c2943b4b42e6e54f055d359c3120055c2ba341db87fd737a6276`；实验室原件 `/mnt/data/joey_tr/physical-RSI/result/34_system2_trajectory_contract/20261106_v1/REPORT.txt`。

另见[独立原始回执与usage复算](../../evidence/period_20261105_20261108/audit/independent-recomputation.json)、[专项解释复核](../../evidence/period_20261105_20261108/audit/SCIENCE_REVIEW_ZH.md)。

## 具体复现入口补充

精确入口 `native-validation/run_native.py`，SHA256 `a9a69800b96785779c796e91b72e1cdbdd3874ea8d1a197afea8f023422cb14b`。development:运行ID[0,1,2,3,4]/源ID[0,1,2,3,4]；classify_objects原生1100步。

已读取2份本批native/request.json，记录原生执行seed=[0]；逐件路径/SHA见复现索引。这不是布局生成seed；场景以各阶段layout ID与SHA256绑定，不把求解器seed或重复布局当成独立场景。

原始源文件、原生子进程argv（若保存）、分开的软件版本及硬件事实见[批次34复现索引](../../evidence/period_20261105_20261108/reproduction/README.md#batch-34)。该索引区分已保存命令与无法确认项，本次不运行历史程序。
