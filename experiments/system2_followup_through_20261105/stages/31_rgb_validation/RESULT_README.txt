本批任务：完成 35 个冻结的原生 RGB 补测、分析及实验室归档。

condition | successes / cases | mean Score (0-100) | cohort wall time (min)
pi05 | 0/5 | 0.00 | 15.07
baseline_1 | 0/5 | 0.00 | 15.75
augmented_1 | 0/5 | 3.00 | 16.05
augmented_2 | 0/5 | 3.00 | 15.94
baseline_2 | 0/5 | 0.00 | 15.31
baseline_3 | 0/5 | 0.00 | 15.29
augmented_3 | 0/5 | 0.00 | 15.93

这是5个历史诊断布局上的执行验证；部分分、完整成功与独立泛化必须分开。
本轮没有重新生成候选或运行策略选择器，保留pi05；新增付费API调用和费用均为0。
先读 analysis/REPORT.txt，再看 analysis/cohort-summary.csv、actor-diagnostics.csv 和 ordered-call-traces.csv。
原始结果和全部105段视频位于 native-campaign/runs/；精选帧在 analysis/keyframes/。
使用 REPRODUCE.txt 中的只读命令可核查归档。
迁移完成以 migration/ARCHIVE_VERIFIED.json 为准；.incoming 目录不是最终归档。
