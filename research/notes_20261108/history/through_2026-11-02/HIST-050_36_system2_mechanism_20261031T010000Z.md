# HIST-050 · 机制诊断第一版准备

- 历史记录范围（北京时间）： 至 。
- 时间依据：run ID timestamp only; exact execution times not inferred
- 本次回溯补录：2026-11-05 11:40，不是重跑日期。
- 类型：`preparation`；原批次：`36_system2_mechanism_20261031T010000Z`。
- 原件现址：`/mnt/data/joey_tr/physical-RSI/result/21_system2_failure_mechanisms/36_system2_mechanism_20261031T010000Z/`。历史文件中的旧执行路径保留作来源，本次导航统一指向实验室。
- 周志性质：协议、准备、审计或管理节点，未作为新的物理实验累计。

## 做了什么与得到什么

保存机制实验的早期脚本准备。

该目录只有准备材料；完成的九次原生尝试见 v3。

## 解释边界与失败记录

判定：**部分**。不增加已完成实验数。

## 复现与证据定位

本次只读取与离线复算；历史 runner、日志、协议、依赖指纹保留在下列原件。不同阶段的补丁和环境不能用一个背景 commit 替代。未明确记录的 seed、硬件或启动命令保持未知，不从今天服务器配置倒推。

| 证据原件（实验室现址） | SHA256 |
|---|---|
| procedures/diagnostic_waypoints.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/21_system2_failure_mechanisms/36_system2_mechanism_20261031T010000Z/procedures/diagnostic_waypoints.py`） | `21639d3c67656d12c0ad038b26113a1cd6fc64fb8810ab061afad7bab7f59ac0` |
| procedures/system2_mechanism_control.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/21_system2_failure_mechanisms/36_system2_mechanism_20261031T010000Z/procedures/system2_mechanism_control.py`） | `6b2dbb5177a9197aa1b4e6aa06e4970f5348d59f5c7a84b3a0427241e126035f` |
| procedures/system2_diagnostic_primitives.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/21_system2_failure_mechanisms/36_system2_mechanism_20261031T010000Z/procedures/system2_diagnostic_primitives.py`） | `4f8a2d83b5201dd0a53d54e5a3fd4399777ad869b516a95c99df399b70e7b82b` |

## 阅读覆盖与下一步

本单元 3 个可读普通文件、3 种不同字节内容已完整读入并校验；逐文件清单见 [审计账本](../../evidence/readthrough_20261102/file-review-ledger.jsonl.gz)，按 `HIST-050` 检索。JSON/日志/代码等做对应结构分析，重点协议、结果、失败和计量证据用于本条解释；这不声称所有依赖副本逐行人工精读，或全部视频逐帧人工审片。

下一步：本阶段记录封存至 11 月 2 日结束。后续实验另登记；如需补证，先定位本条限制对应原件，不自动重跑。
