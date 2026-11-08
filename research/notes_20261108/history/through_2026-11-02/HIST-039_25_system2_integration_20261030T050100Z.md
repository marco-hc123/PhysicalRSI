# HIST-039 · System 2 原生集成

- 历史记录范围（北京时间）：2026-10-30T12:54:51.601192+08:00 至 2026-10-30T14:18:09.259722+08:00。
- 时间依据：original structured timestamp fields; observed record range is not necessarily physical rollout duration
- 本次回溯补录：2026-11-05 11:40，不是重跑日期。
- 类型：`system2`；原批次：`25_system2_integration_20261030T050100Z`。
- 原件现址：`/mnt/data/joey_tr/physical-RSI/result/16_system2_integration/25_system2_integration_20261030T050100Z/`。历史文件中的旧执行路径保留作来源，本次导航统一指向实验室。
- 周志：[ EXP-2026W44-022 ](../../LOGS/2026-W44.md#exp-2026w44-022)。同一批次已有摘要/续接副本不新增实验计数。

## 做了什么与得到什么

打通提案、隔离执行、开发/验证与选择。

集成提案 323599 Token；2 个开发与2个父/候选验证回合形成集成证据，保留父策略。

## 解释边界与失败记录

判定：**部分**。多次工程修复不等于多个被采用的新算法；一个历史辅助脚本存在语法错误，应保留为复现性限制。

原 `run-boundary-probes.py` 第 6 行多行字符串未闭合，静态解析失败；本次保留原件。另有正/负独立 probe 源码及 `isolation-boundary-verification.json`（passed=true），只证明相应软件隔离结果，不能用该回执宣称上述有语法问题的包装脚本可直接重跑。

## 复现与证据定位

本次只读取与离线复算；历史 runner、日志、协议、依赖指纹保留在下列原件。不同阶段的补丁和环境不能用一个背景 commit 替代。未明确记录的 seed、硬件或启动命令保持未知，不从今天服务器配置倒推。

| 证据原件（实验室现址） | SHA256 |
|---|---|
| protocol.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/16_system2_integration/25_system2_integration_20261030T050100Z/protocol.json`） | `c3712b735d71ed934c83e3772f0ca32930fd8e29631eaf1da5ba6a865599308d` |
| attempt-05-planning-contract/workspace/rounds/round-000000/selection.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/16_system2_integration/25_system2_integration_20261030T050100Z/attempt-05-planning-contract/workspace/rounds/round-000000/selection.json`） | `349b1e6a86eecd18d69c4f2e3fbd5771c1d1b439ba5b01460d2cc3cb1c59fb5a` |
| step4-results.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/16_system2_integration/25_system2_integration_20261030T050100Z/step4-results.json`） | `a90658bd7db3346d08049d1e3f81c373f6e4aca4702c00e5d68edc5bbeae7ea7` |
| controller-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/16_system2_integration/25_system2_integration_20261030T050100Z/controller-status.json`） | `fe4851296d352cab4012f2525cca586dfc12c7619ecf8ce20b46fbb5818db776` |
| source-verification.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/16_system2_integration/25_system2_integration_20261030T050100Z/source-verification.json`） | `c5dd2dfd9024b8d57ee5636f7f68fe66f19c8b13056bfc8c688b31ca898ffaa9` |
| initialization-result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/16_system2_integration/25_system2_integration_20261030T050100Z/initialization-result.json`） | `4c8ce8252bb078ac807125c5d6f1d020a38997560ef1477eeec6a58650a46669` |
| isolation-boundary-verification.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/16_system2_integration/25_system2_integration_20261030T050100Z/isolation-boundary-verification.json`） | `2f40e808206576dd6ce4e4e638869c768d2fec045856f4d892fe18dec3128af0` |
| pre-final-original-source-verification.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/16_system2_integration/25_system2_integration_20261030T050100Z/pre-final-original-source-verification.json`） | `955ed64e1f440395810c976975a569c803b710e3f83137704550c5ae2b8c6014` |
| final-audit/verification.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/16_system2_integration/25_system2_integration_20261030T050100Z/final-audit/verification.json`） | `265da8a1b8656c2070824bd75a7c7a4b5b9936852b42ecc20928308061b54d96` |
| isolation-negative/result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/16_system2_integration/25_system2_integration_20261030T050100Z/isolation-negative/result.json`） | `75db039a15f48c5f7148823762cedaaf863a2743faa66d1f0dd6e6adddc0fd67` |
| isolation-positive/result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/16_system2_integration/25_system2_integration_20261030T050100Z/isolation-positive/result.json`） | `7d41e01da1a221d8a16c761195396e8f05bdf11b07d12594cdf89b13335312af` |
| isolation-runtime/manifest.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/16_system2_integration/25_system2_integration_20261030T050100Z/isolation-runtime/manifest.json`） | `5937b26c5e9dd79110b993b8972f3b1a5aaa9c23735c303e814b0b195b2801b6` |
| attempt-02/controller-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/16_system2_integration/25_system2_integration_20261030T050100Z/attempt-02/controller-status.json`） | `f9dc65dd859617b51a12497552b27aed80a6a39e376579cae893fc73e8f7a545` |
| attempt-03/controller-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/16_system2_integration/25_system2_integration_20261030T050100Z/attempt-03/controller-status.json`） | `9ce3e4e806cd99abf8a0a5fe16ebc107f1a38fc84eac7574bb8e73938f66785b` |
| controller-attempt-01.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/16_system2_integration/25_system2_integration_20261030T050100Z/controller-attempt-01.py`） | `976bdb14e88343bc924d269da604b8cc76d9a8e864260d8de0be243c6e228c2f` |
| integration-sources/isolated-sim-entry-validation-v2.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/16_system2_integration/25_system2_integration_20261030T050100Z/integration-sources/isolated-sim-entry-validation-v2.py`） | `b7c37f8dc29cdb6a0bdcf11a4895d1a7bf9c0c99fc210912987122b069aba3c9` |
| integration-sources/isolated-sim-entry-validation-v3.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/16_system2_integration/25_system2_integration_20261030T050100Z/integration-sources/isolated-sim-entry-validation-v3.py`） | `0613c9d713402361536dcd8e27d3aa54b61b21e0b19d9db1aa8ce12d83c3dab8` |

### 原协议中可直接定位的字段

来源 `result/16_system2_integration/25_system2_integration_20261030T050100Z/protocol.json`：
- `registered_utc` = `2026-10-30T04:54:51.601192+00:00`
- `task` = `classify_objects`


## 阅读覆盖与下一步

本单元 11864 个可读普通文件、1728 种不同字节内容已完整读入并校验；逐文件清单见 [审计账本](../../evidence/readthrough_20261102/file-review-ledger.jsonl.gz)，按 `HIST-039` 检索。JSON/日志/代码等做对应结构分析，重点协议、结果、失败和计量证据用于本条解释；这不声称所有依赖副本逐行人工精读，或全部视频逐帧人工审片。

下一步：本阶段记录封存至 11 月 2 日结束。后续实验另登记；如需补证，先定位本条限制对应原件，不自动重跑。
