# HIST-007 · 120 次合成输入 API 正式执行

- 历史记录范围（北京时间）：2026-10-27 至 2026-10-27。
- 时间依据：来源：原记录日期/登记目录；不把文件传输时间当实验开始时间。
- 本次回溯补录：2026-11-05 11:40，不是重跑日期。
- 类型：`api`；原批次：`05_api20_execution_20261027`。
- 原件现址：`/mnt/data/joey_tr/physical-RSI/result/05_api20_execution_20261027/`。历史文件中的旧执行路径保留作来源，本次导航统一指向实验室。
- 周志：[ EXP-2026W44-001 ](../../LOGS/2026-W44.md#exp-2026w44-001)。同一批次已有摘要/续接副本不新增实验计数。

## 做了什么与得到什么

检验较宽输入覆盖下目录投影的用量和计划契约表现。

120/120 HTTP、JSON、contract 和预设标签通过；总 Token 2204597，缓存命中 41 条；输入均值下降 67.31%、total 66.87%、HTTP 均时 31.65%。

## 解释边界与失败记录

判定：**部分**。20 合成场景不是 120 个机器人任务；预设标签不是原生任务评分。

## 复现与证据定位

本次只读取与离线复算；历史 runner、日志、协议、依赖指纹保留在下列原件。不同阶段的补丁和环境不能用一个背景 commit 替代。未明确记录的 seed、硬件或启动命令保持未知，不从今天服务器配置倒推。

| 证据原件（实验室现址） | SHA256 |
|---|---|
| calls.csv（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/05_api20_execution_20261027/calls.csv`） | `e698d9b48c2a032cca108927e8fe80952c9a7c56cb200993004184aa331c7f26` |
| inputs/protocol.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/05_api20_execution_20261027/inputs/protocol.json`） | `81ee864938971e3f99ab038e5b8dd5903d204692f7a17bfa1b7c42ce23c6496d` |
| status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/05_api20_execution_20261027/status.json`） | `61c070903cbf2366790739eb24b379d3dff93c53d7318feaa312d022033e02da` |
| summary.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/05_api20_execution_20261027/summary.json`） | `b5507d584135139706e81bf126be5e29ea4cd2d0a1977d1a09141d8a4180fcb9` |
| file_manifest.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/05_api20_execution_20261027/file_manifest.json`） | `f85d0741dced05d33454db042b0bc8cdddb120b60ebcc04115fc453e133a14a1` |
| execution_manifest.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/05_api20_execution_20261027/execution_manifest.json`） | `f468920d1ef7cd4e8eb98f2e4abd2d6b1c847ab7befa03120bcba21835b7fb9f` |
| inputs/request_manifest.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/05_api20_execution_20261027/inputs/request_manifest.json`） | `641523580abde97bf5925948ba57651be370638998322f1efdceaa9c6ef6b692` |
| README.txt（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/05_api20_execution_20261027/README.txt`） | `1b1bfc76a688e6270a357f652473bf04c2ac4ff72b9edc0b96cac15da8314d31` |
| checkpoint_audit.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/05_api20_execution_20261027/checkpoint_audit.json`） | `589c3edfb982730a1b9041ebfd7deb8b6841ffd93712b9e0a6cbbcd47b864489` |
| completion_audit.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/05_api20_execution_20261027/completion_audit.json`） | `93be69c86d4b34eea254ba9c4661130e5d3969c19f776184967fdc3a966d8275` |
| runtime_requirements.txt（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/05_api20_execution_20261027/runtime_requirements.txt`） | `22710b8c78a4d35b246195ac3aa1b3a766dca63103fa4eb7deaddff20cbe6b1e` |
| offline_runner_checks.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/05_api20_execution_20261027/offline_runner_checks.json`） | `e81a63a1a6f4e3d14a9cfc1405f2d1874ab88daf9506117edcf0599f2c5c16bf` |
| tools/run_live.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/05_api20_execution_20261027/tools/run_live.py`） | `d8f799818dcacba58b4a35281d6c5469ee2f4ee23938b4fff1af8efe294b747c` |
| inputs/scenes.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/05_api20_execution_20261027/inputs/scenes.json`） | `b2c758a17faee627202d82370d680f4e25aec20f3fd846c43b0124fd7a00383c` |
| raw_responses/scene_01__projected__r1.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/05_api20_execution_20261027/raw_responses/scene_01__projected__r1.json`） | `38cbc38b157cc65d7fd6bfcafca7c57b7b6325fc7f7c0848f1041b43fbb1e593` |
| raw_responses/scene_01__projected__r2.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/05_api20_execution_20261027/raw_responses/scene_01__projected__r2.json`） | `5c5451fdfa5bc988f2f64e116efe99e54b32c1c6b04967af49b4d9165ed247dc` |
| tools/finalize_records.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/05_api20_execution_20261027/tools/finalize_records.py`） | `ab40a109189ac777f01aa5256554d34538ce95c6cde682db317439a217d66aaf` |

### 原协议中可直接定位的字段

来源 `result/05_api20_execution_20261027/inputs/protocol.json`：
- `created_utc` = `2026-10-27T13:14:26.604330+00:00`
- `source_commit` = `90b322a3a362aad14125f36d8ed080ca31daaea6`
- `model` = `qwen3-vl-plus`
- `sampling.enable_thinking` = `False`


### 本次独立离线复算

`core-metric-verification.json` 中的 `api120` 已通过。原始数据、使用字段和逐源 SHA256 均保留；未重新请求模型或重跑仿真。

```json
{
  "http": 120,
  "total_tokens": 2204597,
  "cache_hits": 41,
  "groups": {
    "projected": {
      "n": 60,
      "input_tokens": 8969.3,
      "output_tokens": 175.06666666666666,
      "total_tokens": 9144.366666666667,
      "elapsed_seconds": 9.864257193667193
    },
    "unprojected": {
      "n": 60,
      "input_tokens": 27437.3,
      "output_tokens": 161.61666666666667,
      "total_tokens": 27598.916666666668,
      "elapsed_seconds": 14.43237250285844
    }
  },
  "percent_reductions": {
    "input_tokens": 67.30983004887507,
    "total_tokens": 66.866936202206,
    "elapsed_seconds": 31.651866720364218
  },
  "all_contracts_valid": true,
  "method": "Every CSV row matched to original provider response identity, SHA256 and usage."
}
```

## 阅读覆盖与下一步

本单元 327 个可读普通文件、327 种不同字节内容已完整读入并校验；逐文件清单见 审计账本（原始归档位置：`../../evidence/readthrough_20261102/file-review-ledger.jsonl.gz`），按 `HIST-007` 检索。JSON/日志/代码等做对应结构分析，重点协议、结果、失败和计量证据用于本条解释；这不声称所有依赖副本逐行人工精读，或全部视频逐帧人工审片。

下一步：本阶段记录封存至 11 月 2 日结束。后续实验另登记；如需补证，先定位本条限制对应原件，不自动重跑。
