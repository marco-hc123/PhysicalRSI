# HIST-060 · 安装与引导过程日志

- 历史记录范围（北京时间）：原始日期未完整记录；截至本阶段归档 至 原始日期未完整记录；截至本阶段归档。
- 时间依据：来源：原记录日期/登记目录；不把文件传输时间当实验开始时间。
- 本次回溯补录：2026-11-05 11:40，不是重跑日期。
- 类型：`administration`；原批次：`setup_logs`。
- 原件现址：`/mnt/data/joey_tr/physical-RSI/result/setup_logs/`。历史文件中的旧执行路径保留作来源，本次导航统一指向实验室。
- 周志性质：协议、准备、审计或管理节点，未作为新的物理实验累计。

## 做了什么与得到什么

保留前期安装命令输出及失败恢复过程。

13个日志文件、11种不同内容，作为环境验收来源附件关联。

## 解释边界与失败记录

判定：**部分**。安装日志不单独作为机器人或模型实验，缺少原始执行日期的字段保持未明。

## 复现与证据定位

本次只读取与离线复算；历史 runner、日志、协议、依赖指纹保留在下列原件。不同阶段的补丁和环境不能用一个背景 commit 替代。未明确记录的 seed、硬件或启动命令保持未知，不从今天服务器配置倒推。

| 证据原件（实验室现址） | SHA256 |
|---|---|
| venv.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/setup_logs/venv.log`） | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| clone.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/setup_logs/clone.log`） | `451c985ced8775af57ab86266b26a47ee1cedf513b8c6d84bafec03d28ae5689` |
| cli-help.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/setup_logs/cli-help.log`） | `10b26022cde63b14cc0e88db3e12b712fda9cf458072697e8b208e36e0f7af1b` |
| pip-check.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/setup_logs/pip-check.log`） | `9261363b733079a641c2e4cc9bc46ffa1d8336945a87f807b6cf68847dbc9b09` |
| submodules.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/setup_logs/submodules.log`） | `d1a362b1ccff0b7e4d3a1415d0cf1cde04b2a4bbf93d2f312b5ec5cb977942a8` |
| pip-project.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/setup_logs/pip-project.log`） | `2fde7592eba72641c78ee3132babc9beb5b67ee4f1647d16d26cb7cc9794c8ff` |
| pip-research.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/setup_logs/pip-research.log`） | `c4d945908e70d08015b36dff44760f1a4fbbf4807943167ed11ff655dfd7e1e3` |
| cpu-fixture-first.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/setup_logs/cpu-fixture-first.log`） | `2e39d85540294f40a4f986ddfa28c6b276a5e8acd9d91a8b1832ecffc7896022` |
| measurement-tests.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/setup_logs/measurement-tests.log`） | `df197dfabc3bc9c289554f79e7498bd021f35edf624e33c3a3d67e452f14650e` |
| cpu-fixture-resume.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/setup_logs/cpu-fixture-resume.log`） | `2e39d85540294f40a4f986ddfa28c6b276a5e8acd9d91a8b1832ecffc7896022` |
| offline-replay-first.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/setup_logs/offline-replay-first.log`） | `7eefe4f141157f8ab437903258fc4af00217ba9438f45608d7d3394d599c4447` |
| offline-replay-resume.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/setup_logs/offline-replay-resume.log`） | `7eefe4f141157f8ab437903258fc4af00217ba9438f45608d7d3394d599c4447` |
| fixture-skill-registry.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/setup_logs/fixture-skill-registry.log`） | `d2a0c7494912b9af64b2e9ae28f60bb5741967a2e627f2165e9924f42f51c77f` |

## 阅读覆盖与下一步

本单元 13 个可读普通文件、11 种不同字节内容已完整读入并校验；逐文件清单见 [审计账本](../../evidence/readthrough_20261102/file-review-ledger.jsonl.gz)，按 `HIST-060` 检索。JSON/日志/代码等做对应结构分析，重点协议、结果、失败和计量证据用于本条解释；这不声称所有依赖副本逐行人工精读，或全部视频逐帧人工审片。

下一步：本阶段记录封存至 11 月 2 日结束。后续实验另登记；如需补证，先定位本条限制对应原件，不自动重跑。
