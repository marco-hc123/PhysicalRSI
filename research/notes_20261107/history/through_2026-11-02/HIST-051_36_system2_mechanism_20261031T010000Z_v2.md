# HIST-051 · 机制诊断第二版前置失败

- 历史记录范围（北京时间）： 至 。
- 时间依据：run ID timestamp only; exact execution times not inferred
- 本次回溯补录：2026-11-05 11:40，不是重跑日期。
- 类型：`preflight`；原批次：`36_system2_mechanism_20261031T010000Z_v2`。
- 原件现址：`/mnt/data/joey_tr/physical-RSI/result/21_system2_failure_mechanisms/36_system2_mechanism_20261031T010000Z_v2/`。历史文件中的旧执行路径保留作来源，本次导航统一指向实验室。
- 周志：[ EXP-2026W44-031 ](../../LOGS/2026-W44.md#exp-2026w44-031)。同一批次已有摘要/续接副本不新增实验计数。

## 做了什么与得到什么

检查诊断 primitive 是否可导入。

preflight 报 No module named system2_diagnostic_primitives，后续以 v3 完成。

## 解释边界与失败记录

判定：**Crashed**。模块准备失败不是一组完成的物理对照。

## 复现与证据定位

本次只读取与离线复算；历史 runner、日志、协议、依赖指纹保留在下列原件。不同阶段的补丁和环境不能用一个背景 commit 替代。未明确记录的 seed、硬件或启动命令保持未知，不从今天服务器配置倒推。

| 证据原件（实验室现址） | SHA256 |
|---|---|
| cases.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/21_system2_failure_mechanisms/36_system2_mechanism_20261031T010000Z_v2/cases.json`） | `b3eace49fa2c531294993394704323504c74a7699f7a8931c8bfcff0a0ec5d0e` |
| procedures/diagnostic_waypoints.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/21_system2_failure_mechanisms/36_system2_mechanism_20261031T010000Z_v2/procedures/diagnostic_waypoints.py`） | `21639d3c67656d12c0ad038b26113a1cd6fc64fb8810ab061afad7bab7f59ac0` |
| procedures/system2_mechanism_control.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/21_system2_failure_mechanisms/36_system2_mechanism_20261031T010000Z_v2/procedures/system2_mechanism_control.py`） | `6b2dbb5177a9197aa1b4e6aa06e4970f5348d59f5c7a84b3a0427241e126035f` |
| procedures/system2_diagnostic_primitives.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/21_system2_failure_mechanisms/36_system2_mechanism_20261031T010000Z_v2/procedures/system2_diagnostic_primitives.py`） | `4f8a2d83b5201dd0a53d54e5a3fd4399777ad869b516a95c99df399b70e7b82b` |
| conditions/original_dense/preflight.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/21_system2_failure_mechanisms/36_system2_mechanism_20261031T010000Z_v2/conditions/original_dense/preflight.json`） | `26e2591a23644fa76588528ae249be032ac3544552c468a8e516c84292383f24` |

## 阅读覆盖与下一步

本单元 5 个可读普通文件、5 种不同字节内容已完整读入并校验；逐文件清单见 审计账本（原始归档位置：`../../evidence/readthrough_20261102/file-review-ledger.jsonl.gz`），按 `HIST-051` 检索。JSON/日志/代码等做对应结构分析，重点协议、结果、失败和计量证据用于本条解释；这不声称所有依赖副本逐行人工精读，或全部视频逐帧人工审片。

下一步：本阶段记录封存至 11 月 2 日结束。后续实验另登记；如需补证，先定位本条限制对应原件，不自动重跑。
