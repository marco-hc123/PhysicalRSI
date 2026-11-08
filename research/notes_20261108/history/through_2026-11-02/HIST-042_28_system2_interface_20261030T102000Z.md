# HIST-042 · System 2 显式接口与 CPU 门禁

- 历史记录范围（北京时间）：2026-10-30T18:06:53.412139+08:00 至 2026-10-30T18:14:10.934987+08:00。
- 时间依据：original structured timestamp fields; observed record range is not necessarily physical rollout duration
- 本次回溯补录：2026-11-05 11:40，不是重跑日期。
- 类型：`system2`；原批次：`28_system2_interface_20261030T102000Z`。
- 原件现址：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/28_system2_interface_20261030T102000Z/`。历史文件中的旧执行路径保留作来源，本次导航统一指向实验室。
- 周志：[ EXP-2026W44-025 ](../../LOGS/2026-W44.md#exp-2026w44-025)。同一批次已有摘要/续接副本不新增实验计数。

## 做了什么与得到什么

在新候选进入昂贵仿真前检查场景接口。

候选被 named CPU scene contract gate 拒绝，正式迭代状态 blocked；保留原响应和成本。

## 解释边界与失败记录

判定：**Crashed**。后续重用响应不算新 API，门禁失败不填成原生零分。

续接工作区、候选响应复用和物理 dispatch 应按来源 ID/哈希分别核对。中断成本保留；没有有效最终评分的尝试标为未知。不能将各目录摘要中的累计数相加为全局新实验数。

## 复现与证据定位

本次只读取与离线复算；历史 runner、日志、协议、依赖指纹保留在下列原件。不同阶段的补丁和环境不能用一个背景 commit 替代。未明确记录的 seed、硬件或启动命令保持未知，不从今天服务器配置倒推。

| 证据原件（实验室现址） | SHA256 |
|---|---|
| protocol.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/28_system2_interface_20261030T102000Z/protocol.json`） | `eb8cd5ebbf732c8c1c4fb4457f067413b370c518c1b4982c43c89800764a0eff` |
| postrun-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/28_system2_interface_20261030T102000Z/postrun-status.json`） | `28941c2c722a5f4268f7a881929e0554cd0f38e12178ed60911f0341cf6cf39a` |
| controller-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/28_system2_interface_20261030T102000Z/controller-status.json`） | `94128e849d3a80b447c0ad19445f5f2889cb0c251c4c6e4d0242a5c41197bdb0` |
| workspace/rounds/round-000000/development-results.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/28_system2_interface_20261030T102000Z/workspace/rounds/round-000000/development-results.json`） | `32d69b81a223abad837b039d77cdbe42ca633c4f3544e0a576d221c253fd3d66` |
| workspace/rounds/round-000000/development-layouts/generated/manifest.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/28_system2_interface_20261030T102000Z/workspace/rounds/round-000000/development-layouts/generated/manifest.json`） | `539966b8750eb4c1b608a53d030b1d2fc207caa307c24be3d54fd185c8cb0773` |
| workspace/rounds/round-000000/proposals/classify_objects/cpu-contract-gate/gate-result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/28_system2_interface_20261030T102000Z/workspace/rounds/round-000000/proposals/classify_objects/cpu-contract-gate/gate-result.json`） | `1ca3192fe6f8c1db5d199fbb35907604036ffbe6ecbda2ca05a87717b0d88874` |
| workspace/rounds/round-000000/proposals/classify_objects/cpu-contract-gate/empty/result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/28_system2_interface_20261030T102000Z/workspace/rounds/round-000000/proposals/classify_objects/cpu-contract-gate/empty/result.json`） | `38e0b9de817f645c4bec37c0d4a3e58baecccb040f5718dc069a72c7385a0bed` |
| workspace/rounds/round-000000/proposals/classify_objects/cpu-contract-gate/empty/root/output/result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/28_system2_interface_20261030T102000Z/workspace/rounds/round-000000/proposals/classify_objects/cpu-contract-gate/empty/root/output/result.json`） | `9806a1af76ddd4daa5bf5d17e6e1ee08cadd71a6317b38546890afb916989220` |
| workspace/rounds/round-000000/proposals/classify_objects/cpu-contract-gate/named/root/output/result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/28_system2_interface_20261030T102000Z/workspace/rounds/round-000000/proposals/classify_objects/cpu-contract-gate/named/root/output/result.json`） | `92091bf94036714f69abaf4d9e20b6339b37b5a17ff5d182ac94de77819a4fc5` |
| workspace/rounds/round-000000/development/pi05/batch-000000/native/run/native/RoboDojo/classify_objects/physicalRSI/arx_x5/0_physicalrsi/physicalrsi-94e59c9a3509e0ef60890aceff27a70c/_result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/28_system2_interface_20261030T102000Z/workspace/rounds/round-000000/development/pi05/batch-000000/native/run/native/RoboDojo/classify_objects/physicalRSI/arx_x5/0_physicalrsi/physicalrsi-94e59c9a3509e0ef60890aceff27a70c/_result.json`） | `99b780f4e1842dfa81b413ccd2e5302e5827cc349fea4edf978e1bd847986ed3` |
| workspace/rounds/round-000000/development/pi05/batch-000001/native/run/native/RoboDojo/classify_objects/physicalRSI/arx_x5/0_physicalrsi/physicalrsi-83a7d8a74987fa7bce93f5d36fbd9d91/_result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/28_system2_interface_20261030T102000Z/workspace/rounds/round-000000/development/pi05/batch-000001/native/run/native/RoboDojo/classify_objects/physicalRSI/arx_x5/0_physicalrsi/physicalrsi-83a7d8a74987fa7bce93f5d36fbd9d91/_result.json`） | `99b780f4e1842dfa81b413ccd2e5302e5827cc349fea4edf978e1bd847986ed3` |
| workspace/rounds/round-000000/development/pi05/batch-000002/native/run/native/RoboDojo/classify_objects/physicalRSI/arx_x5/0_physicalrsi/physicalrsi-64e61462ad3a057d19ec040e5c04a05e/_result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/28_system2_interface_20261030T102000Z/workspace/rounds/round-000000/development/pi05/batch-000002/native/run/native/RoboDojo/classify_objects/physicalRSI/arx_x5/0_physicalrsi/physicalrsi-64e61462ad3a057d19ec040e5c04a05e/_result.json`） | `99b780f4e1842dfa81b413ccd2e5302e5827cc349fea4edf978e1bd847986ed3` |
| workspace/rounds/round-000000/development/pi05/batch-000003/native/run/native/RoboDojo/classify_objects/physicalRSI/arx_x5/0_physicalrsi/physicalrsi-b7dc57534cbf3ed573709bdb1b4198d9/_result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/28_system2_interface_20261030T102000Z/workspace/rounds/round-000000/development/pi05/batch-000003/native/run/native/RoboDojo/classify_objects/physicalRSI/arx_x5/0_physicalrsi/physicalrsi-b7dc57534cbf3ed573709bdb1b4198d9/_result.json`） | `99b780f4e1842dfa81b413ccd2e5302e5827cc349fea4edf978e1bd847986ed3` |
| workspace/rounds/round-000000/development/pi05/batch-000004/native/run/native/RoboDojo/classify_objects/physicalRSI/arx_x5/0_physicalrsi/physicalrsi-ffac3d4f39ddc3ee097555a9d13a775b/_result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/28_system2_interface_20261030T102000Z/workspace/rounds/round-000000/development/pi05/batch-000004/native/run/native/RoboDojo/classify_objects/physicalRSI/arx_x5/0_physicalrsi/physicalrsi-ffac3d4f39ddc3ee097555a9d13a775b/_result.json`） | `99b780f4e1842dfa81b413ccd2e5302e5827cc349fea4edf978e1bd847986ed3` |
| procedure-sources/step5_feedback.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/28_system2_interface_20261030T102000Z/procedure-sources/step5_feedback.py`） | `822132f0e6f16fe0b4d26df48dcd80bb73f99c91d77a0aa4d97227113d700ef6` |
| procedure-sources/step5_interface_audit.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/28_system2_interface_20261030T102000Z/procedure-sources/step5_interface_audit.py`） | `cf9cb20799c6895624ad9337c3ca56ce2bee2bf9dc4fc166d80263d293cd5d0a` |
| procedure-sources/step5_interface_finish.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/28_system2_interface_20261030T102000Z/procedure-sources/step5_interface_finish.py`） | `f4d20c9faefac178018bcf2805aeea1abb34405cca0ddf6fbaad67ff0ab9588f` |

### 原协议中可直接定位的字段

来源 `result/17_system2_iterations/28_system2_interface_20261030T102000Z/protocol.json`：
- `automatic_http_retries` = `0`
- `collect_interval` = `10`
- `control_dt` = `0.04`
- `model_profile.enable_thinking` = `True`
- `model_profile.model` = `qwen3.7-plus`
- `registered_utc` = `2026-10-30T10:06:53.412139+00:00`
- `task` = `classify_objects`

来源 `result/17_system2_iterations/28_system2_interface_20261030T102000Z/workspace/rounds/round-000000/development-layouts/generated/manifest.json`：
- `seed` = `6269714158801292884`


## 阅读覆盖与下一步

本单元 13178 个可读普通文件、1089 种不同字节内容已完整读入并校验；逐文件清单见 [审计账本](../../evidence/readthrough_20261102/file-review-ledger.jsonl.gz)，按 `HIST-042` 检索。JSON/日志/代码等做对应结构分析，重点协议、结果、失败和计量证据用于本条解释；这不声称所有依赖副本逐行人工精读，或全部视频逐帧人工审片。

下一步：本阶段记录封存至 11 月 2 日结束。后续实验另登记；如需补证，先定位本条限制对应原件，不自动重跑。
