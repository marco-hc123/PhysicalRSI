# HIST-052 · System 2 负结果机制对照

- 历史记录范围（北京时间）：2026-10-31T10:03:18.725238+08:00 至 2026-10-31T10:43:32.440313+08:00。
- 时间依据：original structured timestamp fields; observed record range is not necessarily physical rollout duration
- 本次回溯补录：2026-11-05 11:40，不是重跑日期。
- 类型：`diagnostic`；原批次：`36_system2_mechanism_20261031T010000Z_v3`。
- 原件现址：`/mnt/data/joey_tr/physical-RSI/result/21_system2_failure_mechanisms/36_system2_mechanism_20261031T010000Z_v3/`。历史文件中的旧执行路径保留作来源，本次导航统一指向实验室。
- 周志：[ EXP-2026W44-032 ](../../LOGS/2026-W44.md#exp-2026w44-032)。同一批次已有摘要/续接副本不新增实验计数。

## 做了什么与得到什么

定位入篮边界、规划、跟踪、类别和反馈问题。

9 次尝试中5正常完成均0分，1类别异常、3 tracking中止；24次离线规划；缩小篮界触发动作但仍无任务成功。

## 解释边界与失败记录

判定：**部分**。中止四例评分未知；路径可行、动作增加与抓取成功分开，手工诊断不是自主学习成果。

## 复现与证据定位

本次只读取与离线复算；历史 runner、日志、协议、依赖指纹保留在下列原件。不同阶段的补丁和环境不能用一个背景 commit 替代。未明确记录的 seed、硬件或启动命令保持未知，不从今天服务器配置倒推。

| 证据原件（实验室现址） | SHA256 |
|---|---|
| protocol.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/21_system2_failure_mechanisms/36_system2_mechanism_20261031T010000Z_v3/protocol.json`） | `b88cda5140612d3090c908fa33a52c9e75900198ce19767159d456d0d892fb67` |
| category-repair/protocol.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/21_system2_failure_mechanisms/36_system2_mechanism_20261031T010000Z_v3/category-repair/protocol.json`） | `81edb04b2612c3f92d03c51843cd8d3cc48bb00ffac1e53e2b4d4ced9a84c385` |
| planning-probes/completion.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/21_system2_failure_mechanisms/36_system2_mechanism_20261031T010000Z_v3/planning-probes/completion.json`） | `6a66f66dfa07de83251f1ff26789a01b395dd4a0b573e1d73b7a798731948e01` |
| status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/21_system2_failure_mechanisms/36_system2_mechanism_20261031T010000Z_v3/status.json`） | `cbff62e29732a071f35c0792209cb9496d17051ac2f0f675392214528f78cfca` |
| results.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/21_system2_failure_mechanisms/36_system2_mechanism_20261031T010000Z_v3/results.json`） | `009706c32239e57c690734c2daf3992ebb2e83950292e97f0a9cca75f54728dd` |
| report-zh.txt（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/21_system2_failure_mechanisms/36_system2_mechanism_20261031T010000Z_v3/report-zh.txt`） | `5396d99c0a200fbf5af12a517cc06a076fbcbee109ffc6dbf4ef4f910319c2ea` |
| write-report.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/21_system2_failure_mechanisms/36_system2_mechanism_20261031T010000Z_v3/write-report.log`） | `6b777d04d9aecc85c4add172d510b70a07b13acd954a401f46fcd6737b2096e0` |
| verification.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/21_system2_failure_mechanisms/36_system2_mechanism_20261031T010000Z_v3/verification.json`） | `6f43326b951859f0de6a01d33ab69453857f517c6e4bfdb6faea686469fefcd6` |
| control-summary.csv（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/21_system2_failure_mechanisms/36_system2_mechanism_20261031T010000Z_v3/control-summary.csv`） | `40f0b145209f22daab024a8b7e11281638b854d8faf64e5d943fb9628e7e161f` |
| bundle-manifest.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/21_system2_failure_mechanisms/36_system2_mechanism_20261031T010000Z_v3/bundle-manifest.json`） | `01e1903fd508290023a292821a28b91de269b9e8d974ea7db4627f6a36392fab` |
| video-verification.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/21_system2_failure_mechanisms/36_system2_mechanism_20261031T010000Z_v3/video-verification.json`） | `b8ca045cbadaa0259c2e80f1bfb9f2b810369b7fa69318a3c0eff15742d5a64d` |
| post-controls-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/21_system2_failure_mechanisms/36_system2_mechanism_20261031T010000Z_v3/post-controls-status.json`） | `77b740776e67d938659cbfb1115f429c0d8c43ece22bbabbc8b01757766f1a50` |
| reachability-summary.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/21_system2_failure_mechanisms/36_system2_mechanism_20261031T010000Z_v3/reachability-summary.json`） | `9c25d444dc33e491e94693039cbf9ac58974bd5526bd06648f107e496f336ccc` |
| reporting-interruption.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/21_system2_failure_mechanisms/36_system2_mechanism_20261031T010000Z_v3/reporting-interruption.json`） | `33f7ad49da8daf931d6218972dacf461ac916c7d59ec5a4c1974ed70dcce00b9` |
| procedures/diagnostic_waypoints.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/21_system2_failure_mechanisms/36_system2_mechanism_20261031T010000Z_v3/procedures/diagnostic_waypoints.py`） | `21639d3c67656d12c0ad038b26113a1cd6fc64fb8810ab061afad7bab7f59ac0` |
| procedures/system2_category_repair.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/21_system2_failure_mechanisms/36_system2_mechanism_20261031T010000Z_v3/procedures/system2_category_repair.py`） | `f160e2bb548d8b40e2add9d2d11cef53d90bccd915cea38fdac916191ccca453` |
| procedures/system2_diagnostic_close.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/21_system2_failure_mechanisms/36_system2_mechanism_20261031T010000Z_v3/procedures/system2_diagnostic_close.py`） | `610d27aa75dfb2632d8e9badb50f78ea3485e0d7e916ae4df7e1f8a2551bda68` |

## 阅读覆盖与下一步

本单元 7112 个可读普通文件、1287 种不同字节内容已完整读入并校验；逐文件清单见 [审计账本](../../evidence/readthrough_20261102/file-review-ledger.jsonl.gz)，按 `HIST-052` 检索。JSON/日志/代码等做对应结构分析，重点协议、结果、失败和计量证据用于本条解释；这不声称所有依赖副本逐行人工精读，或全部视频逐帧人工审片。

下一步：本阶段记录封存至 11 月 2 日结束。后续实验另登记；如需补证，先定位本条限制对应原件，不自动重跑。
