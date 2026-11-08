# HIST-002 · 隔离环境与离线工作流验收

- 历史记录范围（北京时间）：2026-10-26 至 2026-10-26。
- 时间依据：来源：原记录日期/登记目录；不把文件传输时间当实验开始时间。
- 本次回溯补录：2026-11-05 11:40，不是重跑日期。
- 类型：`software`；原批次：`01_environment`。
- 原件现址：`/mnt/data/joey_tr/physical-RSI/result/01_environment/`。历史文件中的旧执行路径保留作来源，本次导航统一指向实验室。
- 周志性质：协议、准备、审计或管理节点，未作为新的物理实验累计。

## 做了什么与得到什么

确认实验工具能在项目隔离环境导入、运行和续接。

已有部署检查、两条离线请求回放及两个有效计划；真实 API 为零，未测供应商 usage 保持 null。

## 解释边界与失败记录

判定：**N**。离线通过不能记成机器人成功；环境安装副本与 fixture 不重复计作科学实验。

## 复现与证据定位

本次只读取与离线复算；历史 runner、日志、协议、依赖指纹保留在下列原件。不同阶段的补丁和环境不能用一个背景 commit 替代。未明确记录的 seed、硬件或启动命令保持未知，不从今天服务器配置倒推。

| 证据原件（实验室现址） | SHA256 |
|---|---|
| cpu-fixture/preparation/cases/protocol.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/01_environment/cpu-fixture/preparation/cases/protocol.json`） | `d928d0107b57b6f85560ff7466261e141dd01dd3e7605edd41b0107ddff42dbe` |
| cpu-fixture/campaign/template/cases/protocol.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/01_environment/cpu-fixture/campaign/template/cases/protocol.json`） | `d928d0107b57b6f85560ff7466261e141dd01dd3e7605edd41b0107ddff42dbe` |
| cpu-fixture/campaign/rounds/round-0001/execution/selection.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/01_environment/cpu-fixture/campaign/rounds/round-0001/execution/selection.json`） | `28a1e821c6b065ae3d91362dc5ec0be1837748c711d8b4b4cfbb960a5a645b72` |
| cpu-fixture/campaign/rounds/round-0001/execution/cases/protocol.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/01_environment/cpu-fixture/campaign/rounds/round-0001/execution/cases/protocol.json`） | `d928d0107b57b6f85560ff7466261e141dd01dd3e7605edd41b0107ddff42dbe` |
| offline-replay/summary.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/01_environment/offline-replay/summary.json`） | `7eefe4f141157f8ab437903258fc4af00217ba9438f45608d7d3394d599c4447` |
| cpu-fixture/test-result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/01_environment/cpu-fixture/test-result.json`） | `f1e5042329d58fa7691a3bb9201c38acc3416ff061c2c0e0ca7b799dffed82ee` |
| offline-replay/manifest.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/01_environment/offline-replay/manifest.json`） | `62507b3e688bdc672762be846f3e31fbf6a005de280f56bcf7591d94fa312323` |
| cpu-fixture/campaign-result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/01_environment/cpu-fixture/campaign-result.json`） | `de654e1964d7975a0360cd717b1a10b8123347ed3518bb0baeb87da329ff3941` |
| cpu-fixture/research-result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/01_environment/cpu-fixture/research-result.json`） | `27aec2d1b775b4f94ed53f58a4db78152319d1293e63cd1d1afe7bf1bdda981d` |
| cpu-fixture/report/report.md（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/01_environment/cpu-fixture/report/report.md`） | `f09516f9f991b51c1e5355037ac37e325dc4e9945c3648ce8b58616003ac4881` |
| cpu-fixture/report/manifest.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/01_environment/cpu-fixture/report/manifest.json`） | `78ed64b95a1141b4670378514f7cda75b9ee3c209c258546b8afc76d98ad91c7` |
| cpu-fixture/report/test-result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/01_environment/cpu-fixture/report/test-result.json`） | `f1e5042329d58fa7691a3bb9201c38acc3416ff061c2c0e0ca7b799dffed82ee` |
| cpu-fixture/report/campaign-result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/01_environment/cpu-fixture/report/campaign-result.json`） | `de654e1964d7975a0360cd717b1a10b8123347ed3518bb0baeb87da329ff3941` |
| cpu-fixture/report/research-result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/01_environment/cpu-fixture/report/research-result.json`） | `27aec2d1b775b4f94ed53f58a4db78152319d1293e63cd1d1afe7bf1bdda981d` |

### 原协议中可直接定位的字段

来源 `result/01_environment/offline-replay/manifest.json`：
- `source_pin.commit` = `90b322a3a362aad14125f36d8ed080ca31daaea6`


## 阅读覆盖与下一步

本单元 206 个可读普通文件、123 种不同字节内容已完整读入并校验；逐文件清单见 [审计账本](../../evidence/readthrough_20261102/file-review-ledger.jsonl.gz)，按 `HIST-002` 检索。JSON/日志/代码等做对应结构分析，重点协议、结果、失败和计量证据用于本条解释；这不声称所有依赖副本逐行人工精读，或全部视频逐帧人工审片。

下一步：本阶段记录封存至 11 月 2 日结束。后续实验另登记；如需补证，先定位本条限制对应原件，不自动重跑。
