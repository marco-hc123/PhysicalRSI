# HIST-022 · 固定 sparse-memory 最小原生回合

- 历史记录范围（北京时间）：2026-10-29T07:13:31.505345+08:00 至 2026-10-29T07:13:31.505345+08:00。
- 时间依据：original structured timestamp fields; observed record range is not necessarily physical rollout duration
- 本次回溯补录：2026-11-05 11:40，不是重跑日期。
- 类型：`native`；原批次：`16_fixed_sparse_episode_20261028T230241Z`。
- 原件现址：`/mnt/data/joey_tr/physical-RSI/result/09_single_task_validation/16_fixed_sparse_episode_20261028T230241Z/`。历史文件中的旧执行路径保留作来源，本次导航统一指向实验室。
- 周志：[ EXP-2026W44-013 ](../../LOGS/2026-W44.md#exp-2026w44-013)。同一批次已有摘要/续接副本不新增实验计数。

## 做了什么与得到什么

确认稀疏历史策略的独立加载和原生执行。

general_pickup 布局 0 得到 success=true、原生 score=100；高层 API=0。

## 解释边界与失败记录

判定：**N**。这是早期单例成功，必须与后来的独立布局失败并存；两种权重不同，不能归因于纯 memory 开关。

## 复现与证据定位

本次只读取与离线复算；历史 runner、日志、协议、依赖指纹保留在下列原件。不同阶段的补丁和环境不能用一个背景 commit 替代。未明确记录的 seed、硬件或启动命令保持未知，不从今天服务器配置倒推。

| 证据原件（实验室现址） | SHA256 |
|---|---|
| status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/09_single_task_validation/16_fixed_sparse_episode_20261028T230241Z/status.json`） | `d4490e073dbbf8cfc6bfa7e150ce7645c41b06ad0bee39645a0d7f56b7636d28` |
| native-result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/09_single_task_validation/16_fixed_sparse_episode_20261028T230241Z/native-result.json`） | `117b7aac5c033705b64fc53e97b00912e1fec4f50cff9869aee75b750b3529a6` |
| policy-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/09_single_task_validation/16_fixed_sparse_episode_20261028T230241Z/policy-status.json`） | `d40908e7e9397e0792231385cbba60b7bd99bb5245bd30cbec08ef3fac419903` |
| client.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/09_single_task_validation/16_fixed_sparse_episode_20261028T230241Z/client.log`） | `6eac1df5f0b8a0b14ea40f73c91659ee20116c27f3231d63e451ea4fba39d491` |
| policy.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/09_single_task_validation/16_fixed_sparse_episode_20261028T230241Z/policy.log`） | `56ea9a2006e117e33ecd81f3c16681f0b99843826f091b309d35ded8c3da4ca9` |
| launcher.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/09_single_task_validation/16_fixed_sparse_episode_20261028T230241Z/launcher.log`） | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| fixed-skill.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/09_single_task_validation/16_fixed_sparse_episode_20261028T230241Z/fixed-skill.json`） | `20e9584ba6c3ab06cd872890ac8d5e2c0a92e1b6fe7f33ea8e7433c6c2dc8e88` |
| visual-review.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/09_single_task_validation/16_fixed_sparse_episode_20261028T230241Z/visual-review.json`） | `b78f47f6835f5341b6bff3a63a884a72d68660d1d4d012eabeaa531e1a1eb767` |
| client-command.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/09_single_task_validation/16_fixed_sparse_episode_20261028T230241Z/client-command.json`） | `15ceaa1f305441cfcc1c8f50e2c1b5a04284e22a279977c73d83b6024babcfec` |
| policy-command.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/09_single_task_validation/16_fixed_sparse_episode_20261028T230241Z/policy-command.json`） | `643941c82a4a3cadebffc206f8143c7450cf9367d9a77262ae5cb0436a387347` |

### 本次独立离线复算

`core-metric-verification.json` 中的 `early_sparse_singleton` 已通过。原始数据、使用字段和逐源 SHA256 均保留；未重新请求模型或重跑仿真。

```json
{
  "result/09_single_task_validation/16_fixed_sparse_episode_20261028T230241Z/native-result.json": {
    "success_rate": 1.0,
    "score": 100.0
  }
}
```

## 阅读覆盖与下一步

本单元 15 个可读普通文件、15 种不同字节内容已完整读入并校验；逐文件清单见 [审计账本](../../evidence/readthrough_20261102/file-review-ledger.jsonl.gz)，按 `HIST-022` 检索。JSON/日志/代码等做对应结构分析，重点协议、结果、失败和计量证据用于本条解释；这不声称所有依赖副本逐行人工精读，或全部视频逐帧人工审片。

下一步：本阶段记录封存至 11 月 2 日结束。后续实验另登记；如需补证，先定位本条限制对应原件，不自动重跑。
