# HIST-003 · 代码、提示词与公开项目证据审计

- 历史记录范围（北京时间）：2026-10-27 至 2026-10-27。
- 时间依据：来源：原记录日期/登记目录；不把文件传输时间当实验开始时间。
- 本次回溯补录：2026-11-05 11:40，不是重跑日期。
- 类型：`audit`；原批次：`02_code_audit`。
- 原件现址：`/mnt/data/joey_tr/physical-RSI/result/02_code_audit/`。历史文件中的旧执行路径保留作来源，本次导航统一指向实验室。
- 周志性质：协议、准备、审计或管理节点，未作为新的物理实验累计。

## 做了什么与得到什么

核对两项目的决策层级，并准备真实调用的计量字段。

记录包含 12 个离线 prompt 样本、13 项选定测试、5 项 transport probe、公开项目 100 条结果重聚合及源码锚点。

## 解释边界与失败记录

判定：**部分**。公开结果属于项目 A 作者；实际 HTTP 次数和完整墙钟仍未知，不运行项目 A。

## 复现与证据定位

本次只读取与离线复算；历史 runner、日志、协议、依赖指纹保留在下列原件。不同阶段的补丁和环境不能用一个背景 commit 替代。未明确记录的 seed、硬件或启动命令保持未知，不从今天服务器配置倒推。

| 证据原件（实验室现址） | SHA256 |
|---|---|
| source_manifest.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/02_code_audit/source_manifest.json`） | `adc5cd5bd77775df841345d84d38955eac6b56db0c0cb5e178a585c95d13ad4d` |
| comparator_summary.csv（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/02_code_audit/comparator_summary.csv`） | `0bb1af786075d52deedba1aabc54402f4445a08cb757bd6b3e47b14e865c9d04` |
| comparator_summary.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/02_code_audit/comparator_summary.json`） | `e26ab857e0cd4fc4240aa76969b5937a725e22cd90f65fcc66eacea90ae16ba6` |
| prompt_audit/prompt_summary.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/02_code_audit/prompt_audit/prompt_summary.json`） | `00bd1103fa8d5e8fe178b141e6fa325da67ca47afa0a7c6a2349717ba0eaa863` |
| prompt_audit/fixture_manifest.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/02_code_audit/prompt_audit/fixture_manifest.json`） | `4832da07b8e432249bee27c8ec2d972479d9bd307896b1aa8ae2f575256964ec` |
| prompt_audit/tokenizer_cache_manifest.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/02_code_audit/prompt_audit/tokenizer_cache_manifest.json`） | `3341154c5dd31fc290ef3549e6fd03ecece03ec04c44d570f0785d49c421d765` |
| sources/comparator/release-manifest.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/02_code_audit/sources/comparator/release-manifest.json`） | `bb46985a929a227049fdb6a657e4e747406d6c65b6ce5a8f6aeb1fb0ecd2f511` |
| README.txt（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/02_code_audit/README.txt`） | `091018200a04511ae86a2d63e956dea91573ee19a72985ebc6c8f32cb2907c33` |
| 01_计量口径.txt（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/02_code_audit/01_计量口径.txt`） | `6a9666e6753f2bf5825df7c1c0d497cfefb4ce13bcbf326b02c253df9d379f18` |
| 02_下一步实验说明.txt（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/02_code_audit/02_下一步实验说明.txt`） | `85dbdcec936e72bc0a00f0a191b1a98f893a59c3fe2f14b926aad142d1ced075` |
| 00_第二阶段审计报告.txt（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/02_code_audit/00_第二阶段审计报告.txt`） | `b95262fabeb8cd3d427a1bb7722dd18e0c1c1350b5740b3ff72d4333c898408b` |
| validation.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/02_code_audit/validation.json`） | `e4bac6854c2eb1a298af43265d21cb168cea4cdd75034f33f89ee06eeee7a692` |
| evidence_index.csv（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/02_code_audit/evidence_index.csv`） | `b5ed42747a6ba574faff9baf1b19b0199af702436a1267d202125933cb3a5c92` |
| evidence_index.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/02_code_audit/evidence_index.json`） | `8d626d7c4e93e7faf06b95914f18bb463a930651a5637ba31c6699993c53e40c` |
| reproduce/audit_evidence.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/02_code_audit/reproduce/audit_evidence.py`） | `26195ea59df3e5ebad0509fd83eec285cf82f24bbcf412307c3e8b8fe29e924c` |
| reproduce/audit_prompts.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/02_code_audit/reproduce/audit_prompts.py`） | `deb65fecc9b4e460c77cc7ac212b80394fcad3522b171f40f219b8f0619865d5` |

## 阅读覆盖与下一步

本单元 106 个可读普通文件、106 种不同字节内容已完整读入并校验；逐文件清单见 审计账本（原始归档位置：`../../evidence/readthrough_20261102/file-review-ledger.jsonl.gz`），按 `HIST-003` 检索。JSON/日志/代码等做对应结构分析，重点协议、结果、失败和计量证据用于本条解释；这不声称所有依赖副本逐行人工精读，或全部视频逐帧人工审片。

下一步：本阶段记录封存至 11 月 2 日结束。后续实验另登记；如需补证，先定位本条限制对应原件，不自动重跑。
