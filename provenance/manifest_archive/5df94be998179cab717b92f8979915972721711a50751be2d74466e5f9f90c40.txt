# 研究证据导航（2026-11-02）

先读 [最新研究总览](RESEARCH_OVERVIEW_ZH.md)。本页按研究问题导航；不是实验启动清单。所列样本均为已记录的历史执行，本次整理新增 API 与机器人回合均为 0。

| 研究问题 | 数据、分母与统计边界 | 仓库入口 |
|---|---|---|
| 调用粒度如何影响语言开销 | 旧版 28 调度配置、512 CPU 代理回合；非机器人结果 | [版本化机制证据](../experiments/mechanism_audit/README.md) |
| 单次提示目录有多大 | 静态字符/tokenizer 估算与供应商 usage 分开 | [当前提示审计](../experiments/mechanism_audit/current/prompt_audit/prompt_sizes.csv) |
| 减少目录是否减少 API 消耗 | 80 次探索与 20 场景×2条件×3次=120 次；保留契约失败 | [API 数据、协议与原件](../experiments/fixed_input_api/README.md) |
| 原生任务中目录精简的作用 | 每条件 15 个尝试；完成 native 15/14，成功 5/6 | [30 例明细](../experiments/history/catalogue_ablation/cases.csv) |
| 正式原生路线效果 | 2任务×4路线×5布局=40 正式回合 | [逐例与冻结协议](../experiments/history/classification_reference/episode-metrics.csv) |
| 如何固定比较条件 | 布局分割、指标词典、模型与技能条件 | [协议冻结](../experiments/history/protocol_freeze/protocol.json) |
| 项目 A 的公开依据是什么 | 公共数据与历史源码审计，未运行 A | [公开参考快照](../experiments/public_reference/project_a/project-a-current-data.json)、[来源](../experiments/public_reference/project_a/retrieval-manifest.json) |
| 两项目 Token 差距怎样计算 | 每任务/方法 n=5，缓存是输入子集；非等质量因果对比 | [对应比较表](../experiments/history/task_extension_and_final_test/final-review/matched-project-comparison.csv) |
| B 的时间花在哪里 | 分项计时与区间重叠，A 全墙钟未知 | [计时分项](../experiments/history/task_extension_and_final_test/comparison-analysis/timing-interval-summary.csv)、[3对冷启动补测](../experiments/history/task_extension_and_final_test/final-review/targeted-timing-pairs.csv) |
| System 2 是否改善 | 历史2正式轮，每轮父/候选各5例，均0分，retain_parent | [原两轮记录](../experiments/history/system2_qwen/)、[提案账目](../experiments/history/task_extension_and_final_test/final-review/system2-proposal-details.csv) |
| 最终固定策略是否能独立通过 | pi05两任务各10布局；不是整个Agent成绩 | [独立验收逐例](../experiments/history/task_extension_and_final_test/exports/independent-final-episodes.csv) |
| 状态能否按已验路径恢复 | 软件检查+baseline/restored各1次native smoke，均0分 | [恢复结果](../experiments/history/state_recovery/step6-results.json) |
| 失败发生在哪层 | 9诊断启动=5自然结束0分+4异常未知；24离线规划另列 | [机制报告](../experiments/history/system2_diagnostics/report-zh.txt) |
| 有限扩展表现 | 三任务各5例：1/5、3/5、4/5 | [任务汇总](../experiments/history/task_extension_and_final_test/exports/task-summary.csv) |
| 换高层模型的影响 | 新增10 GPT native与10正式HTTP；另外10行是旧对照 | [System 1 GPT](../experiments/system1_gpt/RESULTS_ZH.md) |
| 换候选生成模型的影响 | 1候选；父/候选各5完成+1基础设施中断；无新独立验收 | [System 2 GPT](../experiments/system2_gpt/RESULTS_ZH.md) |
| 补测应怎样加入汇报 | 保留旧结果，与新模型/设置分开解释 | [整合说明](../reports/supplement_20261102/REPORT_INTEGRATION.md) |
| 现场展示什么 | 3段真实历史视频及3张终末帧，非GPT新视频或随机样本 | [视频、时刻与哈希](../reports/evidence/media/README.md) |

## 完整叙述与图表

- [历史详细报告集合](../reports/research_archive_20261101/README.md)：主报告、每阶段核对、场景数据字典、失败机制和汇报大纲。
- [图表及可编辑数据](../reports/evidence/README.md)：新增表格清单及 SVG/PNG；其中历史统计范围保持原协议，不会自动包含今天的 GPT 补测。
- [本次仓库核对及上传边界](../provenance/REPOSITORY_REVIEW_20261102.md)。
- `provenance/material-map-20261102.json` 映射原离线包路径至仓库位置；`provenance/experiment-coverage-20261102.csv` 为已核对的实验室批次索引（含部署/修复目录，不代表独立实验数）。

## 如何判断资料是否足够

根 README → 最新总览 → 本页 → 指定批次协议/CSV/原子证据。历史报告中某些路径为原执行位置，不能据其本机不可访问判定数据没有产生。未上传的权重、全部观测和逐步日志不宣称已在 Git 验证；完整原件仍在既有档案。

旧辅助表 `early-api-reductions-reviewed.csv` 的 API120 `evidence_level` 保留了早期审计标签。后来 2026-11-01 已完成原件复核；本次再次取得实验室原件并用 `tools/verify_research_evidence.py` 复算。判断当前证据强度以原件和新核验为准，旧快照标签不覆盖新证据。
