# HIST-017 · 原生场景预检通过

- 历史记录范围（北京时间）： 至 。
- 时间依据：run ID timestamp only; exact execution times not inferred
- 本次回溯补录：2026-11-05 11:40，不是重跑日期。
- 类型：`preflight`；原批次：`12_native_scene_preflight_20261028T224100Z`。
- 原件现址：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/12_native_scene_preflight_20261028T224100Z/`。历史文件中的旧执行路径保留作来源，本次导航统一指向实验室。
- 周志：[ EXP-2026W44-009 ](../../LOGS/2026-W44.md#exp-2026w44-009)。同一批次已有摘要/续接副本不新增实验计数。

## 做了什么与得到什么

核验稳定布局、机器人观测与三相机 RGB。

场景检查 passed，布局稳定，三相机与状态数据留存；未执行策略。

## 解释边界与失败记录

判定：**N**。robot_task_success 未测，不能从场景可见推断抓取成功。

## 复现与证据定位

本次只读取与离线复算；历史 runner、日志、协议、依赖指纹保留在下列原件。不同阶段的补丁和环境不能用一个背景 commit 替代。未明确记录的 seed、硬件或启动命令保持未知，不从今天服务器配置倒推。

| 证据原件（实验室现址） | SHA256 |
|---|---|
| result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/12_native_scene_preflight_20261028T224100Z/result.json`） | `5da71006498094442575a1adc036f61619aa30a81caf5ac67dd03c7d17a5d760` |
| run.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/12_native_scene_preflight_20261028T224100Z/run.log`） | `6bf4a30cd3c7252d59de4b499dfa88feba66cd0b5fd324974faed822d5f1d6d5` |
| visual-review.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/12_native_scene_preflight_20261028T224100Z/visual-review.json`） | `cefc9e65a3c4cf037329c08a51176ad099f1c41d8abc9acb2a4096f3a69c79c3` |
| process_exit_code.txt（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/12_native_scene_preflight_20261028T224100Z/process_exit_code.txt`） | `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` |

## 阅读覆盖与下一步

本单元 14 个可读普通文件、14 种不同字节内容已完整读入并校验；逐文件清单见 [审计账本](../../evidence/readthrough_20261102/file-review-ledger.jsonl.gz)，按 `HIST-017` 检索。JSON/日志/代码等做对应结构分析，重点协议、结果、失败和计量证据用于本条解释；这不声称所有依赖副本逐行人工精读，或全部视频逐帧人工审片。

下一步：本阶段记录封存至 11 月 2 日结束。后续实验另登记；如需补证，先定位本条限制对应原件，不自动重跑。
