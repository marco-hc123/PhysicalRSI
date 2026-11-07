# HIST-004 · 两次真实 API 连通检查

- 历史记录范围（北京时间）：2026-10-27 至 2026-10-27。
- 时间依据：来源：原记录日期/登记目录；不把文件传输时间当实验开始时间。
- 本次回溯补录：2026-11-05 11:40，不是重跑日期。
- 类型：`api`；原批次：`03_api_connectivity`。
- 原件现址：`/mnt/data/joey_tr/physical-RSI/result/03_api_connectivity/`。历史文件中的旧执行路径保留作来源，本次导航统一指向实验室。
- 周志：[ EXP-2026W44-005 ](../../LOGS/2026-W44.md#exp-2026w44-005)。同一批次已有摘要/续接副本不新增实验计数。

## 做了什么与得到什么

检验文本、合成图片、JSON 输出及供应商 usage 是否可记录。

两次请求均通过预设检查，模型 qwen3-vl-plus；文本与图像 smoke 单列。

## 解释边界与失败记录

判定：**N**。接口连通不是机器人成功或目录节省实验；费用估计没有账单核对。

## 复现与证据定位

本次只读取与离线复算；历史 runner、日志、协议、依赖指纹保留在下列原件。不同阶段的补丁和环境不能用一个背景 commit 替代。未明确记录的 seed、硬件或启动命令保持未知，不从今天服务器配置倒推。

| 证据原件（实验室现址） | SHA256 |
|---|---|
| 20261027_163633/summary.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/03_api_connectivity/20261027_163633/summary.json`） | `4f58dcefdea2508de98ee85f3f69f065f373505562cd44f4853dc48127308440` |
| 20261027_163633/manifest.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/03_api_connectivity/20261027_163633/manifest.json`） | `efa49ea1ca0273f9029201a3f1a3ab4aa1aa66a79b2f75c2b4e5a0db8d764548` |
| 20261027_163633/text_result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/03_api_connectivity/20261027_163633/text_result.json`） | `197874985a155c37e722cba9f2d05cd55473b683e165eee020ca6294c9f39a92` |
| 20261027_163633/image_result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/03_api_connectivity/20261027_163633/image_result.json`） | `769a49a156ef1ff310ba2d627ca7d570e43104c4cc7c53e4ba7be1954411ab07` |
| 20261027_163633/README.txt（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/03_api_connectivity/20261027_163633/README.txt`） | `e3fbd4447e79297987b06c6160e28e10af6a09905ac696fbad0eec2e4621f7b6` |
| 20261027_163633/text_request.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/03_api_connectivity/20261027_163633/text_request.json`） | `51d9b3c25a6477c9f585c43198d849d75a0049471f38ab089dbe44e0f2bd5d5d` |
| 20261027_163633/image_request.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/03_api_connectivity/20261027_163633/image_request.json`） | `53793b79a21df07ae6c67b0e490816c206f2f60e356c4632aad6addd0e7433cd` |

### 原协议中可直接定位的字段

来源 `result/03_api_connectivity/20261027_163633/manifest.json`：
- `model` = `qwen3-vl-plus`
- `enable_thinking` = `False`


## 阅读覆盖与下一步

本单元 8 个可读普通文件、8 种不同字节内容已完整读入并校验；逐文件清单见 审计账本（原始归档位置：`../../evidence/readthrough_20261102/file-review-ledger.jsonl.gz`），按 `HIST-004` 检索。JSON/日志/代码等做对应结构分析，重点协议、结果、失败和计量证据用于本条解释；这不声称所有依赖副本逐行人工精读，或全部视频逐帧人工审片。

下一步：本阶段记录封存至 11 月 2 日结束。后续实验另登记；如需补证，先定位本条限制对应原件，不自动重跑。
