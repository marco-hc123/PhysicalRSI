# HIST-082 · 候选任务覆盖与完整发布技能参照

- 原始事件：本批最终状态生成于2026-11-07 13:49:05（北京时间）；事件范围依原协议和逐回合回执，未用文件mtime代替发生时间。
- 回溯登记：2026-11-08 19:54（北京时间）。科学材料观察截至2026-11-08 19:49:30（北京时间；科研档案快照，实验结果已于19:44检查）；不是11月8日全天预填。
- 性质：已执行实验及机制分析的回溯核对；周志[EXP-2026W45-020](../../LOGS/2026-W45.md#exp-2026w45-020)。本次整理没有重新执行。

## 目的与假设

核查六次循环是否覆盖全部物体，并了解发布完整技能在同布局的能力。 理想抽象接口下候选是否覆盖任务；完整发布技能是否达到全成功。

## 实际工作

构造CPU理想感知/抓放检查；完整发布分类技能在五布局单列能力参照。

## 指标与结论

5新原生参照回合：[0,15,15,15,40]，均分17，完整成功0/5。六循环候选在8/7物体布局遗留2/1物体，缺少显式final_home。

候选有覆盖限制；完整发布参照也未全成功。complete_hold不等于原生success。

## 解释与限制

参照使用更丰富的感知、恢复和动作能力，17−3不是单因素修正收益，也不能作为公平模型比较。

不同任务、执行条件、重复布局、复用对照与生成样本分别计数。原报告是当时快照，若与后续契约更正冲突，以标有来源的更正解释为准，不改原分数。

## 复核与下一步

以匹配候选和冻结接口分别验证运输目标与循环规则。 原始脚本与协议是复现依据，不能原地重跑覆盖结果。本批加入[整周执行账本](../../evidence/period_20261105_20261108/tables/native_episodes_all.json)，没有把旧回合重复计为新执行。

## 原件与来源

- [20261107_v1/protocol.json](../../evidence/period_20261105_20261108/stages/37/20261107_v1/protocol.json) — SHA256 `2a6ac7a23af45dfe2db53b8b0371d3fe863af5f3549eb6e2891367d8ccf918f1`；实验室原件 `/mnt/data/joey_tr/physical-RSI/result/37_system2_candidate_capacity/20261107_v1/protocol.json`。
- [20261107_v1/FINAL_SUMMARY.json](../../evidence/period_20261105_20261108/stages/37/20261107_v1/FINAL_SUMMARY.json) — SHA256 `dd4ec941fecf9ddb23a9819ef2d5c7b0cb8328ebe483b318f5fe0f17b9ce37c5`；实验室原件 `/mnt/data/joey_tr/physical-RSI/result/37_system2_candidate_capacity/20261107_v1/FINAL_SUMMARY.json`。
- [20261107_v1/REPORT.txt](../../evidence/period_20261105_20261108/stages/37/20261107_v1/REPORT.txt) — SHA256 `ad3ac382760091dd6c1fc9e3384bd10c87d5d62242d1399a1b20c8ba1680e043`；实验室原件 `/mnt/data/joey_tr/physical-RSI/result/37_system2_candidate_capacity/20261107_v1/REPORT.txt`。

另见[独立原始回执与usage复算](../../evidence/period_20261105_20261108/audit/independent-recomputation.json)、[专项解释复核](../../evidence/period_20261105_20261108/audit/SCIENCE_REVIEW_ZH.md)。

## 具体复现入口补充

精确入口 `native-validation/run_reference_v2.py`，SHA256 `146748b7f465b681ec587d9432570db471a12db7ef43ef8ced94057d85a40eab`。development:运行ID[0,1,2,3,4]/源ID[0,1,2,3,4]；classify_objects原生1100步。

已读取1份本批native/request.json，记录原生执行seed=[0]；逐件路径/SHA见复现索引。这不是布局生成seed；场景以各阶段layout ID与SHA256绑定，不把求解器seed或重复布局当成独立场景。

原始源文件、原生子进程argv（若保存）、分开的软件版本及硬件事实见[批次37复现索引](../../evidence/period_20261105_20261108/reproduction/README.md#batch-37)。该索引区分已保存命令与无法确认项，本次不运行历史程序。
