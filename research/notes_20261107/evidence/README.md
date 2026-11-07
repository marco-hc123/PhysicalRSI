# 已完成阶段的证据表

这些表是 2026-11-01 既有阶段报告的原字节副本，用于索引与复核。复制时间不是实验时间，本次没有新增 API、训练或原生评估。`provenance.json` 保存每个副本的 SHA256。

| 文件 | 用途 |
|---|---|
| `api120-raw-recomputed.json` | 120 次合成输入 API 的既有复算结果；服务器原摘要在 `../../result/05_api20_execution_20261027/summary.json` |
| `system1_reference_matrix.csv` | 两任务、四路线、每格 5 个布局的原生参考矩阵 |
| `system2_rounds.csv` | 两轮父策略/候选验证与选择结果 |
| `independent-final-episodes.csv` | 最终保留 pi05 的 20 个独立验收案例 |
| `catalogue_ablation.csv` | 原生目录消融，两个条件各 15 个逻辑案例 |
| `targeted-timing-pairs.csv` | 3 对 cold/continuous 计时结果 |
| `unknowns-and-evidence-gaps.csv` | 已有报告的 20 个跟踪条目，其中一个已闭合，其余有限制或待补证 |

统一从 [HISTORY.md](../HISTORY.md) 和 [实验室结果目录索引](../history/result_inventory.csv) 访问当前服务器原件。表内原始来源字段保留作溯源，不作为本工作区的目录组织方式。所有论文式结论须回到原协议、评分与供应商原件，不能只依据汇总表推断。


## 2026-11-02 追加证据

[模型替换补测入口](model_swap_20261102/README.md)保存新表、离线复算与[报告整合说明](model_swap_20261102/REPORT_INTEGRATION.md)。原有证据表不变；新增记录为EXP-2026W45-001与EXP-2026W45-002。最新结果不应仅从旧的2026-11-01摘要读取。
