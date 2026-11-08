# HIST-086 · 单周期搬运链能力下限与发布参照

- 原始事件：本批最终状态生成于2026-11-07 17:42:08（北京时间）；事件范围依原协议和逐回合回执，未用文件mtime代替发生时间。
- 回溯登记：2026-11-08 19:54（北京时间）。科学材料观察截至2026-11-08 19:49:30（北京时间；科研档案快照，实验结果已于19:44检查）；不是11月8日全天预填。
- 性质：已执行实验及机制分析的回溯核对；周志[EXP-2026W45-024](../../LOGS/2026-W45.md#exp-2026w45-024)。本次整理没有重新执行。

## 目的与假设

判断候选是否具备把一个选定物体稳定送入目标篮筐的局部能力。 单周期候选是否可靠完成搬运，其代理指标是否等同整任务评分。

## 实际工作

单周期候选与发布技能首篮筐周期各五布局；旁路诊断只作分析，不进入候选输入。

## 指标与结论

10新回合。稳定送达代理候选2/5、发布参照5/5；后者2次在到位异常后清理张爪中送达。原生分数候选[0,0,0,0,15]、参照[0,15,15,15,15]，完整成功均0。

存在局部操作能力，但动作调用返回、单物体送达和整任务成功不同。

## 解释与限制

选物及接口能力不一致，不能据2/5对5/5直接排名。发布参照的清理动作不能误写为正常返回成功。

不同任务、执行条件、重复布局、复用对照与生成样本分别计数。原报告是当时快照，若与后续契约更正冲突，以标有来源的更正解释为准，不改原分数。

## 复核与下一步

冻结执行条件与代码父策略，再比较候选池、人工目标对照与后续生成。 原始脚本与协议是复现依据，不能原地重跑覆盖结果。本批加入[整周执行账本](../../evidence/period_20261105_20261108/tables/native_episodes_all.json)，没有把旧回合重复计为新执行。

## 原件与来源

- [20261107_v1/protocol.json](../../evidence/period_20261105_20261108/stages/41/20261107_v1/protocol.json) — SHA256 `b78df85684a6450ceb80eee14a1cbd51206275e4b3faf0af8ca6a3d5ecf754a2`；实验室原件 `/mnt/data/joey_tr/physical-RSI/result/41_system2_skill_chain_floor/20261107_v1/protocol.json`。
- [20261107_v1/FINAL_SUMMARY.json](../../evidence/period_20261105_20261108/stages/41/20261107_v1/FINAL_SUMMARY.json) — SHA256 `258d8132c8eb28ad1e85e36c06862672079513e006cdaa24aef9d517d8ced5ef`；实验室原件 `/mnt/data/joey_tr/physical-RSI/result/41_system2_skill_chain_floor/20261107_v1/FINAL_SUMMARY.json`。
- [20261107_v1/REPORT.txt](../../evidence/period_20261105_20261108/stages/41/20261107_v1/REPORT.txt) — SHA256 `f1d0e1c0be08de3c6b8ca53c7511e95cb370aa3a1165292b3a742029d0239fba`；实验室原件 `/mnt/data/joey_tr/physical-RSI/result/41_system2_skill_chain_floor/20261107_v1/REPORT.txt`。

另见[独立原始回执与usage复算](../../evidence/period_20261105_20261108/audit/independent-recomputation.json)、[专项解释复核](../../evidence/period_20261105_20261108/audit/SCIENCE_REVIEW_ZH.md)。

## 具体复现入口补充

精确入口 `native-validation/run_native.py`，SHA256 `7ef7975229bf6c15add45c70f404d53f9808d0893ae5147d4674f74b87d13ca7`。development:运行ID[0,1,2,3,4]/源ID[0,1,2,3,4]；classify_objects原生1100步。

已读取2份本批native/request.json，记录原生执行seed=[0]；逐件路径/SHA见复现索引。这不是布局生成seed；场景以各阶段layout ID与SHA256绑定，不把求解器seed或重复布局当成独立场景。

原始源文件、原生子进程argv（若保存）、分开的软件版本及硬件事实见[批次41复现索引](../../evidence/period_20261105_20261108/reproduction/README.md#batch-41)。该索引区分已保存命令与无法确认项，本次不运行历史程序。
