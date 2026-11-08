# HIST-005 · 80 次固定输入 API 与 schema 修订

- 历史记录范围（北京时间）：2026-10-27 至 2026-10-27。
- 时间依据：来源：原记录日期/登记目录；不把文件传输时间当实验开始时间。
- 本次回溯补录：2026-11-05 11:40，不是重跑日期。
- 类型：`api`；原批次：`03_api_experiments`。
- 原件现址：`/mnt/data/joey_tr/physical-RSI/result/03_api_experiments/`。历史文件中的旧执行路径保留作来源，本次导航统一指向实验室。
- 周志：[ EXP-2026W44-006 ](../../LOGS/2026-W44.md#exp-2026w44-006)。同一批次已有摘要/续接副本不新增实验计数。

## 做了什么与得到什么

比较目录投影的语言用量，并检验返回计划的契约。

80 次 HTTP 成功，共 870375 Token；composition 40 次、operation pilot 10 次、补 schema 后 30 次。pilot 契约 projected 0/5、unprojected 1/5；schema 两条件各 15/15。

## 解释边界与失败记录

判定：**部分**。schema 是观察 pilot 后修订；合成输入没有机器人动作。输入下降与延迟下降并非固定比例。

## 复现与证据定位

本次只读取与离线复算；历史 runner、日志、协议、依赖指纹保留在下列原件。不同阶段的补丁和环境不能用一个背景 commit 替代。未明确记录的 seed、硬件或启动命令保持未知，不从今天服务器配置倒推。

| 证据原件（实验室现址） | SHA256 |
|---|---|
| all_calls.csv（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/03_api_experiments/all_calls.csv`） | `9750f235b83b0f84019fbde0abf6958161a080f7b0b85d069bb448413c9f79ef` |
| completion.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/03_api_experiments/completion.json`） | `0265bc5fee3e30d55f7d0cc013eda517db5e80601c0562278cfaef68eb613866` |
| 20261027_qwen_followup/calls.csv（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/03_api_experiments/20261027_qwen_followup/calls.csv`） | `a95f92ca5cb81b5c590dc3721184c780c59829d306b8eb234a40df291934d1dd` |
| 20261027_qwen_projection/calls.csv（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/03_api_experiments/20261027_qwen_projection/calls.csv`） | `601cb0b33ec62e39f913ef33e9243af4dd3e52dc5c0875d4044147e45aeedda0` |
| summary.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/03_api_experiments/summary.json`） | `6f81601b50a0399dc09bfa2a99d3943f74193d74ed2b4e26993831ae33cbcc75` |
| file_manifest.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/03_api_experiments/file_manifest.json`） | `b28defca75b3beb3c831f9cb566896098a12cdd95fcf720912a183e44632f29c` |
| 20261027_qwen_followup/summary.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/03_api_experiments/20261027_qwen_followup/summary.json`） | `04558b5f8ae6b706be99b940025d3845f62fa908d99313121b6987f8d9e1d0df` |
| 20261027_qwen_followup/manifest.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/03_api_experiments/20261027_qwen_followup/manifest.json`） | `ad67e090a3ce864bb2a3f21aeea127f2b2a99c719ea18ad793a94b23c3ab5763` |
| 20261027_qwen_projection/summary.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/03_api_experiments/20261027_qwen_projection/summary.json`） | `186d8329b4e509c8fd06e2fd8caf33a78e15e1cb4f1a09a3b156ae62c3dd716a` |
| 20261027_qwen_projection/manifest.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/03_api_experiments/20261027_qwen_projection/manifest.json`） | `4df915b1533b10adb899ed663d1cd56d69f6f563638e3e793dd05b4f772f6aa6` |
| README.txt（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/03_api_experiments/README.txt`） | `5024ae34d39eab432dd12b6ef80e8be9ed686b3eff27dc4a024dc685bb452dd2` |
| 00_实验报告.txt（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/03_api_experiments/00_实验报告.txt`） | `a1aa4c476394afde378fef0c4cf1351f69c2446afe31e6c8113b93658d604bf3` |
| all_calls.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/03_api_experiments/all_calls.json`） | `12518f435d20938b3c68d87b4b6d6a9a832e1dffe591838dbe5a4b21bebedeb3` |
| failure_analysis.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/03_api_experiments/failure_analysis.json`） | `5a5829e2b31d08a94a422b0165e2610cec870700dcc3eea633e2ee581698242b` |
| 20261027_qwen_followup/experiment_script.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/03_api_experiments/20261027_qwen_followup/experiment_script.py`） | `2a2cb2d0d8226b2385cdcd4a3ca9c6b4406ec99bf61670486f7aab00b2a1e500` |
| 20261027_qwen_projection/experiment_script.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/03_api_experiments/20261027_qwen_projection/experiment_script.py`） | `b4c314d0cd8957ae48b051052821178727a1f5d20db2305d7900da4a996afeb0` |
| analysis_tools/analyze_qwen_experiments.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/03_api_experiments/analysis_tools/analyze_qwen_experiments.py`） | `c4c368c48266c6bebba327894d36fa6c4a41c2f5b9eccfacf6506ebebd78f50b` |

### 原协议中可直接定位的字段

来源 `result/03_api_experiments/20261027_qwen_followup/manifest.json`：
- `source_commit` = `90b322a3a362aad14125f36d8ed080ca31daaea6`
- `model` = `qwen3-vl-plus`
- `sampling.enable_thinking` = `False`

来源 `result/03_api_experiments/20261027_qwen_projection/manifest.json`：
- `source_commit` = `90b322a3a362aad14125f36d8ed080ca31daaea6`
- `model` = `qwen3-vl-plus`
- `sampling.enable_thinking` = `False`


### 本次独立离线复算

`core-metric-verification.json` 中的 `api80` 已通过。原始数据、使用字段和逐源 SHA256 均保留；未重新请求模型或重跑仿真。

```json
{
  "http": 80,
  "total_tokens": 870375,
  "cache_hits": 38,
  "suites": {
    "registry_22_operations": 10,
    "example_2_compositions": 40,
    "registry_22_operations_schema": 30
  },
  "method": "Recomputed from original all_calls.csv; original response files separately parsed in full file audit."
}
```

## 阅读覆盖与下一步

本单元 184 个可读普通文件、160 种不同字节内容已完整读入并校验；逐文件清单见 [审计账本](../../evidence/readthrough_20261102/file-review-ledger.jsonl.gz)，按 `HIST-005` 检索。JSON/日志/代码等做对应结构分析，重点协议、结果、失败和计量证据用于本条解释；这不声称所有依赖副本逐行人工精读，或全部视频逐帧人工审片。

下一步：本阶段记录封存至 11 月 2 日结束。后续实验另登记；如需补证，先定位本条限制对应原件，不自动重跑。
