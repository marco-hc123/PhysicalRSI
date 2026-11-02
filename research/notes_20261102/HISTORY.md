# 实验室 PhysicalRSI 结果总入口

统一研究根目录：`/mnt/data/joey_tr/physical-RSI`。核对时间：2026-11-01 20:13。用户要求所有结果按实验室服务器现有目录组织。

## 覆盖范围

- [结果目录索引](history/result_inventory.csv)：本次可见的 31 个顶层结果条目，包括目录、导航文件与单独标注的记录工具管理材料。
- [历史批次索引](history/experiment_index.csv)：原阶段索引中的 43 条批次记录，现有目录 43 条全部可访问。
- 原始 [实验过程索引](../result/实验过程索引.csv) 保留；派生索引统一给出实验室现有位置。
- 本页为全目录导航及重点摘要，未声称逐字复核每个日志或重算全部实验。目录/批次数不是 API 次数或机器人 episode 数。
- 索引中的状态与日期是原记录的历史快照，不代表相应进程仍运行。

## 全部结果目录与导航

| 名称 | 类别 | 阶段索引行数 | 入口 |
|---|---|---:|---|
| 00_protocol | existing_research_result_or_navigation | 0 | [打开](../result/00_protocol) |
| 00_第一步完成情况.txt | existing_research_result_or_navigation | 0 | [打开](../result/00_第一步完成情况.txt) |
| 01_environment | existing_research_result_or_navigation | 0 | [打开](../result/01_environment) |
| 02_code_audit | existing_research_result_or_navigation | 0 | [打开](../result/02_code_audit) |
| 02_completion.json | existing_research_result_or_navigation | 0 | [打开](../result/02_completion.json) |
| 03_api_connectivity | existing_research_result_or_navigation | 0 | [打开](../result/03_api_connectivity) |
| 03_api_experiments | existing_research_result_or_navigation | 0 | [打开](../result/03_api_experiments) |
| 04_next_batch_20_scenes | existing_research_result_or_navigation | 0 | [打开](../result/04_next_batch_20_scenes) |
| 05_api20_execution_20261027 | existing_research_result_or_navigation | 0 | [打开](../result/05_api20_execution_20261027) |
| 06_policy_environment_20261029 | existing_research_result_or_navigation | 0 | [打开](../result/06_policy_environment_20261029) |
| 07_rerun_compatibility_20261029 | existing_research_result_or_navigation | 0 | [打开](../result/07_rerun_compatibility_20261029) |
| 08_simulation_setup | existing_research_result_or_navigation | 12 | [打开](../result/08_simulation_setup) |
| 09_single_task_validation | existing_research_result_or_navigation | 6 | [打开](../result/09_single_task_validation) |
| 10_general_pickup_comparison | existing_research_result_or_navigation | 1 | [打开](../result/10_general_pickup_comparison) |
| 11_catalogue_ablation | existing_research_result_or_navigation | 1 | [打开](../result/11_catalogue_ablation) |
| 12_cross_project_measurement | existing_research_result_or_navigation | 2 | [打开](../result/12_cross_project_measurement) |
| 13_failure_consistency | existing_research_result_or_navigation | 1 | [打开](../result/13_failure_consistency) |
| 14_protocol_freeze | existing_research_result_or_navigation | 1 | [打开](../result/14_protocol_freeze) |
| 15_system1_diagnostics_memory | existing_research_result_or_navigation | 5 | [打开](../result/15_system1_diagnostics_memory) |
| 16_system2_integration | existing_research_result_or_navigation | 1 | [打开](../result/16_system2_integration) |
| 17_system2_iterations | existing_research_result_or_navigation | 6 | [打开](../result/17_system2_iterations) |
| 18_state_recovery | existing_research_result_or_navigation | 1 | [打开](../result/18_state_recovery) |
| 19_extended_tasks_final_acceptance | existing_research_result_or_navigation | 2 | [打开](../result/19_extended_tasks_final_acceptance) |
| 20_targeted_timing | existing_research_result_or_navigation | 1 | [打开](../result/20_targeted_timing) |
| 21_system2_failure_mechanisms | existing_research_result_or_navigation | 3 | [打开](../result/21_system2_failure_mechanisms) |
| 22_workflow_records | existing_research_result_or_navigation | 0 | [打开](../result/22_workflow_records) |
| 23_lab_environment_setup | existing_research_result_or_navigation | 0 | [打开](../result/23_lab_environment_setup) |
| research_tool_deployment_20261101T115117Z | recording_tool_administration | 0 | [打开](../result/research_tool_deployment_20261101T115117Z) |
| research_tool_initialization_20261101T120523Z | recording_tool_administration | 0 | [打开](../result/research_tool_initialization_20261101T120523Z) |
| setup_logs | existing_research_result_or_navigation | 0 | [打开](../result/setup_logs) |
| 实验过程索引.csv | existing_research_result_or_navigation | 0 | [打开](../result/实验过程索引.csv) |

## 当前四组代表性记录

| 记录 | 已有结果 | 边界 |
|---|---|---|
| [EXP-2026W44-001](LOGS/2026-W44.md#exp-2026w44-001) | 120 次合成输入 API；输入均值下降 67.31%，HTTP 均时下降 31.65% | 没有机器人动作；不是同等质量费用或总墙钟优势 |
| [EXP-2026W44-002](LOGS/2026-W44.md#exp-2026w44-002) | 两任务×四路线×五布局；code 2/5、1/5，Agent 1/5、1/5 | 有限队列，不能与其他布局组混算 |
| [EXP-2026W44-003](LOGS/2026-W44.md#exp-2026w44-003) | System 2 两轮未提高验证分数，保留父策略 | 工程流程完成不等于能力提升 |
| [EXP-2026W44-004](LOGS/2026-W44.md#exp-2026w44-004) | 最终 pi05 两任务各 0/10 | 对象是保留策略，不是整个 Agent |

其余 API 批次、general_pickup、目录消融、环境修复、扩展任务、计时、恢复与机制诊断均从上表进入；不会因摘要仅选四组而移除其他历史结果。

## 证据管理

原件继续保留在各自结果目录。`evidence/` 是既有报告部分表格的校验副本，源文件哈希和表内原字段保留；实际查阅以本页的实验室入口为准。原视频、模型与大日志不复制到科研记录目录。


## 2026-11-02 新增补测（优先入口）

新增原始结果与核对说明已按主题归档；43条旧批次仍保留，当前派生索引为45条科学批次。管理归档目录不计实验批次。

| 新记录 | 结果与用途 | 当前入口 |
|---|---|---|
| [EXP-2026W45-001](LOGS/2026-W45.md#exp-2026w45-001) | System 1高层模型替换，10个新回合，对照历史10行 | [原件](../result/24_system1_model_swap/37_gpt61sol_supplement_20261102/README_归档入口.md) |
| [EXP-2026W45-002](LOGS/2026-W45.md#exp-2026w45-002) | System 2一个新候选，10正常回合与1中断，保留父策略 | [原件](../result/25_system2_model_swap/38_system2_gpt61sol_20261102/README_归档入口.md) |
| 材料归档核验 | 四个ZIP原件、完整成员映射、哈希及文档备份 | [导入记录](../result/26_supplement_import/20261102T105827Z/) |

[报告应添加的位置和最新结论](evidence/model_swap_20261102/REPORT_INTEGRATION.md)、[批次索引](history/supplement_index_20261102.csv)、[账目](evidence/model_swap_20261102/accounting.csv)。本次只导入已完成补测，新API/仿真/训练均0。新包不含原始视频；未提供的逐步原件与视频仍待补齐，不能称为全量原生证据迁入完成。

页面上方“31个顶层条目、43条批次”为2026-11-01初始化快照；当前目录清单以history/result_inventory.csv及index_status.json的supplement_update为准。
