# HIST-081 · 夹爪实际开度与闭爪命令保持对照

- 原始事件：本批最终状态生成于2026-11-07 13:35:17（北京时间）；事件范围依原协议和逐回合回执，未用文件mtime代替发生时间。
- 回溯登记：2026-11-08 19:54（北京时间）。科学材料观察截至2026-11-08 19:49:30（北京时间；科研档案快照，实验结果已于19:44检查）；不是11月8日全天预填。
- 性质：已执行实验及机制分析的回溯核对；周志[EXP-2026W45-019](../../LOGS/2026-W45.md#exp-2026w45-019)。本次整理没有重新执行。

## 目的与假设

核查后续approach是否错误地把实际夹爪开度当成目标命令。 保持最近闭爪目标后，命令偏差及整任务结果是否改善。

## 实际工作

固定其他条件，对照实际开度与最近命令保持，各五布局。

## 指标与结论

10新回合；152个手臂—动作检查项中的命令偏差72→0。两组分数均[0,0,0,0,15]，成功0/5，无配对分数增加。

命令语义得到修正，但本批未证明任务得分或稳定抓持提高。

## 解释与限制

152是动作检查项，不是机器人回合；闭爪命令正确不自动证明物体附着。

不同任务、执行条件、重复布局、复用对照与生成样本分别计数。原报告是当时快照，若与后续契约更正冲突，以标有来源的更正解释为准，不改原分数。

## 复核与下一步

检查候选覆盖能力、运输目标和发布参照的能力差异。 原始脚本与协议是复现依据，不能原地重跑覆盖结果。本批加入[整周执行账本](../../evidence/period_20261105_20261108/tables/native_episodes_all.json)，没有把旧回合重复计为新执行。

## 原件与来源

- [20261107_v1/protocol.json](../../evidence/period_20261105_20261108/stages/36/20261107_v1/protocol.json) — SHA256 `5454b05c4e437949a3754ecafa9e35be2735e2a359964b4bea8f8bcb284e1e52`；实验室原件 `/mnt/data/joey_tr/physical-RSI/result/36_system2_gripper_command_contract/20261107_v1/protocol.json`。
- [20261107_v1/FINAL_SUMMARY.json](../../evidence/period_20261105_20261108/stages/36/20261107_v1/FINAL_SUMMARY.json) — SHA256 `c388aa94430cacaa8badb97fd6218e0f2af1745f865517627e8eceefc35fac22`；实验室原件 `/mnt/data/joey_tr/physical-RSI/result/36_system2_gripper_command_contract/20261107_v1/FINAL_SUMMARY.json`。
- [20261107_v1/REPORT.txt](../../evidence/period_20261105_20261108/stages/36/20261107_v1/REPORT.txt) — SHA256 `6db6ecfde8752888418a1fb8ad8589713ca04f40fc17b6daa8c2cd565d1c8d43`；实验室原件 `/mnt/data/joey_tr/physical-RSI/result/36_system2_gripper_command_contract/20261107_v1/REPORT.txt`。

另见[独立原始回执与usage复算](../../evidence/period_20261105_20261108/audit/independent-recomputation.json)、[专项解释复核](../../evidence/period_20261105_20261108/audit/SCIENCE_REVIEW_ZH.md)。

## 具体复现入口补充

精确入口 `run_native.py`，SHA256 `9d5a40131b8f7df8d57fff37410c8aa966464ab84fb25cc169eb342749838e81`。development:运行ID[0,1,2,3,4]/源ID[0,1,2,3,4]；classify_objects原生1100步。

已读取2份本批native/request.json，记录原生执行seed=[0]；逐件路径/SHA见复现索引。这不是布局生成seed；场景以各阶段layout ID与SHA256绑定，不把求解器seed或重复布局当成独立场景。

原始源文件、原生子进程argv（若保存）、分开的软件版本及硬件事实见[批次36复现索引](../../evidence/period_20261105_20261108/reproduction/README.md#batch-36)。该索引区分已保存命令与无法确认项，本次不运行历史程序。
