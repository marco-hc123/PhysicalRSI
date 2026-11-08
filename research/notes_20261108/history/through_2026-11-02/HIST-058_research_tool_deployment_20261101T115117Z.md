# HIST-058 · 研究记录模板部署

- 历史记录范围（北京时间）：2026-11-01 至 2026-11-01。
- 时间依据：来源：原记录日期/登记目录；不把文件传输时间当实验开始时间。
- 本次回溯补录：2026-11-05 11:40，不是重跑日期。
- 类型：`administration`；原批次：`research_tool_deployment_20261101T115117Z`。
- 原件现址：`/mnt/data/joey_tr/physical-RSI/result/research_tool_deployment_20261101T115117Z/`。历史文件中的旧执行路径保留作来源，本次导航统一指向实验室。
- 周志性质：协议、准备、审计或管理节点，未作为新的物理实验累计。

## 做了什么与得到什么

把协作协议和管理脚本放入研究目录。

36个文件核验、9个Python文件语法检查，部署状态 verified。

## 解释边界与失败记录

判定：**N**。模板是记录流程工具，未部署常驻独立模型 Agent。

## 复现与证据定位

本次只读取与离线复算；历史 runner、日志、协议、依赖指纹保留在下列原件。不同阶段的补丁和环境不能用一个背景 commit 替代。未明确记录的 seed、硬件或启动命令保持未知，不从今天服务器配置倒推。

| 证据原件（实验室现址） | SHA256 |
|---|---|
| status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/research_tool_deployment_20261101T115117Z/status.json`） | `ba6db4415bc7e0922141cfefe7463b7a136c8cb198b0c6f45951e6d564fd15be` |
| manifest.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/research_tool_deployment_20261101T115117Z/manifest.json`） | `ddd6610cc3e2eac2143e5624c1e62899a8cfe8c677b6e4c381013342eb325726` |
| lint_protocol.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/research_tool_deployment_20261101T115117Z/lint_protocol.log`） | `93f829d9bde89c0695b7e8a498247d8d3bfc8207e28525de8472877b643844b1` |
| session_check.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/research_tool_deployment_20261101T115117Z/session_check.log`） | `81a716f7aa17443f0a5e33e462491b97b1bc267fd1efefb27ce69fec6133edd5` |

## 阅读覆盖与下一步

本单元 4 个可读普通文件、4 种不同字节内容已完整读入并校验；逐文件清单见 [审计账本](../../evidence/readthrough_20261102/file-review-ledger.jsonl.gz)，按 `HIST-058` 检索。JSON/日志/代码等做对应结构分析，重点协议、结果、失败和计量证据用于本条解释；这不声称所有依赖副本逐行人工精读，或全部视频逐帧人工审片。

下一步：本阶段记录封存至 11 月 2 日结束。后续实验另登记；如需补证，先定位本条限制对应原件，不自动重跑。
