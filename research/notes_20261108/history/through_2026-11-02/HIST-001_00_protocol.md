# HIST-001 · 固定研究版本与计量协议

- 历史记录范围（北京时间）：2026-10-26 至 2026-10-26。
- 时间依据：来源：原记录日期/登记目录；不把文件传输时间当实验开始时间。
- 本次回溯补录：2026-11-05 11:40，不是重跑日期。
- 类型：`protocol`；原批次：`00_protocol`。
- 原件现址：`/mnt/data/joey_tr/physical-RSI/result/00_protocol/`。历史文件中的旧执行路径保留作来源，本次导航统一指向实验室。
- 周志性质：协议、准备、审计或管理节点，未作为新的物理实验累计。

## 做了什么与得到什么

锁定主源码与复用计量工具的来源，明确 PhysicalRSI 是复现对象。

source-pins 与工具来源记录保留；主阶段源码为 90b322a3a362aad14125f36d8ed080ca31daaea6。

## 解释边界与失败记录

判定：**N**。工具和合成 fixture 的存在不构成真实机器人或模型性能证据。

## 复现与证据定位

本次只读取与离线复算；历史 runner、日志、协议、依赖指纹保留在下列原件。不同阶段的补丁和环境不能用一个背景 commit 替代。未明确记录的 seed、硬件或启动命令保持未知，不从今天服务器配置倒推。

| 证据原件（实验室现址） | SHA256 |
|---|---|
| source-pins.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/00_protocol/source-pins.json`） | `f5e9ee5f48ad797599677045a6524f90387f77e24829992b0bf8f5f22af51c94` |
| measurement-tool-provenance.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/00_protocol/measurement-tool-provenance.json`） | `8ccdb9c074b08c89781f61c3461a99dd85d30537fdd13a4683d8cfc7fa7c2dda` |

### 原协议中可直接定位的字段

来源 `result/00_protocol/source-pins.json`：
- `source_url` = `https://github.com/PhysicalRSI/PhysicalRSI.git`
- `commit` = `90b322a3a362aad14125f36d8ed080ca31daaea6`


## 阅读覆盖与下一步

本单元 2 个可读普通文件、2 种不同字节内容已完整读入并校验；逐文件清单见 [审计账本](../../evidence/readthrough_20261102/file-review-ledger.jsonl.gz)，按 `HIST-001` 检索。JSON/日志/代码等做对应结构分析，重点协议、结果、失败和计量证据用于本条解释；这不声称所有依赖副本逐行人工精读，或全部视频逐帧人工审片。

下一步：本阶段记录封存至 11 月 2 日结束。后续实验另登记；如需补证，先定位本条限制对应原件，不自动重跑。
