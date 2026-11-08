# HIST-083 · 运输目标XY偏移的匹配原生对照

- 原始事件：本批最终状态生成于2026-11-07 14:27:49（北京时间）；事件范围依原协议和逐回合回执，未用文件mtime代替发生时间。
- 回溯登记：2026-11-08 19:54（北京时间）。科学材料观察截至2026-11-08 19:49:30（北京时间；科研档案快照，实验结果已于19:44检查）；不是11月8日全天预填。
- 性质：已执行实验及机制分析的回溯核对；周志[EXP-2026W45-021](../../LOGS/2026-W45.md#exp-2026w45-021)。本次整理没有重新执行。

## 目的与假设

检查失败运输目标是否可由发布目标偏移规则改善。 仅修订运输XY目标后，可行轨迹、动作推进与原生得分是否共同增加。

## 实际工作

18次离线原/偏移目标检查后，在固定候选下新增原目标/偏移目标各五回合。

## 指标与结论

10新回合；离线原目标0/9、偏移9/9返回轨迹。原生规划拒绝5→0，完成approach35→64，运输完成5/10→16/16；两组分数仍[0,0,0,0,15]。

目标偏移改善规划和运输推进，未提高整任务分数。

## 解释与限制

运输分母不同且是调用计数，不是独立场景成功率；初始漏检、循环上限、物体未稳定入筐仍可能影响任务。

不同任务、执行条件、重复布局、复用对照与生成样本分别计数。原报告是当时快照，若与后续契约更正冲突，以标有来源的更正解释为准，不改原分数。

## 复核与下一步

仅改变观察循环次数，复用本批偏移组作明确对照。 原始脚本与协议是复现依据，不能原地重跑覆盖结果。本批加入[整周执行账本](../../evidence/period_20261105_20261108/tables/native_episodes_all.json)，没有把旧回合重复计为新执行。

## 原件与来源

- [20261107_v1/protocol.json](../../evidence/period_20261105_20261108/stages/38/20261107_v1/protocol.json) — SHA256 `a18a49f0197b75740613631f9ee221c05b0bbd1d3ad4d8c424597af4559437bc`；实验室原件 `/mnt/data/joey_tr/physical-RSI/result/38_system2_transport_destination/20261107_v1/protocol.json`。
- [20261107_v1/FINAL_SUMMARY.json](../../evidence/period_20261105_20261108/stages/38/20261107_v1/FINAL_SUMMARY.json) — SHA256 `e84d7ab4291391c565b7c9847687a186196be8061b3f29f76a9688c51ca2a677`；实验室原件 `/mnt/data/joey_tr/physical-RSI/result/38_system2_transport_destination/20261107_v1/FINAL_SUMMARY.json`。
- [20261107_v1/REPORT.txt](../../evidence/period_20261105_20261108/stages/38/20261107_v1/REPORT.txt) — SHA256 `97405fd39d8f2113175fb21dbd034c2d23163d05eefaca0a6a35104ac3269d25`；实验室原件 `/mnt/data/joey_tr/physical-RSI/result/38_system2_transport_destination/20261107_v1/REPORT.txt`。

另见[独立原始回执与usage复算](../../evidence/period_20261105_20261108/audit/independent-recomputation.json)、[专项解释复核](../../evidence/period_20261105_20261108/audit/SCIENCE_REVIEW_ZH.md)。

## 具体复现入口补充

精确入口 `run_native.py`，SHA256 `b05b2cff73d702d25c9950371c2fbd81ab3b6cbb5e2d7a9376130259f50fdf32`。development:运行ID[0,1,2,3,4]/源ID[0,1,2,3,4]；classify_objects原生1100步。

已读取2份本批native/request.json，记录原生执行seed=[0]；逐件路径/SHA见复现索引。这不是布局生成seed；场景以各阶段layout ID与SHA256绑定，不把求解器seed或重复布局当成独立场景。

原始源文件、原生子进程argv（若保存）、分开的软件版本及硬件事实见[批次38复现索引](../../evidence/period_20261105_20261108/reproduction/README.md#batch-38)。该索引区分已保存命令与无法确认项，本次不运行历史程序。
