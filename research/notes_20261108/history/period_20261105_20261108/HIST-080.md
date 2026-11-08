# HIST-080 · 抓后位姿旁路与求解目标诊断

- 原始事件：本批最终状态生成于2026-11-07 12:52:46（北京时间）；事件范围依原协议和逐回合回执，未用文件mtime代替发生时间。
- 回溯登记：2026-11-08 19:54（北京时间）。科学材料观察截至2026-11-08 19:49:30（北京时间；科研档案快照，实验结果已于19:44检查）；不是11月8日全天预填。
- 性质：已执行实验及机制分析的回溯核对；周志[EXP-2026W45-018](../../LOGS/2026-W45.md#exp-2026w45-018)。本次整理没有重新执行。

## 目的与假设

把末端动作完成、物体抬升、稳定抓持和目标可达性分开。 完成lift调用后是否已可靠抓住物体，以及后续无轨迹是否由单一目标设置解释。

## 实际工作

固定候选，在原布局0、1、4新增只读旁路位姿日志，不将真值交给候选；另做高度/yaw/seed探针。

## 指标与结论

3新原生回合，分数[0,0,15]；81离线求解探针。原目标9/9无轨迹，有限布局0变体中12次可行。

末端到达lift不等同稳定抓持；观测到短暂抬起、移向篮筐等不同过程。

## 解释与限制

三个最后失败调用尚未形成可执行轨迹，不应说执行到一半失败；无轨迹不证明绝对不可达或一定碰撞。

不同任务、执行条件、重复布局、复用对照与生成样本分别计数。原报告是当时快照，若与后续契约更正冲突，以标有来源的更正解释为准，不改原分数。

## 复核与下一步

用匹配对照检验夹爪命令保持，并保留物体旁路证据。 原始脚本与协议是复现依据，不能原地重跑覆盖结果。本批加入[整周执行账本](../../evidence/period_20261105_20261108/tables/native_episodes_all.json)，没有把旧回合重复计为新执行。

## 原件与来源

- [20261107_v1/protocol.json](../../evidence/period_20261105_20261108/stages/35/20261107_v1/protocol.json) — SHA256 `8503189c0f5d731718f6c16140a9c35fd9fc55aa2dc18642bd95e5ca45e4a56d`；实验室原件 `/mnt/data/joey_tr/physical-RSI/result/35_system2_postgrasp_diagnosis/20261107_v1/protocol.json`。
- [20261107_v1/FINAL_SUMMARY.json](../../evidence/period_20261105_20261108/stages/35/20261107_v1/FINAL_SUMMARY.json) — SHA256 `fc0bcafbcaf8ad1c8c8cd918ef8dccb4708c819d7a03ec3315b9ac65bf3aa5ae`；实验室原件 `/mnt/data/joey_tr/physical-RSI/result/35_system2_postgrasp_diagnosis/20261107_v1/FINAL_SUMMARY.json`。
- [20261107_v1/REPORT.txt](../../evidence/period_20261105_20261108/stages/35/20261107_v1/REPORT.txt) — SHA256 `86a213efdbd886c8252697c0a91828126d211cc88ba4f0c488a803d5ec4b948e`；实验室原件 `/mnt/data/joey_tr/physical-RSI/result/35_system2_postgrasp_diagnosis/20261107_v1/REPORT.txt`。

另见[独立原始回执与usage复算](../../evidence/period_20261105_20261108/audit/independent-recomputation.json)、[专项解释复核](../../evidence/period_20261105_20261108/audit/SCIENCE_REVIEW_ZH.md)。

## 具体复现入口补充

精确入口 `native-validation/run_native.py`，SHA256 `c69d1a1fe3cca048a96d0af266f4c834bed6ce591493c930e921858dc58e7e2d`。development:运行ID[0,1,2]/源ID[0,1,4]；classify_objects原生1100步。

已读取2份本批native/request.json，记录原生执行seed=[0]；逐件路径/SHA见复现索引。这不是布局生成seed；场景以各阶段layout ID与SHA256绑定，不把求解器seed或重复布局当成独立场景。

原始源文件、原生子进程argv（若保存）、分开的软件版本及硬件事实见[批次35复现索引](../../evidence/period_20261105_20261108/reproduction/README.md#batch-35)。该索引区分已保存命令与无法确认项，本次不运行历史程序。
