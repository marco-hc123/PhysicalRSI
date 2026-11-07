# HIST-049 · 冷启动与连续执行针对性计时

- 历史记录范围（北京时间）：2026-10-31T07:41:57.867462+08:00 至 2026-10-31T08:12:33.112518+08:00。
- 时间依据：original structured timestamp fields; observed record range is not necessarily physical rollout duration
- 本次回溯补录：2026-11-05 11:40，不是重跑日期。
- 类型：`timing`；原批次：`35_targeted_language_timing_20261030T234157Z`。
- 原件现址：`/mnt/data/joey_tr/physical-RSI/result/20_targeted_timing/35_targeted_language_timing_20261030T234157Z/`。历史文件中的旧执行路径保留作来源，本次导航统一指向实验室。
- 周志：[ EXP-2026W44-030 ](../../LOGS/2026-W44.md#exp-2026w44-030)。同一批次已有摘要/续接副本不新增实验计数。

## 做了什么与得到什么

在相同任务条件下核对语言 API 与回合耗时边界。

3 对正式样本加1预热，共7回合与7 HTTP；cold/continuous 平均 reset-to-result 231.92/236.71 秒，均未成功。

## 解释边界与失败记录

判定：**Y**。没有总体加速证据；两批 wrapper 工作量不同，图像也不是逐像素相同。

## 复现与证据定位

本次只读取与离线复算；历史 runner、日志、协议、依赖指纹保留在下列原件。不同阶段的补丁和环境不能用一个背景 commit 替代。未明确记录的 seed、硬件或启动命令保持未知，不从今天服务器配置倒推。

| 证据原件（实验室现址） | SHA256 |
|---|---|
| protocol.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/20_targeted_timing/35_targeted_language_timing_20261030T234157Z/protocol.json`） | `30fe35844aed3443ca6bca4811d9c30975f49f062cadb5448420068fe3c41415` |
| completion.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/20_targeted_timing/35_targeted_language_timing_20261030T234157Z/completion.json`） | `6a130fc220e41e6963dda6c1d302aa20603eb3648eab2a9783a9c846475df4ff` |
| analysis-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/20_targeted_timing/35_targeted_language_timing_20261030T234157Z/analysis-status.json`） | `de7fc6af549ed03b60c995883f36b0de0c5c34451c539a8fc7d39a141bafb174` |
| controller-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/20_targeted_timing/35_targeted_language_timing_20261030T234157Z/controller-status.json`） | `d00b9e808164913f543bfd894adf47817ae016c90457715b434c67a99793c788` |
| preparation-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/20_targeted_timing/35_targeted_language_timing_20261030T234157Z/preparation-status.json`） | `3ed50024750b9e02bd51a029564d1e7fe18d74af627155d0ed287fb64e63fcce` |
| raw-evidence-manifest.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/20_targeted_timing/35_targeted_language_timing_20261030T234157Z/raw-evidence-manifest.json`） | `e63eb6237508404e8e125053f59fe9495f468d42de2ad30995a2e23492d3f29d` |
| independent-evidence-verification.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/20_targeted_timing/35_targeted_language_timing_20261030T234157Z/independent-evidence-verification.json`） | `09b4b145b3260cc517c37601221912a2c45c21c96224481de0d78eec96b2c752` |
| language_cold_0/status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/20_targeted_timing/35_targeted_language_timing_20261030T234157Z/language_cold_0/status.json`） | `1f0586b4d2b7a51c026d9b8569e9d9a55295ab5e70a4ce38f3d601914300d4ff` |
| language_cold_1/status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/20_targeted_timing/35_targeted_language_timing_20261030T234157Z/language_cold_1/status.json`） | `4682e3d4a133bfafef3527981f95aae9b327dd93f87ebf81d378d5d2961b0698` |
| language_cold_2/status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/20_targeted_timing/35_targeted_language_timing_20261030T234157Z/language_cold_2/status.json`） | `b742d9146697dd6de2c3d49882a41dea2f080bea4f101d83e45f7b8ad5e88fec` |
| language_continuous/status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/20_targeted_timing/35_targeted_language_timing_20261030T234157Z/language_continuous/status.json`） | `e7216b1795baa0bb0172f92a9167f0fb05a4d75abcbe866087f9c2b44bb2aa4a` |
| language_cold_0/native-result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/20_targeted_timing/35_targeted_language_timing_20261030T234157Z/language_cold_0/native-result.json`） | `9bdc0fa56eff782c76625c7b3a164829f9ac3e76128cdf742fd961424ac1b740` |
| language_cold_0/policy-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/20_targeted_timing/35_targeted_language_timing_20261030T234157Z/language_cold_0/policy-status.json`） | `b6b9b2dc439bd70700660ef3b064fe2183f7684f33267ec05072a73d393a3f6b` |
| language_cold_1/native-result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/20_targeted_timing/35_targeted_language_timing_20261030T234157Z/language_cold_1/native-result.json`） | `cb192da4d03957828bd1177bb4987a4509e93784574074c643e4b011e859a08a` |
| language_cold_0/api/call-001-response.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/20_targeted_timing/35_targeted_language_timing_20261030T234157Z/language_cold_0/api/call-001-response.json`） | `b2084d7d47fc788aa3be46b8c8e5c29cdd2be20fcf972bfece25cad081bc2b95` |
| language_cold_1/api/call-001-response.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/20_targeted_timing/35_targeted_language_timing_20261030T234157Z/language_cold_1/api/call-001-response.json`） | `863b090d52154e6494cfc010d38f387c588e477c66060511c729c42682e0116e` |
| analysis-sources/cloud_closing_contract.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/20_targeted_timing/35_targeted_language_timing_20261030T234157Z/analysis-sources/cloud_closing_contract.py`） | `f88f41688d8d395476bd1a617ee121b4dc61b7c68743e8b34f901aeef28c6c16` |
| analysis-sources/cloud_closing_native.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/20_targeted_timing/35_targeted_language_timing_20261030T234157Z/analysis-sources/cloud_closing_native.py`） | `cf8245aa7e33f66da3b783e432a27db2020772210234038ddebd67a50cba50e3` |
| analysis-sources/cloud_closing_policy.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/20_targeted_timing/35_targeted_language_timing_20261030T234157Z/analysis-sources/cloud_closing_policy.py`） | `1d2ffc9515050cc105a0449f2224430e44ab8ff8d03e2f9c55e44ebb866811b8` |

### 原协议中可直接定位的字段

来源 `result/20_targeted_timing/35_targeted_language_timing_20261030T234157Z/protocol.json`：
- `registered_utc` = `2026-10-30T23:41:57.867462+00:00`
- `model` = `qwen3.7-plus`


## 阅读覆盖与下一步

本单元 1617 个可读普通文件、1482 种不同字节内容已完整读入并校验；逐文件清单见 审计账本（原始归档位置：`../../evidence/readthrough_20261102/file-review-ledger.jsonl.gz`），按 `HIST-049` 检索。JSON/日志/代码等做对应结构分析，重点协议、结果、失败和计量证据用于本条解释；这不声称所有依赖副本逐行人工精读，或全部视频逐帧人工审片。

下一步：本阶段记录封存至 11 月 2 日结束。后续实验另登记；如需补证，先定位本条限制对应原件，不自动重跑。
