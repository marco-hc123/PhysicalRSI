# HIST-027 · 高层 Agent 最小闭环

- 历史记录范围（北京时间）：2026-10-29T09:11:10.633027+08:00 至 2026-10-29T09:11:10.633027+08:00。
- 时间依据：original structured timestamp fields; observed record range is not necessarily physical rollout duration
- 本次回溯补录：2026-11-05 11:40，不是重跑日期。
- 类型：`native`；原批次：`17_qwen_agent_episode_20261029T010919Z`。
- 原件现址：`/mnt/data/joey_tr/physical-RSI/result/09_single_task_validation/17_qwen_agent_episode_20261029T010919Z/`。历史文件中的旧执行路径保留作来源，本次导航统一指向实验室。
- 周志：[ EXP-2026W44-015 ](../../LOGS/2026-W44.md#exp-2026w44-015)。同一批次已有摘要/续接副本不新增实验计数。

## 做了什么与得到什么

验证 API 选技能、执行和原生评分能连起来。

一次实际 HTTP，input=11552/output=198/total=11750；general_pickup 正常得到原生结果但 success=false。

## 解释边界与失败记录

判定：**部分**。闭环可运行与物理成功分开；不与此前连通 smoke 重复计数。

## 复现与证据定位

本次只读取与离线复算；历史 runner、日志、协议、依赖指纹保留在下列原件。不同阶段的补丁和环境不能用一个背景 commit 替代。未明确记录的 seed、硬件或启动命令保持未知，不从今天服务器配置倒推。

| 证据原件（实验室现址） | SHA256 |
|---|---|
| status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/09_single_task_validation/17_qwen_agent_episode_20261029T010919Z/status.json`） | `5a39bc3766d081209b26e9e00a3b2b1c5a584aaf3bfab366c9199c9f0b3ccab5` |
| native-result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/09_single_task_validation/17_qwen_agent_episode_20261029T010919Z/native-result.json`） | `99b780f4e1842dfa81b413ccd2e5302e5827cc349fea4edf978e1bd847986ed3` |
| policy-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/09_single_task_validation/17_qwen_agent_episode_20261029T010919Z/policy-status.json`） | `094c01a803cbc90e30397508ce987283d61c891afab3051a16a71f1bed7081c0` |
| usage-summary.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/09_single_task_validation/17_qwen_agent_episode_20261029T010919Z/usage-summary.json`） | `2216e549bfb82457a788199f59096281ec8ed0bf5d22e569ec225751630d49fd` |
| client.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/09_single_task_validation/17_qwen_agent_episode_20261029T010919Z/client.log`） | `72596681fce2d2e88fe61ae12b4511fb294f89a25f51625cacb6c2de446f50c3` |
| policy.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/09_single_task_validation/17_qwen_agent_episode_20261029T010919Z/policy.log`） | `cd0233862c014df2cd97a3e6e38fb996482d72f292283e1de54e4a201fa1d356` |
| skills.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/09_single_task_validation/17_qwen_agent_episode_20261029T010919Z/skills.json`） | `63195c4d5f14d10a89bd4d6a6169a8aaf4f52eaaaa76686f55884fa7ebf33b0e` |
| configuration.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/09_single_task_validation/17_qwen_agent_episode_20261029T010919Z/configuration.log`） | `0afe8129f628d9fef4cf26548d1e11b2e6b3dcfb494330da7d9377a3e63ec202` |
| source-hashes.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/09_single_task_validation/17_qwen_agent_episode_20261029T010919Z/source-hashes.json`） | `aec995caa94c837b36bb04df6388157b5022c77c56975508eb0a64dd4ec0240b` |
| client-command.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/09_single_task_validation/17_qwen_agent_episode_20261029T010919Z/client-command.json`） | `6361bfa659dc6bc0bf21ddaca2649be14cf1cb2ecebc6725e0b67d6532be37e9` |
| measurement-notes.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/09_single_task_validation/17_qwen_agent_episode_20261029T010919Z/measurement-notes.json`） | `238fa41cafd6c2dd983de9d0de1f056a9e8889e116ce6261e2cb1f31a5fdbfd7` |
| policy-deployment.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/09_single_task_validation/17_qwen_agent_episode_20261029T010919Z/policy-deployment.json`） | `3ae09b9433971a0f182b0850224e5a6ae0fcb9b693f75b96f11a4823f2708771` |
| api/call-001-request.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/09_single_task_validation/17_qwen_agent_episode_20261029T010919Z/api/call-001-request.json`） | `d3f08ce9e88a4c6eb49b4c6d3afe4dd2d83310b34bb6868f063ec6e9d4ded258` |
| api/call-001-metadata.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/09_single_task_validation/17_qwen_agent_episode_20261029T010919Z/api/call-001-metadata.json`） | `b1885724812fa81cc8ae2aa455908f0cb79b3718c5d81c69c6c4a54b8bd6896f` |
| api/call-001-response.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/09_single_task_validation/17_qwen_agent_episode_20261029T010919Z/api/call-001-response.json`） | `51867a6154fc721f43c29c88f721e0936fcb11fbcca10b68ef28c763c42180a0` |
| sources/cloud_qwen_agent_server.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/09_single_task_validation/17_qwen_agent_episode_20261029T010919Z/sources/cloud_qwen_agent_server.py`） | `8115a025f5e37b9aa785dab29595b1976048c7354a42e8d950677bec1496964f` |
| sources/cloud_run_qwen_episode.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/09_single_task_validation/17_qwen_agent_episode_20261029T010919Z/sources/cloud_run_qwen_episode.py`） | `716a20c27c91867a74dd1de8bcc082d9dea4e3cb40d56197d285538e811d5c38` |

## 阅读覆盖与下一步

本单元 29 个可读普通文件、29 种不同字节内容已完整读入并校验；逐文件清单见 审计账本（原始归档位置：`../../evidence/readthrough_20261102/file-review-ledger.jsonl.gz`），按 `HIST-027` 检索。JSON/日志/代码等做对应结构分析，重点协议、结果、失败和计量证据用于本条解释；这不声称所有依赖副本逐行人工精读，或全部视频逐帧人工审片。

下一步：本阶段记录封存至 11 月 2 日结束。后续实验另登记；如需补证，先定位本条限制对应原件，不自动重跑。
