# HIST-015 · 原生场景预检第一次失败

- 历史记录范围（北京时间）： 至 。
- 时间依据：run ID timestamp only; exact execution times not inferred
- 本次回溯补录：2026-11-05 11:40，不是重跑日期。
- 类型：`preflight`；原批次：`12_native_scene_preflight_20261028T223526Z`。
- 原件现址：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/12_native_scene_preflight_20261028T223526Z/`。历史文件中的旧执行路径保留作来源，本次导航统一指向实验室。
- 周志：[ EXP-2026W44-007 ](../../LOGS/2026-W44.md#exp-2026w44-007)。同一批次已有摘要/续接副本不新增实验计数。

## 做了什么与得到什么

加载 general_pickup 布局、机器人状态与相机。

原始 result 和 traceback 指向缺少 h5py，未得到有效策略任务结果。

## 解释边界与失败记录

判定：**Crashed**。进程退出码不能替代 passed/原生评分；task success 保持未知。

## 复现与证据定位

本次只读取与离线复算；历史 runner、日志、协议、依赖指纹保留在下列原件。不同阶段的补丁和环境不能用一个背景 commit 替代。未明确记录的 seed、硬件或启动命令保持未知，不从今天服务器配置倒推。

| 证据原件（实验室现址） | SHA256 |
|---|---|
| result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/12_native_scene_preflight_20261028T223526Z/result.json`） | `743e306624aec68f11633d9d7c738a0d57fb3ce2e2ef96cdb3abb915e68d1978` |
| run.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/12_native_scene_preflight_20261028T223526Z/run.log`） | `4f5342ba9a364fd91dc709b184b1004350e7722f3c16374e1a090dfea068732e` |
| exit_code.txt（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/12_native_scene_preflight_20261028T223526Z/exit_code.txt`） | `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` |

## 阅读覆盖与下一步

本单元 3 个可读普通文件、3 种不同字节内容已完整读入并校验；逐文件清单见 审计账本（原始归档位置：`../../evidence/readthrough_20261102/file-review-ledger.jsonl.gz`），按 `HIST-015` 检索。JSON/日志/代码等做对应结构分析，重点协议、结果、失败和计量证据用于本条解释；这不声称所有依赖副本逐行人工精读，或全部视频逐帧人工审片。

下一步：本阶段记录封存至 11 月 2 日结束。后续实验另登记；如需补证，先定位本条限制对应原件，不自动重跑。
