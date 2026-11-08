# HIST-084 · 固定六次观察循环与终止机制核对

- 原始事件：本批最终状态生成于2026-11-07 14:51:03（北京时间）；事件范围依原协议和逐回合回执，未用文件mtime代替发生时间。
- 回溯登记：2026-11-08 19:54（北京时间）。科学材料观察截至2026-11-08 19:49:30（北京时间；科研档案快照，实验结果已于19:44检查）；不是11月8日全天预填。
- 性质：已执行实验及机制分析的回溯核对；周志[EXP-2026W45-022](../../LOGS/2026-W45.md#exp-2026w45-022)。本次整理没有重新执行。

## 目的与假设

区分初始观测物体数带来的循环截断和其他停止条件。 将min(6,len(items))改为固定六次，是否提高任务覆盖和分数。

## 实际工作

只新增固定六次组五回合，复用批次38偏移组对照；保存最初重放和后来的真实包装层重放。

## 指标与结论

5新回合，分数[0,0,0,0,15]；多完成2次运输，完整成功仍0/5。

增加循环次数推进部分运输，但未改变整任务分数；停止解释须依据真实包装层更正版本。

## 解释与限制

旧重放遗漏包装层，使用可被候选捕获的AssertionError标注缺失后续；不能继续称作精确执行重放。原分数不改。

不同任务、执行条件、重复布局、复用对照与生成样本分别计数。原报告是当时快照，若与后续契约更正冲突，以标有来源的更正解释为准，不改原分数。

## 复核与下一步

在候选不变的条件下修正零动作规划拒绝返回契约。 原始脚本与协议是复现依据，不能原地重跑覆盖结果。本批加入[整周执行账本](../../evidence/period_20261105_20261108/tables/native_episodes_all.json)，没有把旧回合重复计为新执行。

## 原件与来源

- [20261107_v1/protocol.json](../../evidence/period_20261105_20261108/stages/39/20261107_v1/protocol.json) — SHA256 `180cf1e785aad457507bc0b9447755bc68f19f9918a2f0bc04c74224aa5d411e`；实验室原件 `/mnt/data/joey_tr/physical-RSI/result/39_system2_observation_loop/20261107_v1/protocol.json`。
- [20261107_v1/FINAL_SUMMARY.json](../../evidence/period_20261105_20261108/stages/39/20261107_v1/FINAL_SUMMARY.json) — SHA256 `515614e75fe8b1988a578b783f1cfb654174e2724a2f7a4800bc575e00ee0867`；实验室原件 `/mnt/data/joey_tr/physical-RSI/result/39_system2_observation_loop/20261107_v1/FINAL_SUMMARY.json`。
- [20261107_v1/REPORT.txt](../../evidence/period_20261105_20261108/stages/39/20261107_v1/REPORT.txt) — SHA256 `17b5afb43b67e471b080e9b75836448ca050ff4ef35239a22164c4e7afe1870a`；实验室原件 `/mnt/data/joey_tr/physical-RSI/result/39_system2_observation_loop/20261107_v1/REPORT.txt`。
- [20261107_v1/driver-contract-replay-v2.json](../../evidence/period_20261105_20261108/stages/39/20261107_v1/driver-contract-replay-v2.json) — SHA256 `e4d36f04c9f3547b0d0ce0ada54ac11ece7344b93af9b7e84429cb9f0cf0744a`；实验室原件 `/mnt/data/joey_tr/physical-RSI/result/39_system2_observation_loop/20261107_v1/driver-contract-replay-v2.json`。

另见[独立原始回执与usage复算](../../evidence/period_20261105_20261108/audit/independent-recomputation.json)、[专项解释复核](../../evidence/period_20261105_20261108/audit/SCIENCE_REVIEW_ZH.md)。

## 具体复现入口补充

精确入口 `run_native.py`，SHA256 `5edaf5677ccc67b504c8fc231ec04e3778d4e9a226f4d669063ca83daf20e5c5`。development:运行ID[0,1,2,3,4]/源ID[0,1,2,3,4]；classify_objects原生1100步。

已读取1份本批native/request.json，记录原生执行seed=[0]；逐件路径/SHA见复现索引。这不是布局生成seed；场景以各阶段layout ID与SHA256绑定，不把求解器seed或重复布局当成独立场景。

原始源文件、原生子进程argv（若保存）、分开的软件版本及硬件事实见[批次39复现索引](../../evidence/period_20261105_20261108/reproduction/README.md#batch-39)。该索引区分已保存命令与无法确认项，本次不运行历史程序。
