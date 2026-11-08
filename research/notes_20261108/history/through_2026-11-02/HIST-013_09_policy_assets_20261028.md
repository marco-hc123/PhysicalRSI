# HIST-013 · 策略资产下载暂停记录

- 历史记录范围（北京时间）：2026-10-28T21:25:04.494261+08:00 至 2026-10-28T21:25:04.494261+08:00。
- 时间依据：original structured timestamp fields; observed record range is not necessarily physical rollout duration
- 本次回溯补录：2026-11-05 11:40，不是重跑日期。
- 类型：`preparation`；原批次：`09_policy_assets_20261028`。
- 原件现址：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/09_policy_assets_20261028/`。历史文件中的旧执行路径保留作来源，本次导航统一指向实验室。
- 周志性质：协议、准备、审计或管理节点，未作为新的物理实验累计。

## 做了什么与得到什么

保留用户暂停时的真实进度。

状态 paused_by_user，记录部分下载 2623816 字节；后续由独立下载批次接续。

## 解释边界与失败记录

判定：**部分**。暂停不是模型任务失败，部分字节不是已完成权重。

## 复现与证据定位

本次只读取与离线复算；历史 runner、日志、协议、依赖指纹保留在下列原件。不同阶段的补丁和环境不能用一个背景 commit 替代。未明确记录的 seed、硬件或启动命令保持未知，不从今天服务器配置倒推。

| 证据原件（实验室现址） | SHA256 |
|---|---|
| status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/09_policy_assets_20261028/status.json`） | `0d1af464a855c457b7c9d30d7f41d1a22899b5dd0fff60dd80489a74d62c9905` |
| fetch_policy_assets.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/09_policy_assets_20261028/fetch_policy_assets.py`） | `e1c1a0b4860973d9793496e6b5cda1208a2df5f4899ddc26ceba888793de563e` |
| logs/pi05-weights.tar.part000.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/09_policy_assets_20261028/logs/pi05-weights.tar.part000.log`） | `d1d08f727201d761896b836337a2bceedf4cb3babcca073bbdbb44d9ae421f8d` |
| logs/pi05-weights.tar.part001.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/09_policy_assets_20261028/logs/pi05-weights.tar.part001.log`） | `d1d08f727201d761896b836337a2bceedf4cb3babcca073bbdbb44d9ae421f8d` |
| logs/pi05-weights.tar.part002.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/09_policy_assets_20261028/logs/pi05-weights.tar.part002.log`） | `d1d08f727201d761896b836337a2bceedf4cb3babcca073bbdbb44d9ae421f8d` |
| logs/pi05-weights.tar.part003.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/09_policy_assets_20261028/logs/pi05-weights.tar.part003.log`） | `d1d08f727201d761896b836337a2bceedf4cb3babcca073bbdbb44d9ae421f8d` |

## 阅读覆盖与下一步

本单元 7 个可读普通文件、4 种不同字节内容已完整读入并校验；逐文件清单见 [审计账本](../../evidence/readthrough_20261102/file-review-ledger.jsonl.gz)，按 `HIST-013` 检索。JSON/日志/代码等做对应结构分析，重点协议、结果、失败和计量证据用于本条解释；这不声称所有依赖副本逐行人工精读，或全部视频逐帧人工审片。

下一步：本阶段记录封存至 11 月 2 日结束。后续实验另登记；如需补证，先定位本条限制对应原件，不自动重跑。
