# HIST-078 · 能力说明反馈的六候选生成与原生验证

- 原始事件：本批最终状态生成于2026-11-06 14:35:07（北京时间）；事件范围依原协议和逐回合回执，未用文件mtime代替发生时间。
- 回溯登记：2026-11-08 19:54（北京时间）。科学材料观察截至2026-11-08 19:49:30（北京时间；科研档案快照，实验结果已于19:44检查）；不是11月8日全天预填。
- 性质：已执行实验及机制分析的回溯核对；周志[EXP-2026W45-016](../../LOGS/2026-W45.md#exp-2026w45-016)。本次整理没有重新执行。

## 目的与假设

在相同失败代码和停止证据基础上，对照是否补充能力说明。 每条件三次候选生成中，能力说明组能否超过原反馈组的原生得分。

## 实际工作

原反馈/能力说明各生成3个候选，使用五个历史布局执行；保存6份请求、响应、候选源码和原生回执。

## 指标与结论

30个新有评分回合；六候选各为[0,0,0,0,15]、均分3、成功0/5。6次API，input每次15316/15755，total106959，历史估算$0.1846203。

本批实际运行没有组间得分提升；后续发现能力说明与真实包装层不一致，不能据此断言部署一致的能力反馈无效。

## 解释与限制

说明把后台错误字典当成候选所见返回，真实包装层会抛RuntimeError；早期CPU夹具未覆盖此层。保留原分数、代码和账目，用批次40更正解释。

不同任务、执行条件、重复布局、复用对照与生成样本分别计数。原报告是当时快照，若与后续契约更正冲突，以标有来源的更正解释为准，不改原分数。

## 复核与下一步

阅读真实包装回放及历史契约更正，不使用这一批否定一致契约下的反馈方法。 原始脚本与协议是复现依据，不能原地重跑覆盖结果。本批加入[整周执行账本](../../evidence/period_20261105_20261108/tables/native_episodes_all.json)，没有把旧回合重复计为新执行。

## 原件与来源

- [20261106_v1/protocol.json](../../evidence/period_20261105_20261108/stages/33/20261106_v1/protocol.json) — SHA256 `803f851be1245b2f16c8d2c293ec791983de556f683f42ae7a1a7f47b445c8bb`；实验室原件 `/mnt/data/joey_tr/physical-RSI/result/33_system2_capability_feedback/20261106_v1/protocol.json`。
- [20261106_v1/FINAL_SUMMARY.json](../../evidence/period_20261105_20261108/stages/33/20261106_v1/FINAL_SUMMARY.json) — SHA256 `71b851466dfe4fc25cefdb3e4db1c32890ecf05aa3686704e61d09db1fbbc2aa`；实验室原件 `/mnt/data/joey_tr/physical-RSI/result/33_system2_capability_feedback/20261106_v1/FINAL_SUMMARY.json`。
- [20261106_v1/REPORT.txt](../../evidence/period_20261105_20261108/stages/33/20261106_v1/REPORT.txt) — SHA256 `5e2fc5e1bffe1e14b8daf00daab04d89d0b32dcc46e7e03fb56953b6ed130e1a`；实验室原件 `/mnt/data/joey_tr/physical-RSI/result/33_system2_capability_feedback/20261106_v1/REPORT.txt`。

另见[独立原始回执与usage复算](../../evidence/period_20261105_20261108/audit/independent-recomputation.json)、[专项解释复核](../../evidence/period_20261105_20261108/audit/SCIENCE_REVIEW_ZH.md)。

## 具体复现入口补充

精确入口 `native-validation/run_native.py`，SHA256 `245722a6b742e0a9ea8baafbbb9a13b87946fc9b0f807f40b3015c8fbf142d5c`。development:运行ID[0,1,2,3,4]/源ID[0,1,2,3,4]；classify_objects原生1100步。

已读取3份本批native/request.json，记录原生执行seed=[0]；逐件路径/SHA见复现索引。这不是布局生成seed；场景以各阶段layout ID与SHA256绑定，不把求解器seed或重复布局当成独立场景。

原始源文件、原生子进程argv（若保存）、分开的软件版本及硬件事实见[批次33复现索引](../../evidence/period_20261105_20261108/reproduction/README.md#batch-33)。该索引区分已保存命令与无法确认项，本次不运行历史程序。
