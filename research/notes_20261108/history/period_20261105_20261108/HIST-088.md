# HIST-088 · 分类与抓取的双任务反馈、选择与独立验收

- 原始事件：本批最终状态生成于2026-11-08 18:08:40（北京时间）；事件范围依原协议和逐回合回执，未用文件mtime代替发生时间。
- 回溯登记：2026-11-08 19:54（北京时间）。科学材料观察截至2026-11-08 19:49:30（北京时间；科研档案快照，实验结果已于19:44检查）；不是11月8日全天预填。
- 性质：已执行实验及机制分析的回溯核对；周志[EXP-2026W45-026](../../LOGS/2026-W45.md#exp-2026w45-026)。本次整理没有重新执行。

## 目的与假设

在已修正接口和较完整说明下，核查basic与execution_feedback在两个任务中的候选效果。 每任务每反馈条件三候选中，是否出现严格提高开发均分且不降低完整成功数的候选，并在独立布局验证。

## 实际工作

gpt-6.1-sol/high共生成12候选，全部准入；两任务各五个新开发布局，选择冻结后各五个新布局；按唯一策略去重执行，pi05单列参照。

## 指标与结论

89个终态评分=88正式+1准备smoke；另2中断无终态分数，总尝试91。12API/121745Token，估算$0.4614434。分类开发父/六候选全0，独立父[15,null,15,0,0]、0/4、均分7.5。抓取开发父3/5均60；basic候选均分[60,60,40]、增强[40,60,60]，各组8/15成功；独立父[0,null,100,0,0]、1/4、均25。两任务两条件均retain_parent。

本轮未产生被选择的新技能。抓取有原生成功，分类仍无完整成功；不能把两种任务混为总体成功率。两个反馈视图共享相同父策略的验收证据。

## 解释与限制

分类layout1第214步、抓取layout1第31步因轨迹跟踪偏离中断，score/success必须null，不能填0或宣称5/5验收。抓取成功指指定物体抬升达到阈值，不等于稳定运输。15次分类增强回合在第四次运输请求拒绝后正常返回；16次抓取候选Actor关闭由原生success终止引起，不应当成失败。

不同任务、执行条件、重复布局、复用对照与生成样本分别计数。原报告是当时快照，若与后续契约更正冲突，以标有来源的更正解释为准，不改原分数。

## 复核与下一步

保留中断和准入原件，不自动重试；后续研究需单独决定干预、匹配对照、独立布局和停止条件。 原始脚本与协议是复现依据，不能原地重跑覆盖结果。本批加入[整周执行账本](../../evidence/period_20261105_20261108/tables/native_episodes_all.json)，没有把旧回合重复计为新执行。

## 原件与来源

- [20261108_v1/native-validation/protocol.json](../../evidence/period_20261105_20261108/stages/43/20261108_v1/native-validation/protocol.json) — SHA256 `55c2ea848f3031b4b773c1a65eda99de7f8ec98a42a118651acb44f6470d033d`；实验室原件 `/mnt/data/joey_tr/physical-RSI/result/43_system2_multitask/20261108_v1/native-validation/protocol.json`。
- [20261108_v1/native-validation/FINAL_SUMMARY.json](../../evidence/period_20261105_20261108/stages/43/20261108_v1/native-validation/FINAL_SUMMARY.json) — SHA256 `7d74bae0ca3bd6e9ab5511d8d2b8dfa7c59a66a665213901e56b65dc162731ea`；实验室原件 `/mnt/data/joey_tr/physical-RSI/result/43_system2_multitask/20261108_v1/native-validation/FINAL_SUMMARY.json`。
- [20261108_v1/native-validation/REPORT.txt](../../evidence/period_20261105_20261108/stages/43/20261108_v1/native-validation/REPORT.txt) — SHA256 `aca64a6bbfbdc6df9d3f4a35dc69fc6992eb5f9d68c2ee1bfe661c84b31486be`；实验室原件 `/mnt/data/joey_tr/physical-RSI/result/43_system2_multitask/20261108_v1/native-validation/REPORT.txt`。

另见[独立原始回执与usage复算](../../evidence/period_20261105_20261108/audit/independent-recomputation.json)、[专项解释复核](../../evidence/period_20261105_20261108/audit/SCIENCE_REVIEW_ZH.md)。

## 具体复现入口补充

精确入口 `native-validation/run_phase.py`，SHA256 `eccdd79636e8c3b5435ab82218b0bdb717b4deb5b3177c3f73c3cf3080ca73c8`。classify_objects-candidates:运行ID[0,1,2,3,4]/源ID[0,1,2,3,4]；classify_objects-heldout:运行ID[0,1,2,3,4]/源ID[0,1,2,3,4]；classify_objects-parent:运行ID[0,1,2,3,4]/源ID[0,1,2,3,4]；general_pickup-candidates:运行ID[0,1,2,3,4]/源ID[0,1,2,3,4]；general_pickup-heldout:运行ID[0,1,2,3,4]/源ID[0,1,2,3,4]；general_pickup-parent:运行ID[0,1,2,3,4]/源ID[0,1,2,3,4]；general_pickup-smoke:运行ID[0]/源ID[0]；分类1100步/抓取200步，heldout中断布局保留null。

已读取7份本批native/request.json，记录原生执行seed=[0]；逐件路径/SHA见复现索引。这不是布局生成seed；场景以各阶段layout ID与SHA256绑定，不把求解器seed或重复布局当成独立场景。

原始源文件、原生子进程argv（若保存）、分开的软件版本及硬件事实见[批次43复现索引](../../evidence/period_20261105_20261108/reproduction/README.md#batch-43)。该索引区分已保存命令与无法确认项，本次不运行历史程序。
