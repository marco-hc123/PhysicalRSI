# HIST-032 · 低成功率与复现一致性审计

- 历史记录范围（北京时间）：2026-10-29T20:35:15.935792+08:00 至 2026-10-29T20:36:05.231913+08:00。
- 时间依据：original structured timestamp fields; observed record range is not necessarily physical rollout duration
- 本次回溯补录：2026-11-05 11:40，不是重跑日期。
- 类型：`audit`；原批次：`22_failure_consistency_20261029T121940Z`。
- 原件现址：`/mnt/data/joey_tr/physical-RSI/result/13_failure_consistency/22_failure_consistency_20261029T121940Z/`。历史文件中的旧执行路径保留作来源，本次导航统一指向实验室。
- 周志性质：协议、准备、审计或管理节点，未作为新的物理实验累计。

## 做了什么与得到什么

排查版本、资产和原生评分解释错误。

检查 21 条评估记录、其中 19 native；选定源码和场景检查没有发现预期外完整性问题，新增 API/native 均为 0。

## 解释边界与失败记录

判定：**部分**。选定完整性检查不是与作者全部环境严格等价的证明；缺少最终对象变换时不事后补判成功。

## 复现与证据定位

本次只读取与离线复算；历史 runner、日志、协议、依赖指纹保留在下列原件。不同阶段的补丁和环境不能用一个背景 commit 替代。未明确记录的 seed、硬件或启动命令保持未知，不从今天服务器配置倒推。

| 证据原件（实验室现址） | SHA256 |
|---|---|
| protocol.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/13_failure_consistency/22_failure_consistency_20261029T121940Z/protocol.json`） | `12242135edee4a86f3c3d85dde7d6f5d92e8363881af3e0faad330a61a2ec00e` |
| COMPLETION.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/13_failure_consistency/22_failure_consistency_20261029T121940Z/COMPLETION.json`） | `e5fd8b4854b791102833c6a912b79f04478f8cd6362c04d2040db599aa4dd021` |
| status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/13_failure_consistency/22_failure_consistency_20261029T121940Z/status.json`） | `730a8d543a2ed34c1cd6277f60213c0c848e6c14cc301147283b87c40ec36c68` |
| archive-manifest.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/13_failure_consistency/22_failure_consistency_20261029T121940Z/archive-manifest.json`） | `bfb68613df4ac6bc045fcbec69fe1e7d9953df214028a660b11f1a74573b8e49` |
| inventory-summary.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/13_failure_consistency/22_failure_consistency_20261029T121940Z/inventory-summary.json`） | `8482a2aa7dd06384d3efaf06d1fac5ef01a7d43791cdb5126fac44cacfba9612` |
| analysis-sources/cloud_failure_report.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/13_failure_consistency/22_failure_consistency_20261029T121940Z/analysis-sources/cloud_failure_report.py`） | `1b01edf54e90b6d11a85f3f28e57116ea32603cd662c66c67d562b5159ccd9ce` |
| audit.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/13_failure_consistency/22_failure_consistency_20261029T121940Z/audit.log`） | `8d2e372bb1ea40d46423530e431a07237a51a8295941b2792d7c8ac1cdcab34f` |
| visuals.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/13_failure_consistency/22_failure_consistency_20261029T121940Z/visuals.log`） | `aba28804c3413e4bbf4a12f906efc891e6ea67c684311e3dfa9e400866eb8e41` |
| audit-v2.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/13_failure_consistency/22_failure_consistency_20261029T121940Z/audit-v2.log`） | `2f132fe3ed6133d8c8c2953a53b8505b89ca3b5acd908baac47888c7a5e0ff0a` |
| 低成功率复现偏差检查.txt（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/13_failure_consistency/22_failure_consistency_20261029T121940Z/低成功率复现偏差检查.txt`） | `de7e7538718e5ed5913bbc1e30d623678a55fde49536bd4c51c4298d1f080e2e` |
| secret-scan.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/13_failure_consistency/22_failure_consistency_20261029T121940Z/secret-scan.json`） | `0a3f8a98d34f11060b657093ee8782f65aca8278766dfa15a5143d9eca71e0ab` |
| case-diagnosis.csv（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/13_failure_consistency/22_failure_consistency_20261029T121940Z/case-diagnosis.csv`） | `20ac1bef68d15866cbf273a6b559140878d5e6e7003feef728f52e7469f03722` |
| failure-audit.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/13_failure_consistency/22_failure_consistency_20261029T121940Z/failure-audit.json`） | `5ad136f71e8ce8ad38445f3189473623c1c2b20eabf36b5cbee45a3f3d149aa9` |
| fatal-log-screen.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/13_failure_consistency/22_failure_consistency_20261029T121940Z/fatal-log-screen.json`） | `ea768329c39d5d49fe44361fefcd9f827ac18ac8853a3ad119292bb2de8d93b7` |
| analysis-sources/cloud_failure_audit.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/13_failure_consistency/22_failure_consistency_20261029T121940Z/analysis-sources/cloud_failure_audit.py`） | `8c7d4dc1b1712fa58aa5e3119ecf1ff9b9d49e06d07a71cedb49c5e0871164b4` |
| analysis-sources/cloud_failure_visuals.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/13_failure_consistency/22_failure_consistency_20261029T121940Z/analysis-sources/cloud_failure_visuals.py`） | `9fbdca7c36134cad417dbb007030ad08639d7c6eb1523e11716bcaa61546c281` |

## 阅读覆盖与下一步

本单元 56 个可读普通文件、56 种不同字节内容已完整读入并校验；逐文件清单见 审计账本（原始归档位置：`../../evidence/readthrough_20261102/file-review-ledger.jsonl.gz`），按 `HIST-032` 检索。JSON/日志/代码等做对应结构分析，重点协议、结果、失败和计量证据用于本条解释；这不声称所有依赖副本逐行人工精读，或全部视频逐帧人工审片。

下一步：本阶段记录封存至 11 月 2 日结束。后续实验另登记；如需补证，先定位本条限制对应原件，不自动重跑。
