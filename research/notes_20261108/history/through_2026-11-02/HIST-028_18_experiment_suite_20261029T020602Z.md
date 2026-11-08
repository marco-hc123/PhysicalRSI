# HIST-028 · general_pickup 多路线开发比较

- 历史记录范围（北京时间）：2026-10-29T11:08:28.293858+08:00 至 2026-10-29T12:24:46.587720+08:00。
- 时间依据：original structured timestamp fields; observed record range is not necessarily physical rollout duration
- 本次回溯补录：2026-11-05 11:40，不是重跑日期。
- 类型：`native_comparison`；原批次：`18_experiment_suite_20261029T020602Z`。
- 原件现址：`/mnt/data/joey_tr/physical-RSI/result/10_general_pickup_comparison/18_experiment_suite_20261029T020602Z/`。历史文件中的旧执行路径保留作来源，本次导航统一指向实验室。
- 周志：[ EXP-2026W44-016 ](../../LOGS/2026-W44.md#exp-2026w44-016)。同一批次已有摘要/续接副本不新增实验计数。

## 做了什么与得到什么

比较固定策略、代码技能与 Agent 配置的实际表现。

59 个逻辑案例中 58 个 native、1 个规划失败，另有 6 API-only；新布局 pi05 0/10、sparse 0/10、code 4/10、nonthinking Agent 0/10、thinking Agent 7/10。

## 解释边界与失败记录

判定：**部分**。布局 0 的三次重复另列；开发队列和补测不能当成统一盲测榜单，26 次 API 已包含 API-only。

## 复现与证据定位

本次只读取与离线复算；历史 runner、日志、协议、依赖指纹保留在下列原件。不同阶段的补丁和环境不能用一个背景 commit 替代。未明确记录的 seed、硬件或启动命令保持未知，不从今天服务器配置倒推。

| 证据原件（实验室现址） | SHA256 |
|---|---|
| protocol.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/10_general_pickup_comparison/18_experiment_suite_20261029T020602Z/protocol.json`） | `deb57b4cf3628da06ce4a6b9801d7bb6e2f93f851246eeda9a6378256c56af53` |
| COMPLETION.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/10_general_pickup_comparison/18_experiment_suite_20261029T020602Z/COMPLETION.json`） | `505cf742fb4d5136d0c6daef1a5e7a66bb6f234dcc6bc6846e84deab91e8234f` |
| suite-report.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/10_general_pickup_comparison/18_experiment_suite_20261029T020602Z/suite-report.json`） | `ea917abf237cc22f141c146750519ce2986e8aa629f2f2467cba8e695410c412` |
| video-manifest.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/10_general_pickup_comparison/18_experiment_suite_20261029T020602Z/video-manifest.json`） | `bb141d52bd56890b929214c1c2bad5c27598b3155a18f30ca76f6adeca88b38f` |
| archive-manifest.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/10_general_pickup_comparison/18_experiment_suite_20261029T020602Z/archive-manifest.json`） | `f598d28c0f3caa5df04af8799438d28f701802b89a667d9fd254209f37c1c5d7` |
| extension-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/10_general_pickup_comparison/18_experiment_suite_20261029T020602Z/extension-status.json`） | `70c3a60e08817d91907eec9aa4c76ebb7bd3a2a27ed6f67ecd29eb7ced4337c1` |
| controller-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/10_general_pickup_comparison/18_experiment_suite_20261029T020602Z/controller-status.json`） | `cce1722d1d27d49ea5183d48194956c1a254701ec24a36e16ce689f7d4744e1b` |
| experiment-summary.txt（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/10_general_pickup_comparison/18_experiment_suite_20261029T020602Z/experiment-summary.txt`） | `514f23982f7072be6fe01f6666fe69e0fe5eece53c3acf4e0fed9534c0b76bc9` |
| thinking-continuation-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/10_general_pickup_comparison/18_experiment_suite_20261029T020602Z/thinking-continuation-status.json`） | `d387b81c1a1398e94a0cdfbf8a552e170eeda6a959f39f03a548bfeed46ab4ac` |
| api-modes/status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/10_general_pickup_comparison/18_experiment_suite_20261029T020602Z/api-modes/status.json`） | `2869480b56784c6fac1ce5a92de7bdb482b558686e10646f1e46ebd4d7f019e4` |
| layout-assets/status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/10_general_pickup_comparison/18_experiment_suite_20261029T020602Z/layout-assets/status.json`） | `7160aaee75a745f27ffb2b4da1e6f327db6790a7b5d6ee52a5e4b0751e983cbf` |
| control_code_01/status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/10_general_pickup_comparison/18_experiment_suite_20261029T020602Z/control_code_01/status.json`） | `38bd98fe7e736cd18fe5bb449f7b07f7e097e77c0907f6f90ffd22fd629d8f1d` |
| control_code_02/status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/10_general_pickup_comparison/18_experiment_suite_20261029T020602Z/control_code_02/status.json`） | `ec29f0cb6dbb7f814e914716852e055a48f603d0d8ac0e179efc1f588d3eda1c` |
| control_code_03/status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/10_general_pickup_comparison/18_experiment_suite_20261029T020602Z/control_code_03/status.json`） | `82cd3601e11e513242ffbe77662eb252c8c8d2ad3e3f75b186d87cb033cc3bf5` |
| control_code_01_retry2/native-result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/10_general_pickup_comparison/18_experiment_suite_20261029T020602Z/control_code_01_retry2/native-result.json`） | `117b7aac5c033705b64fc53e97b00912e1fec4f50cff9869aee75b750b3529a6` |
| control_code_02/native-result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/10_general_pickup_comparison/18_experiment_suite_20261029T020602Z/control_code_02/native-result.json`） | `117b7aac5c033705b64fc53e97b00912e1fec4f50cff9869aee75b750b3529a6` |
| new_layouts_agent/api/call-001-response.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/10_general_pickup_comparison/18_experiment_suite_20261029T020602Z/new_layouts_agent/api/call-001-response.json`） | `834215868675a6542d19fcd502e50f1bf83780102d8c7865d046adfee7861dbd` |
| new_layouts_agent/api/call-002-response.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/10_general_pickup_comparison/18_experiment_suite_20261029T020602Z/new_layouts_agent/api/call-002-response.json`） | `475ef5e231d3fc2b7c9eeed68e5d17f2e2e67d8ba1d8af8f2f40dec3ab0d0a1e` |
| procedure-sources/cloud_download_subset.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/10_general_pickup_comparison/18_experiment_suite_20261029T020602Z/procedure-sources/cloud_download_subset.py`） | `b4de34010cba8f85e733f8ce591c05210ec11d1fc7f4206ac4da2ad79b737ac1` |
| procedure-sources/cloud_native_subset.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/10_general_pickup_comparison/18_experiment_suite_20261029T020602Z/procedure-sources/cloud_native_subset.py`） | `3417e2de9a12150ada9691619a757d5712ff4b3b4e616351d1bed8588f4a3b14` |
| procedure-sources/cloud_probe_qwen_modes.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/10_general_pickup_comparison/18_experiment_suite_20261029T020602Z/procedure-sources/cloud_probe_qwen_modes.py`） | `c3dbadc617c7a7ed6fa94184c689d662c6646f2400427a72f700f8ac22f50fe8` |

### 原协议中可直接定位的字段

来源 `result/10_general_pickup_comparison/18_experiment_suite_20261029T020602Z/protocol.json`：
- `task` = `general_pickup`
- `seed` = `0`


## 阅读覆盖与下一步

本单元 1197 个可读普通文件、953 种不同字节内容已完整读入并校验；逐文件清单见 [审计账本](../../evidence/readthrough_20261102/file-review-ledger.jsonl.gz)，按 `HIST-028` 检索。JSON/日志/代码等做对应结构分析，重点协议、结果、失败和计量证据用于本条解释；这不声称所有依赖副本逐行人工精读，或全部视频逐帧人工审片。

下一步：本阶段记录封存至 11 月 2 日结束。后续实验另登记；如需补证，先定位本条限制对应原件，不自动重跑。
