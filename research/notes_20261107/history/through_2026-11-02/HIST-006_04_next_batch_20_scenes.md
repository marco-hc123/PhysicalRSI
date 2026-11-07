# HIST-006 · 20 个合成场景后续批次准备

- 历史记录范围（北京时间）：2026-10-27 至 2026-10-27。
- 时间依据：来源：原记录日期/登记目录；不把文件传输时间当实验开始时间。
- 本次回溯补录：2026-11-05 11:40，不是重跑日期。
- 类型：`preparation`；原批次：`04_next_batch_20_scenes`。
- 原件现址：`/mnt/data/joey_tr/physical-RSI/result/04_next_batch_20_scenes/`。历史文件中的旧执行路径保留作来源，本次导航统一指向实验室。
- 周志性质：协议、准备、审计或管理节点，未作为新的物理实验累计。

## 做了什么与得到什么

冻结更宽的输入覆盖、调用顺序和预设操作标签。

20 图、10 family、40 条唯一请求、每条件三重复，计划 120 次；本准备目录未发起请求。

## 解释边界与失败记录

判定：**N**。准备与下一目录的实际执行分开登记，不能把计划数再加为新调用。

## 复现与证据定位

本次只读取与离线复算；历史 runner、日志、协议、依赖指纹保留在下列原件。不同阶段的补丁和环境不能用一个背景 commit 替代。未明确记录的 seed、硬件或启动命令保持未知，不从今天服务器配置倒推。

| 证据原件（实验室现址） | SHA256 |
|---|---|
| protocol.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/04_next_batch_20_scenes/protocol.json`） | `81ee864938971e3f99ab038e5b8dd5903d204692f7a17bfa1b7c42ce23c6496d` |
| file_manifest.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/04_next_batch_20_scenes/file_manifest.json`） | `3a878715809f5d6b98c8b5e042fb1edf4d2fd181589a8cff81510fb1f3a13aae` |
| request_manifest.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/04_next_batch_20_scenes/request_manifest.json`） | `641523580abde97bf5925948ba57651be370638998322f1efdceaa9c6ef6b692` |
| previous_results_preservation.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/04_next_batch_20_scenes/previous_results_preservation.json`） | `d84c09bc999319f492665a1cf91e48052aedf54c7b543e8106a28ce874fa7a53` |
| basis/stage1_report.txt（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/04_next_batch_20_scenes/basis/stage1_report.txt`） | `a1aa4c476394afde378fef0c4cf1351f69c2446afe31e6c8113b93658d604bf3` |
| basis/stage1_summary.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/04_next_batch_20_scenes/basis/stage1_summary.json`） | `6f81601b50a0399dc09bfa2a99d3943f74193d74ed2b4e26993831ae33cbcc75` |
| basis/stage1_file_manifest.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/04_next_batch_20_scenes/basis/stage1_file_manifest.json`） | `b28defca75b3beb3c831f9cb566896098a12cdd95fcf720912a183e44632f29c` |
| README.txt（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/04_next_batch_20_scenes/README.txt`） | `5cef3061abaca57373fad3b7be0828ce5ab15fab77fe64fe5a43b6cc5a76c49e` |
| scenes.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/04_next_batch_20_scenes/scenes.json`） | `b2c758a17faee627202d82370d680f4e25aec20f3fd846c43b0124fd7a00383c` |
| schedule.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/04_next_batch_20_scenes/schedule.json`） | `594c6ebc0858f835faac0dd3229ca2f7eb883974352a47b923c2959c4695198e` |
| 00_下一批实验方案.txt（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/04_next_batch_20_scenes/00_下一批实验方案.txt`） | `eda0a8809e52847d931a1a8f9401a478950e086699cfd3970f0c3dfae1bbcf27` |
| process_log.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/04_next_batch_20_scenes/process_log.json`） | `5f556d1b9ba8b2eb326f78a6ec2b26ee273256b01352effcec45b2f7f2f321df` |
| sync_receipt.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/04_next_batch_20_scenes/sync_receipt.json`） | `cce28f49eea4d5090e319a404cf5c4c3fd199e28d83e207369b8760226a5df7e` |
| visual_review.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/04_next_batch_20_scenes/visual_review.json`） | `2f8ddab7681a66432175a53a62ad3411ff87974223f0bb1397e1d65fd3996d93` |
| tools/prepare_inputs.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/04_next_batch_20_scenes/tools/prepare_inputs.py`） | `e1657330b0339f5dd4c47d4bd1669138b67df908cf0096f02e3a3af0b8d0d99b` |
| tools/validate_preparation.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/04_next_batch_20_scenes/tools/validate_preparation.py`） | `2710eac29f7cbe15db6d9373061e4985304b3122e84263cf16c89fd63a0d0589` |

### 原协议中可直接定位的字段

来源 `result/04_next_batch_20_scenes/protocol.json`：
- `created_utc` = `2026-10-27T13:14:26.604330+00:00`
- `source_commit` = `90b322a3a362aad14125f36d8ed080ca31daaea6`
- `model` = `qwen3-vl-plus`
- `sampling.enable_thinking` = `False`


## 阅读覆盖与下一步

本单元 95 个可读普通文件、95 种不同字节内容已完整读入并校验；逐文件清单见 审计账本（原始归档位置：`../../evidence/readthrough_20261102/file-review-ledger.jsonl.gz`），按 `HIST-006` 检索。JSON/日志/代码等做对应结构分析，重点协议、结果、失败和计量证据用于本条解释；这不声称所有依赖副本逐行人工精读，或全部视频逐帧人工审片。

下一步：本阶段记录封存至 11 月 2 日结束。后续实验另登记；如需补证，先定位本条限制对应原件，不自动重跑。
