# HIST-044 · System 2 最终验证首个续接失败

- 历史记录范围（北京时间）：2026-10-30T20:05:07.903762+08:00 至 2026-10-30T20:06:57.683862+08:00。
- 时间依据：original structured timestamp fields; observed record range is not necessarily physical rollout duration
- 本次回溯补录：2026-11-05 11:40，不是重跑日期。
- 类型：`system2`；原批次：`30_system2_final_validation_20261030T120500Z`。
- 原件现址：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/30_system2_final_validation_20261030T120500Z/`。历史文件中的旧执行路径保留作来源，本次导航统一指向实验室。
- 周志：[ EXP-2026W44-027 ](../../LOGS/2026-W44.md#exp-2026w44-027)。同一批次已有摘要/续接副本不新增实验计数。

## 做了什么与得到什么

用已记录候选与开发证据恢复验证。

Incumbent failed admission 导致状态 blocked；随后登记资源/提示词/依赖重绑定与外部 lineage bridge。

## 解释边界与失败记录

判定：**Crashed**。不能声称从头到尾政策哈希未变化；复用文件不等于新执行。

续接工作区、候选响应复用和物理 dispatch 应按来源 ID/哈希分别核对。中断成本保留；没有有效最终评分的尝试标为未知。不能将各目录摘要中的累计数相加为全局新实验数。

## 复现与证据定位

本次只读取与离线复算；历史 runner、日志、协议、依赖指纹保留在下列原件。不同阶段的补丁和环境不能用一个背景 commit 替代。未明确记录的 seed、硬件或启动命令保持未知，不从今天服务器配置倒推。

| 证据原件（实验室现址） | SHA256 |
|---|---|
| protocol.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/30_system2_final_validation_20261030T120500Z/protocol.json`） | `eefdbaaae7e407e6e9a16fc961460537ca471c0b6529f130a7f93974b2137624` |
| postrun-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/30_system2_final_validation_20261030T120500Z/postrun-status.json`） | `177db32888f7c38fd12eaed2fc3aa6e144dc5d64a6100b83e61d9cf4b5c2c0e2` |
| controller-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/30_system2_final_validation_20261030T120500Z/controller-status.json`） | `b4ffed28b6563738c03106923453daf34113a3e1fbb25637a6d86abc7bcc57cb` |
| offline-gate-checks/verification.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/30_system2_final_validation_20261030T120500Z/offline-gate-checks/verification.json`） | `5433c62135d23abe1c2553ecf5381e92ccce6b34e9823a8be23383b7e9b32178` |
| offline-gate-checks/actual-second-proposal/gate-result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/30_system2_final_validation_20261030T120500Z/offline-gate-checks/actual-second-proposal/gate-result.json`） | `370d87ab6b5cb37f4ee2c19c69def25b8b4dcd09b783f9a7b5b42ca612e494d2` |
| workspace/rounds/round-000000/development-results.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/30_system2_final_validation_20261030T120500Z/workspace/rounds/round-000000/development-results.json`） | `461f477b2f53e6a1438700ca3a6fc5f74388178300136d25b76408bc202b73e4` |
| offline-gate-checks/actual-second-proposal/empty/result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/30_system2_final_validation_20261030T120500Z/offline-gate-checks/actual-second-proposal/empty/result.json`） | `38e0b9de817f645c4bec37c0d4a3e58baecccb040f5718dc069a72c7385a0bed` |
| offline-gate-checks/actual-second-proposal/named-planner-rejection/result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/30_system2_final_validation_20261030T120500Z/offline-gate-checks/actual-second-proposal/named-planner-rejection/result.json`） | `38e0b9de817f645c4bec37c0d4a3e58baecccb040f5718dc069a72c7385a0bed` |
| offline-gate-checks/actual-second-proposal/underscore_and_repeated_category-planner-rejection/result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/30_system2_final_validation_20261030T120500Z/offline-gate-checks/actual-second-proposal/underscore_and_repeated_category-planner-rejection/result.json`） | `38e0b9de817f645c4bec37c0d4a3e58baecccb040f5718dc069a72c7385a0bed` |
| offline-gate-checks/invalid-quaternion/root/output/result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/30_system2_final_validation_20261030T120500Z/offline-gate-checks/invalid-quaternion/root/output/result.json`） | `fa2ebe37bc47b05b333ff57d75052b745ac2d00a3c34dac7e031029d71297d34` |
| offline-gate-checks/original-name-error/root/output/result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/30_system2_final_validation_20261030T120500Z/offline-gate-checks/original-name-error/root/output/result.json`） | `a80592faa16df07b0453068e1ad55370b4bc4d60501a74e7301172d789b0a34c` |
| offline-gate-checks/actual-second-proposal/empty/root/output/result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/30_system2_final_validation_20261030T120500Z/offline-gate-checks/actual-second-proposal/empty/root/output/result.json`） | `9806a1af76ddd4daa5bf5d17e6e1ee08cadd71a6317b38546890afb916989220` |
| offline-gate-checks/actual-second-proposal/named/root/output/result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/30_system2_final_validation_20261030T120500Z/offline-gate-checks/actual-second-proposal/named/root/output/result.json`） | `29dd4f137c2cbc4d4b59c0886e7f2ae84111bdc773f5ac6b9319392fca77a874` |
| workspace/rounds/round-000000/development-layouts/generated/manifest.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/30_system2_final_validation_20261030T120500Z/workspace/rounds/round-000000/development-layouts/generated/manifest.json`） | `22cb0623385cdc73d4187597f0168c2cfd49b69902206d34a5fe76aa8af2b024` |
| procedure-sources/step5_feedback.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/30_system2_final_validation_20261030T120500Z/procedure-sources/step5_feedback.py`） | `822132f0e6f16fe0b4d26df48dcd80bb73f99c91d77a0aa4d97227113d700ef6` |
| procedure-sources/step5_observe.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/30_system2_final_validation_20261030T120500Z/procedure-sources/step5_observe.py`） | `7622c4d526862e83b41d1a3a81abc08db95875fd1a4c2e578ccb02cea1b5c424` |
| procedure-sources/step5_scene_api_v4.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/30_system2_final_validation_20261030T120500Z/procedure-sources/step5_scene_api_v4.py`） | `09db344ca589ba093e6b2be68701eadb3e6e6cf6f5c2b81867c7627135404190` |

### 原协议中可直接定位的字段

来源 `result/17_system2_iterations/30_system2_final_validation_20261030T120500Z/protocol.json`：
- `automatic_http_retries` = `0`
- `collect_interval` = `10`
- `control_dt` = `0.04`
- `model_profile.enable_thinking` = `True`
- `model_profile.model` = `qwen3.7-plus`
- `registered_utc` = `2026-10-30T12:05:07.903762+00:00`
- `task` = `classify_objects`

来源 `result/17_system2_iterations/30_system2_final_validation_20261030T120500Z/workspace/rounds/round-000000/development-layouts/generated/manifest.json`：
- `seed` = `663050387014311974`


## 阅读覆盖与下一步

本单元 20300 个可读普通文件、1117 种不同字节内容已完整读入并校验；逐文件清单见 审计账本（原始归档位置：`../../evidence/readthrough_20261102/file-review-ledger.jsonl.gz`），按 `HIST-044` 检索。JSON/日志/代码等做对应结构分析，重点协议、结果、失败和计量证据用于本条解释；这不声称所有依赖副本逐行人工精读，或全部视频逐帧人工审片。

下一步：本阶段记录封存至 11 月 2 日结束。后续实验另登记；如需补证，先定位本条限制对应原件，不自动重跑。
