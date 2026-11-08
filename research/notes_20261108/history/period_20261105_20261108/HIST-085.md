# HIST-085 · 零动作规划拒绝返回契约修正

- 原始事件：本批最终状态生成于2026-11-07 15:24:15（北京时间）；事件范围依原协议和逐回合回执，未用文件mtime代替发生时间。
- 回溯登记：2026-11-08 19:54（北京时间）。科学材料观察截至2026-11-08 19:49:30（北京时间；科研档案快照，实验结果已于19:44检查）；不是11月8日全天预填。
- 性质：已执行实验及机制分析的回溯核对；周志[EXP-2026W45-023](../../LOGS/2026-W45.md#exp-2026w45-023)。本次整理没有重新执行。

## 目的与假设

核查候选的换臂恢复分支是否被研究适配层错误返回阻止。 将零动作拒绝按原字典返回后，候选能否执行已有恢复分支，并提高整任务分数。

## 实际工作

只改变适配包装的拒绝返回；候选、动作参数、评分和预算不变。新增五回合，复用批次39对照。

## 指标与结论

5新回合，[0,0,0,0,15]；3次换臂approach真实完成，完成approach72→93、运输18→21，完整成功0/5。

契约不一致确实阻止了一部分恢复；修好后仍没有整任务分数提升。缺陷属于本研究适配层，不能归给冻结官方源码。

## 解释与限制

后台已有no_path与候选收到该信息是两个层次；历史批次33的解释需收窄，不能把所有低分归给这一项。

不同任务、执行条件、重复布局、复用对照与生成样本分别计数。原报告是当时快照，若与后续契约更正冲突，以标有来源的更正解释为准，不改原分数。

## 复核与下一步

区分最小技能链能力与生成候选的独立增益，保留历史更正原件。 原始脚本与协议是复现依据，不能原地重跑覆盖结果。本批加入[整周执行账本](../../evidence/period_20261105_20261108/tables/native_episodes_all.json)，没有把旧回合重复计为新执行。

## 原件与来源

- [20261107_v1/protocol.json](../../evidence/period_20261105_20261108/stages/40/20261107_v1/protocol.json) — SHA256 `5c674832fe746802b3c517abd9a4a61256d163070116482d8d555f9ae9a2c5de`；实验室原件 `/mnt/data/joey_tr/physical-RSI/result/40_system2_rejection_contract/20261107_v1/protocol.json`。
- [20261107_v1/FINAL_SUMMARY.json](../../evidence/period_20261105_20261108/stages/40/20261107_v1/FINAL_SUMMARY.json) — SHA256 `177f1072fe5aa918d891da70ba2db6ec2b4a0d9e63ca206decf9540f25be1e48`；实验室原件 `/mnt/data/joey_tr/physical-RSI/result/40_system2_rejection_contract/20261107_v1/FINAL_SUMMARY.json`。
- [20261107_v1/REPORT.txt](../../evidence/period_20261105_20261108/stages/40/20261107_v1/REPORT.txt) — SHA256 `580905d7a4a7cae533a7dc0a4e1a0ad7b8268d79f733decbbeb44f943e01a01d`；实验室原件 `/mnt/data/joey_tr/physical-RSI/result/40_system2_rejection_contract/20261107_v1/REPORT.txt`。
- [20261107_v1/HISTORICAL_CONTRACT_CORRECTION.txt](../../evidence/period_20261105_20261108/stages/40/20261107_v1/HISTORICAL_CONTRACT_CORRECTION.txt) — SHA256 `d9c88c6e53fdc31c3033ced86f82ccb404b5a7e2bba5ce15543c22268d61ae83`；实验室原件 `/mnt/data/joey_tr/physical-RSI/result/40_system2_rejection_contract/20261107_v1/HISTORICAL_CONTRACT_CORRECTION.txt`。

另见[独立原始回执与usage复算](../../evidence/period_20261105_20261108/audit/independent-recomputation.json)、[专项解释复核](../../evidence/period_20261105_20261108/audit/SCIENCE_REVIEW_ZH.md)。

## 具体复现入口补充

精确入口 `run_native.py`，SHA256 `6b6be5bc3811f61823412a10d026385df4d2a1ad0bb2fb1468d672f9328c692a`。development:运行ID[0,1,2,3,4]/源ID[0,1,2,3,4]；classify_objects原生1100步。

已读取2份本批native/request.json，记录原生执行seed=[0]；逐件路径/SHA见复现索引。这不是布局生成seed；场景以各阶段layout ID与SHA256绑定，不把求解器seed或重复布局当成独立场景。

原始源文件、原生子进程argv（若保存）、分开的软件版本及硬件事实见[批次40复现索引](../../evidence/period_20261105_20261108/reproduction/README.md#batch-40)。该索引区分已保存命令与无法确认项，本次不运行历史程序。
