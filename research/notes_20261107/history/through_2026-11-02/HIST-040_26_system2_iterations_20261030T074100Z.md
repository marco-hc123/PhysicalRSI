# HIST-040 · System 2 首轮场景契约中断

- 历史记录范围（北京时间）：2026-10-30T15:31:58.948776+08:00 至 2026-10-30T16:58:13.700649+08:00。
- 时间依据：original structured timestamp fields; observed record range is not necessarily physical rollout duration
- 本次回溯补录：2026-11-05 11:40，不是重跑日期。
- 类型：`system2`；原批次：`26_system2_iterations_20261030T074100Z`。
- 原件现址：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/26_system2_iterations_20261030T074100Z/`。历史文件中的旧执行路径保留作来源，本次导航统一指向实验室。
- 周志：[ EXP-2026W44-023 ](../../LOGS/2026-W44.md#exp-2026w44-023)。同一批次已有摘要/续接副本不新增实验计数。

## 做了什么与得到什么

检查生成候选能否通过原生验证。

提案 31207 Token；10 开发加 5 父验证正常完成，候选将 basket_1 解析成整数而中止，未提交 round。

## 解释边界与失败记录

判定：**Crashed**。中止尝试没有有效最终评分；已有失败成本不能删除，不能写成正式迭代成功。

续接工作区、候选响应复用和物理 dispatch 应按来源 ID/哈希分别核对。中断成本保留；没有有效最终评分的尝试标为未知。不能将各目录摘要中的累计数相加为全局新实验数。

## 复现与证据定位

本次只读取与离线复算；历史 runner、日志、协议、依赖指纹保留在下列原件。不同阶段的补丁和环境不能用一个背景 commit 替代。未明确记录的 seed、硬件或启动命令保持未知，不从今天服务器配置倒推。

| 证据原件（实验室现址） | SHA256 |
|---|---|
| protocol.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/26_system2_iterations_20261030T074100Z/protocol.json`） | `e34660e5d2c9d1e857245bbae406e1aaeef2a3ffbcd6743f5bf8183f54d94c1b` |
| postrun-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/26_system2_iterations_20261030T074100Z/postrun-status.json`） | `52f27f0e5b7bfff76f8870496235caf04aeda04eba0bc89f2a4c2da9f56dd1cf` |
| controller-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/26_system2_iterations_20261030T074100Z/controller-status.json`） | `f2c0aef18ef16f9af910562304a8ce90f33c9d9c97927c6f09a7705cac044bb5` |
| step5-stopped-results.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/26_system2_iterations_20261030T074100Z/step5-stopped-results.json`） | `0edba703ad27d98509075c964e7d8af929f8dd4158c70f35df3404b7e3699bcd` |
| parent-state-verification.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/26_system2_iterations_20261030T074100Z/parent-state-verification.json`） | `ce5a0b568796d0ae6a6e8fc11206f20b206f2296d5703673098061fafd4a85a4` |
| interruption-audit/verification.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/26_system2_iterations_20261030T074100Z/interruption-audit/verification.json`） | `2e5a480fb13f9751e5ab6dfb0a6b2c86fe6d03be3823f7e22a98ee1228437977` |
| workspace/rounds/round-000000/development-results.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/26_system2_iterations_20261030T074100Z/workspace/rounds/round-000000/development-results.json`） | `5c5794f2edfb2a116b3ed5b5be572f97c6e872b122ee9afdd67fcae0e62fb487` |
| workspace/rounds/round-000000/validation-layouts/generated/manifest.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/26_system2_iterations_20261030T074100Z/workspace/rounds/round-000000/validation-layouts/generated/manifest.json`） | `11c5f690086176163218a5a6496bd9fee8b7f3d1fbbd02feff4dce580e142435` |
| workspace/rounds/round-000000/development-layouts/generated/manifest.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/26_system2_iterations_20261030T074100Z/workspace/rounds/round-000000/development-layouts/generated/manifest.json`） | `539966b8750eb4c1b608a53d030b1d2fc207caa307c24be3d54fd185c8cb0773` |
| workspace/rounds/round-000000/evaluation/candidate_round-000000/batch-000000/model/expert/5bdeb7402c164492b695627f29e3a58a/0/policy/root/output/result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/26_system2_iterations_20261030T074100Z/workspace/rounds/round-000000/evaluation/candidate_round-000000/batch-000000/model/expert/5bdeb7402c164492b695627f29e3a58a/0/policy/root/output/result.json`） | `a80592faa16df07b0453068e1ad55370b4bc4d60501a74e7301172d789b0a34c` |
| workspace/rounds/round-000000/development/pi05/batch-000000/native/run/native/RoboDojo/classify_objects/physicalRSI/arx_x5/0_physicalrsi/physicalrsi-94e59c9a3509e0ef60890aceff27a70c/_result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/26_system2_iterations_20261030T074100Z/workspace/rounds/round-000000/development/pi05/batch-000000/native/run/native/RoboDojo/classify_objects/physicalRSI/arx_x5/0_physicalrsi/physicalrsi-94e59c9a3509e0ef60890aceff27a70c/_result.json`） | `99b780f4e1842dfa81b413ccd2e5302e5827cc349fea4edf978e1bd847986ed3` |
| workspace/rounds/round-000000/development/pi05/batch-000001/native/run/native/RoboDojo/classify_objects/physicalRSI/arx_x5/0_physicalrsi/physicalrsi-83a7d8a74987fa7bce93f5d36fbd9d91/_result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/26_system2_iterations_20261030T074100Z/workspace/rounds/round-000000/development/pi05/batch-000001/native/run/native/RoboDojo/classify_objects/physicalRSI/arx_x5/0_physicalrsi/physicalrsi-83a7d8a74987fa7bce93f5d36fbd9d91/_result.json`） | `99b780f4e1842dfa81b413ccd2e5302e5827cc349fea4edf978e1bd847986ed3` |
| workspace/rounds/round-000000/development/pi05/batch-000002/native/run/native/RoboDojo/classify_objects/physicalRSI/arx_x5/0_physicalrsi/physicalrsi-64e61462ad3a057d19ec040e5c04a05e/_result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/26_system2_iterations_20261030T074100Z/workspace/rounds/round-000000/development/pi05/batch-000002/native/run/native/RoboDojo/classify_objects/physicalRSI/arx_x5/0_physicalrsi/physicalrsi-64e61462ad3a057d19ec040e5c04a05e/_result.json`） | `99b780f4e1842dfa81b413ccd2e5302e5827cc349fea4edf978e1bd847986ed3` |
| workspace/rounds/round-000000/development/pi05/batch-000003/native/run/native/RoboDojo/classify_objects/physicalRSI/arx_x5/0_physicalrsi/physicalrsi-b7dc57534cbf3ed573709bdb1b4198d9/_result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/26_system2_iterations_20261030T074100Z/workspace/rounds/round-000000/development/pi05/batch-000003/native/run/native/RoboDojo/classify_objects/physicalRSI/arx_x5/0_physicalrsi/physicalrsi-b7dc57534cbf3ed573709bdb1b4198d9/_result.json`） | `99b780f4e1842dfa81b413ccd2e5302e5827cc349fea4edf978e1bd847986ed3` |
| postprocessing-sources/step5_interruption_audit.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/26_system2_iterations_20261030T074100Z/postprocessing-sources/step5_interruption_audit.py`） | `11d92126452bced76133eac9cefec8139adfa9aa30c8a910cbb2c15968259eae` |
| procedure-sources/step5_audit.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/26_system2_iterations_20261030T074100Z/procedure-sources/step5_audit.py`） | `51fb37e36917e5a8b626915c40680fc5ba359fee8dfb6551e1052b6fd7531e61` |
| procedure-sources/step5_feedback.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/26_system2_iterations_20261030T074100Z/procedure-sources/step5_feedback.py`） | `822132f0e6f16fe0b4d26df48dcd80bb73f99c91d77a0aa4d97227113d700ef6` |

### 原协议中可直接定位的字段

来源 `result/17_system2_iterations/26_system2_iterations_20261030T074100Z/protocol.json`：
- `automatic_http_retries` = `0`
- `collect_interval` = `10`
- `control_dt` = `0.04`
- `model_profile.enable_thinking` = `True`
- `model_profile.model` = `qwen3.7-plus`
- `registered_utc` = `2026-10-30T07:31:58.948776+00:00`
- `task` = `classify_objects`

来源 `result/17_system2_iterations/26_system2_iterations_20261030T074100Z/workspace/rounds/round-000000/validation-layouts/generated/manifest.json`：
- `seed` = `8507145529354306223`

来源 `result/17_system2_iterations/26_system2_iterations_20261030T074100Z/workspace/rounds/round-000000/development-layouts/generated/manifest.json`：
- `seed` = `6269714158801292884`


## 阅读覆盖与下一步

本单元 18410 个可读普通文件、1333 种不同字节内容已完整读入并校验；逐文件清单见 审计账本（原始归档位置：`../../evidence/readthrough_20261102/file-review-ledger.jsonl.gz`），按 `HIST-040` 检索。JSON/日志/代码等做对应结构分析，重点协议、结果、失败和计量证据用于本条解释；这不声称所有依赖副本逐行人工精读，或全部视频逐帧人工审片。

下一步：本阶段记录封存至 11 月 2 日结束。后续实验另登记；如需补证，先定位本条限制对应原件，不自动重跑。
