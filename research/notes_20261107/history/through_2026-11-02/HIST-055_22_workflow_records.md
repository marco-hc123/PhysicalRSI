# HIST-055 · 历史工作流导航整理

- 历史记录范围（北京时间）：历史导航；单一执行日期不适用 至 历史导航；单一执行日期不适用。
- 时间依据：来源：原记录日期/登记目录；不把文件传输时间当实验开始时间。
- 本次回溯补录：2026-11-05 11:40，不是重跑日期。
- 类型：`administration`；原批次：`22_workflow_records`。
- 原件现址：`/mnt/data/joey_tr/physical-RSI/result/22_workflow_records/`。历史文件中的旧执行路径保留作来源，本次导航统一指向实验室。
- 周志性质：协议、准备、审计或管理节点，未作为新的物理实验累计。

## 做了什么与得到什么

将已有批次按研究主题和日期组织。

原时间戳与导航链接保留，43 条阶段索引及其历史计划状态可追溯。

## 解释边界与失败记录

判定：**N**。历史 planned/PID 不是截至11月2日的当前任务状态，也不是新增执行。

## 复现与证据定位

本次只读取与离线复算；历史 runner、日志、协议、依赖指纹保留在下列原件。不同阶段的补丁和环境不能用一个背景 commit 替代。未明确记录的 seed、硬件或启动命令保持未知，不从今天服务器配置倒推。

| 证据原件（实验室现址） | SHA256 |
|---|---|
| original_control_records/CURRENT_FINAL_REPORT.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/22_workflow_records/original_control_records/CURRENT_FINAL_REPORT.json`） | `6f343813c227e3b43fd0f2e7623a7b991a59d2792300a54af5dca907fd42b8eb` |
| 阶段说明.txt（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/22_workflow_records/阶段说明.txt`） | `7dfe39477b58ccb9b8d8ab35d86a06facf3673c3287ed514c94dde86687fcd2d` |
| by_experiment_date/说明.txt（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/22_workflow_records/by_experiment_date/说明.txt`） | `f0b3bbbfec877b769945119b2790304b0e054e69c96668772ad8b392e42df56f` |
| original_control_records/CURRENT_STEP4.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/22_workflow_records/original_control_records/CURRENT_STEP4.json`） | `fe4851296d352cab4012f2525cca586dfc12c7619ecf8ce20b46fbb5818db776` |
| original_control_records/CURRENT_STEP5.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/22_workflow_records/original_control_records/CURRENT_STEP5.json`） | `7b77d8a47f28f43f086f9c7c81bdf4f9c3ab0a8240219cefc90bdfb8004f22f9` |
| original_control_records/CURRENT_STEP6.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/22_workflow_records/original_control_records/CURRENT_STEP6.json`） | `d5d7c16884282f1e86de5938ffdfedf62eb444a980ec59ed7576a59c1dad1c1d` |
| original_control_records/CURRENT_STEP7.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/22_workflow_records/original_control_records/CURRENT_STEP7.json`） | `9b8429a80d17887f618df041e3e84aa919fb62d2c0030746e7e49c7155ed2afd` |
| original_control_records/CURRENT_STEPS23.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/22_workflow_records/original_control_records/CURRENT_STEPS23.json`） | `918a00b4c46dc7635126952577924cb66cffe16d799516170950e3a100f9ed61` |
| original_control_records/PAUSED_20261028.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/22_workflow_records/original_control_records/PAUSED_20261028.json`） | `4d2af3de3ee4c7553921dd0e29ec9476b2aedaf16d3c65a91e0be670a8e92711` |
| original_control_records/CURRENT_SUITE_RUN.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/22_workflow_records/original_control_records/CURRENT_SUITE_RUN.json`） | `4e54ba3ecbd09953563f79cc199669e28bc53eb87a280c868bfa5013b8be4147` |
| original_control_records/CURRENT_FINAL_TEST.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/22_workflow_records/original_control_records/CURRENT_FINAL_TEST.json`） | `aab897534e805f259cee04f4900bf286c6794fc382fadb04328d674154b8cad9` |
| original_control_records/PENDING_STEPS23_V2.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/22_workflow_records/original_control_records/PENDING_STEPS23_V2.json`） | `2bcfa9700ab332380bfa512ea0be797dabb8310bd60b53400aa12d243d64969d` |
| original_control_records/CURRENT_NATIVE_SCENE.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/22_workflow_records/original_control_records/CURRENT_NATIVE_SCENE.json`） | `f203ee44b8a87ac079b0c428bf86a29d2ad11e63d08a2400c834c0f55f9c377b` |
| original_control_records/CURRENT_QWEN_EPISODE.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/22_workflow_records/original_control_records/CURRENT_QWEN_EPISODE.json`） | `2ff56a1fb43361a31cc227b2250cfd0e97d91470365bd89a0a98bc466dd67c00` |

## 阅读覆盖与下一步

本单元 39 个可读普通文件、39 种不同字节内容已完整读入并校验；逐文件清单见 审计账本（原始归档位置：`../../evidence/readthrough_20261102/file-review-ledger.jsonl.gz`），按 `HIST-055` 检索。JSON/日志/代码等做对应结构分析，重点协议、结果、失败和计量证据用于本条解释；这不声称所有依赖副本逐行人工精读，或全部视频逐帧人工审片。

下一步：本阶段记录封存至 11 月 2 日结束。后续实验另登记；如需补证，先定位本条限制对应原件，不自动重跑。
