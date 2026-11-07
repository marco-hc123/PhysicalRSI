# HIST-026 · 高层 Agent 初始化失败

- 历史记录范围（北京时间）：2026-10-29T09:08:22.378802+08:00 至 2026-10-29T09:08:22.378802+08:00。
- 时间依据：original structured timestamp fields; observed record range is not necessarily physical rollout duration
- 本次回溯补录：2026-11-05 11:40，不是重跑日期。
- 类型：`native_attempt`；原批次：`17_qwen_agent_episode_20261029T010809Z`。
- 原件现址：`/mnt/data/joey_tr/physical-RSI/result/09_single_task_validation/17_qwen_agent_episode_20261029T010809Z/`。历史文件中的旧执行路径保留作来源，本次导航统一指向实验室。
- 周志：[ EXP-2026W44-014 ](../../LOGS/2026-W44.md#exp-2026w44-014)。同一批次已有摘要/续接副本不新增实验计数。

## 做了什么与得到什么

接通计量包装器与技能模型。

MeasuredModel 缺少 preloaded 属性，初始化失败；实际 API 尝试为 0。

## 解释边界与失败记录

判定：**Crashed**。软件接口失败不作为已完成机器人零分结果。

## 复现与证据定位

本次只读取与离线复算；历史 runner、日志、协议、依赖指纹保留在下列原件。不同阶段的补丁和环境不能用一个背景 commit 替代。未明确记录的 seed、硬件或启动命令保持未知，不从今天服务器配置倒推。

| 证据原件（实验室现址） | SHA256 |
|---|---|
| status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/09_single_task_validation/17_qwen_agent_episode_20261029T010809Z/status.json`） | `0e8b58d04e94fe2b78ae6d188058a802919f141849226b2c19e76af57fe63114` |
| policy-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/09_single_task_validation/17_qwen_agent_episode_20261029T010809Z/policy-status.json`） | `2dd228c3d77946d78f5ca104f4b8c3d82f4b37178bfd6ff9f515858e2e3fb581` |
| usage-summary.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/09_single_task_validation/17_qwen_agent_episode_20261029T010809Z/usage-summary.json`） | `d4c51a790cf2d0b678e16eac7cc65176f1247c7097a76ae5652bdd6f6a607748` |
| policy.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/09_single_task_validation/17_qwen_agent_episode_20261029T010809Z/policy.log`） | `b61a879571c2dfbed2b1bde6dfb40418f4d294f296ba8b9e20f406043de0ef76` |
| skills.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/09_single_task_validation/17_qwen_agent_episode_20261029T010809Z/skills.json`） | `0d0883c1cfbb70b1e9e7755f27743d731bc8d6aac177a351f9646daceb86a68e` |
| configuration.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/09_single_task_validation/17_qwen_agent_episode_20261029T010809Z/configuration.log`） | `0afe8129f628d9fef4cf26548d1e11b2e6b3dcfb494330da7d9377a3e63ec202` |
| source-hashes.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/09_single_task_validation/17_qwen_agent_episode_20261029T010809Z/source-hashes.json`） | `4c84b072f9610771da70273bb54229487ca3de73cd15efe86d200a37eb473b68` |
| policy-deployment.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/09_single_task_validation/17_qwen_agent_episode_20261029T010809Z/policy-deployment.json`） | `3ae09b9433971a0f182b0850224e5a6ae0fcb9b693f75b96f11a4823f2708771` |
| runtime/7e9011e2b50443bb91732f8452c3826c/identity.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/09_single_task_validation/17_qwen_agent_episode_20261029T010809Z/runtime/7e9011e2b50443bb91732f8452c3826c/identity.json`） | `79d69f2392b6a55f9c18db93af2f477d61bf5f0f6ae8ead446f17c633c9c947a` |
| runtime/7e9011e2b50443bb91732f8452c3826c/memory/2baf78234f39ff0cd1d7a8a52b85ff89fdb0e21285f7e1812e36f805899d7dab.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/09_single_task_validation/17_qwen_agent_episode_20261029T010809Z/runtime/7e9011e2b50443bb91732f8452c3826c/memory/2baf78234f39ff0cd1d7a8a52b85ff89fdb0e21285f7e1812e36f805899d7dab.json`） | `0856f8bb8917062bd931608261774c8a4061c95f3f8e3d585c4cf7663de13c29` |

## 阅读覆盖与下一步

本单元 12 个可读普通文件、12 种不同字节内容已完整读入并校验；逐文件清单见 审计账本（原始归档位置：`../../evidence/readthrough_20261102/file-review-ledger.jsonl.gz`），按 `HIST-026` 检索。JSON/日志/代码等做对应结构分析，重点协议、结果、失败和计量证据用于本条解释；这不声称所有依赖副本逐行人工精读，或全部视频逐帧人工审片。

下一步：本阶段记录封存至 11 月 2 日结束。后续实验另登记；如需补证，先定位本条限制对应原件，不自动重跑。
