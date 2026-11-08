# HIST-087 · 候选池、人工目标对照、第二轮生成与独立布局

- 原始事件：本批最终状态生成于2026-11-07 21:47:16（北京时间）；事件范围依原协议和逐回合回执，未用文件mtime代替发生时间。
- 回溯登记：2026-11-08 19:54（北京时间）。科学材料观察截至2026-11-08 19:49:30（北京时间；科研档案快照，实验结果已于19:44检查）；不是11月8日全天预填。
- 性质：已执行实验及机制分析的回溯核对；周志[EXP-2026W45-025](../../LOGS/2026-W45.md#exp-2026w45-025)。本次整理没有重新执行。

## 目的与假设

区分候选数量、执行目标和补充反馈对当前固定代码父策略的影响。 在本次固定条件及有限候选池中，生成候选能否超过父策略并在独立布局保留收益。

## 实际工作

首轮生成5候选、单因素目标对照、第二轮生成3候选，再冻结选择并对唯一策略去重执行五个新布局。

## 指标与结论

60新有评分回合、180视频；5次无策略动作布局资格检查另计。8API/146516Token，估算$0.8154218。首轮五候选五布局全0；第二轮2份nonlocal拒绝无评分，唯一准入者[0,0,0,0,15]。选择均保留fixed_parent。独立父[0,15,0,15,0]均分6、control全0、offset[0,15,0,0,0]均分3，完整成功均0。

本候选池没有超过代码父策略；人工XY修正有有限局部改善但不构成自主改进。后续已实际执行独立布局验收，不能再概括整个项目从未重评选择器。

## 解释与限制

两份拒绝候选没有0/5分数；原提示未告知nonlocal禁令。首轮未告知100RPC限制但当次未触发；第二轮同时增加反馈和搜索机会，不能隔离二者作用。多个保留父策略的视图共享一次验收。

不同任务、执行条件、重复布局、复用对照与生成样本分别计数。原报告是当时快照，若与后续契约更正冲突，以标有来源的更正解释为准，不改原分数。

## 复核与下一步

按任务、生成条件、准入和实际执行分别报告，并核对跨任务的新布局与中断边界。 原始脚本与协议是复现依据，不能原地重跑覆盖结果。本批加入[整周执行账本](../../evidence/period_20261105_20261108/tables/native_episodes_all.json)，没有把旧回合重复计为新执行。

## 原件与来源

- [20261107_v1/protocol.json](../../evidence/period_20261105_20261108/stages/42/20261107_v1/protocol.json) — SHA256 `9aa00cde30fcc9ca4a3d020d334b07c0569bf3c58829937c02d582ed6a3838bf`；实验室原件 `/mnt/data/joey_tr/physical-RSI/result/42_system2_search_execution_controls/20261107_v1/protocol.json`。
- [20261107_v1/FINAL_SUMMARY.json](../../evidence/period_20261105_20261108/stages/42/20261107_v1/FINAL_SUMMARY.json) — SHA256 `8c245cd521155f8cca4a61d8f8c49284c638f4ef55ff4a3acb13ad2135c1cf4c`；实验室原件 `/mnt/data/joey_tr/physical-RSI/result/42_system2_search_execution_controls/20261107_v1/FINAL_SUMMARY.json`。
- [20261107_v1/REPORT.txt](../../evidence/period_20261105_20261108/stages/42/20261107_v1/REPORT.txt) — SHA256 `07154f76c653f8a7159cdffb0e552379e8bc5b4889516c4dbb58fbe76ba33caa`；实验室原件 `/mnt/data/joey_tr/physical-RSI/result/42_system2_search_execution_controls/20261107_v1/REPORT.txt`。

另见[独立原始回执与usage复算](../../evidence/period_20261105_20261108/audit/independent-recomputation.json)、[专项解释复核](../../evidence/period_20261105_20261108/audit/SCIENCE_REVIEW_ZH.md)。

## 具体复现入口补充

精确入口 `native-validation/run_phase.py`，SHA256 `ff458b38da207e38963223849a1f9e274e17ac0ff4dc520bd531e18688b69aa5`。heldout:运行ID[0,1,2,3,4]/源ID[0,1,2,3,4]；parent:运行ID[0,1,2,3,4]/源ID[0,1,2,3,4]；repair:运行ID[0,1,2,3,4]/源ID[0,1,2,3,4]；round2:运行ID[0,1,2,3,4]/源ID[0,1,2,3,4]；sampling:运行ID[0,1,2,3,4]/源ID[0,1,2,3,4]；classify_objects原生1100步。

已读取3份本批native/request.json，记录原生执行seed=[0]；逐件路径/SHA见复现索引。这不是布局生成seed；场景以各阶段layout ID与SHA256绑定，不把求解器seed或重复布局当成独立场景。

原始源文件、原生子进程argv（若保存）、分开的软件版本及硬件事实见[批次42复现索引](../../evidence/period_20261105_20261108/reproduction/README.md#batch-42)。该索引区分已保存命令与无法确认项，本次不运行历史程序。
