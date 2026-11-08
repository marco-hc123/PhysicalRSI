# HIST-047 · 扩展任务首个启动中断

- 历史记录范围（北京时间）：2026-10-30T23:09:38.369288+08:00 至 2026-10-30T23:09:38.369288+08:00。
- 时间依据：original structured timestamp fields; observed record range is not necessarily physical rollout duration
- 本次回溯补录：2026-11-05 11:40，不是重跑日期。
- 类型：`native_attempt`；原批次：`33_limited_completion_20261030T150938Z`。
- 原件现址：`/mnt/data/joey_tr/physical-RSI/result/19_extended_tasks_final_acceptance/33_limited_completion_20261030T150938Z/`。历史文件中的旧执行路径保留作来源，本次导航统一指向实验室。
- 周志：[ EXP-2026W44-029 ](../../LOGS/2026-W44.md#exp-2026w44-029)。同一批次已有摘要/续接副本不新增实验计数。

## 做了什么与得到什么

开始注册的新任务 smoke 与最终验收流程。

smoke_stack_bowls 命令退出非零，控制器 needs_review；后续由独立 34 批次接续。

## 解释边界与失败记录

判定：**Crashed**。本目录的计划项不能当作完成结果；失败启动不填正常任务评分。

## 复现与证据定位

本次只读取与离线复算；历史 runner、日志、协议、依赖指纹保留在下列原件。不同阶段的补丁和环境不能用一个背景 commit 替代。未明确记录的 seed、硬件或启动命令保持未知，不从今天服务器配置倒推。

| 证据原件（实验室现址） | SHA256 |
|---|---|
| protocol.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/19_extended_tasks_final_acceptance/33_limited_completion_20261030T150938Z/protocol.json`） | `90e5450a91c351791dde84eef4a5cf1b71163bc7916a666f9f21f3f91ba78f27` |
| analysis-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/19_extended_tasks_final_acceptance/33_limited_completion_20261030T150938Z/analysis-status.json`） | `69564fa0d5274de0b7554ffc7d4827bec995aa3cb5576581c1f83a42ff35dbf9` |
| preparation-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/19_extended_tasks_final_acceptance/33_limited_completion_20261030T150938Z/preparation-status.json`） | `2fc0014f844646898e320244460d9d647f45a9f15b5742e576f1a971d2120468` |
| smoke-controller-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/19_extended_tasks_final_acceptance/33_limited_completion_20261030T150938Z/smoke-controller-status.json`） | `e18a9884cd7dbdc09eb6a5299135818d7298eb9ed1ccb1c58f16d501748f77dd` |
| task-assets/status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/19_extended_tasks_final_acceptance/33_limited_completion_20261030T150938Z/task-assets/status.json`） | `6a9cdf8d78d21650d21b8037c17eaf492c0db1dfec2240181ac8887dc91c5dee` |
| task-assets/manifest.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/19_extended_tasks_final_acceptance/33_limited_completion_20261030T150938Z/task-assets/manifest.json`） | `a06e36c3a9c3bb45725300d428007f8d719450f9817ed794910dddc24f77d811` |
| smoke_stack_bowls/status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/19_extended_tasks_final_acceptance/33_limited_completion_20261030T150938Z/smoke_stack_bowls/status.json`） | `0e00c721e2d9dd917f36d4eaf13fb2ef3f37c29d5f3bee76f25541d098a1aa07` |
| assets.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/19_extended_tasks_final_acceptance/33_limited_completion_20261030T150938Z/assets.log`） | `3a2d8c26e4c810317df001cce9626034e8d5ea2a1475dadb7937a8d983b0f6a7` |
| smoke-controller.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/19_extended_tasks_final_acceptance/33_limited_completion_20261030T150938Z/smoke-controller.log`） | `c07e62876a206770d2640234a14452337d71a8d4558853ae924a1b1b7a5eb699` |
| previous-master-plan.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/19_extended_tasks_final_acceptance/33_limited_completion_20261030T150938Z/previous-master-plan.json`） | `ca726243378b7c6636920eaef5ddae2cc138fd78abeacac17de903602bc78dad` |
| procedure-registration.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/19_extended_tasks_final_acceptance/33_limited_completion_20261030T150938Z/procedure-registration.json`） | `cab30260f67114e24094ad990e26d6daa8aa0a71a0ab7ae0bc6a5589b054ee7e` |
| smoke_stack_bowls.launch.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/19_extended_tasks_final_acceptance/33_limited_completion_20261030T150938Z/smoke_stack_bowls.launch.log`） | `37e494f460834f0a3ef755a8c22779c7af6ca20142be7fc42161b61b334c22ca` |
| analysis-sources/step7_assets.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/19_extended_tasks_final_acceptance/33_limited_completion_20261030T150938Z/analysis-sources/step7_assets.py`） | `de42e46a2e9222897f89de6cd10ee07b9602a0a9acf1dce3762110fe41ba67fa` |
| analysis-sources/step7_register.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/19_extended_tasks_final_acceptance/33_limited_completion_20261030T150938Z/analysis-sources/step7_register.py`） | `2676a1581d3f20e19a19f5434be01e1d8cf776b140700a6e3d5fa873cc4bce9d` |
| analysis-sources/cloud_comparison_native.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/19_extended_tasks_final_acceptance/33_limited_completion_20261030T150938Z/analysis-sources/cloud_comparison_native.py`） | `8eed3ac4ff2a73ca1ead2b913a37cea61f846fbafe8ac8c5cdda084e5801c9c1` |
| analysis-sources/cloud_comparison_policy.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/19_extended_tasks_final_acceptance/33_limited_completion_20261030T150938Z/analysis-sources/cloud_comparison_policy.py`） | `23bfd4f0fa23089b18fd7abf4fb40ad938f4a2c56cab0d7a08b83b29540791fe` |
| analysis-sources/cloud_comparison_run.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/19_extended_tasks_final_acceptance/33_limited_completion_20261030T150938Z/analysis-sources/cloud_comparison_run.py`） | `3bf21e56e2e07e964906d68681305535c021b11310d9ffe7937bc797d22bafe2` |

### 原协议中可直接定位的字段

来源 `result/19_extended_tasks_final_acceptance/33_limited_completion_20261030T150938Z/protocol.json`：
- `registered_utc` = `2026-10-30T15:09:38.369288+00:00`


## 阅读覆盖与下一步

本单元 19 个可读普通文件、19 种不同字节内容已完整读入并校验；逐文件清单见 [审计账本](../../evidence/readthrough_20261102/file-review-ledger.jsonl.gz)，按 `HIST-047` 检索。JSON/日志/代码等做对应结构分析，重点协议、结果、失败和计量证据用于本条解释；这不声称所有依赖副本逐行人工精读，或全部视频逐帧人工审片。

下一步：本阶段记录封存至 11 月 2 日结束。后续实验另登记；如需补证，先定位本条限制对应原件，不自动重跑。
