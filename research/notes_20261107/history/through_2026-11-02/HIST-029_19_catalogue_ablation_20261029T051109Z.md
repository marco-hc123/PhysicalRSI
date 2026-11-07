# HIST-029 · 原生技能目录投影消融

- 历史记录范围（北京时间）：2026-10-29T13:11:09.095457+08:00 至 2026-10-29T14:23:44.584986+08:00。
- 时间依据：original structured timestamp fields; observed record range is not necessarily physical rollout duration
- 本次回溯补录：2026-11-05 11:40，不是重跑日期。
- 类型：`ablation`；原批次：`19_catalogue_ablation_20261029T051109Z`。
- 原件现址：`/mnt/data/joey_tr/physical-RSI/result/11_catalogue_ablation/19_catalogue_ablation_20261029T051109Z/`。历史文件中的旧执行路径保留作来源，本次导航统一指向实验室。
- 周志：[ EXP-2026W44-017 ](../../LOGS/2026-W44.md#exp-2026w44-017)。同一批次已有摘要/续接副本不新增实验计数。

## 做了什么与得到什么

检验目录呈现对实际 Agent 请求成本和结果的影响。

两条件各 15 个逻辑案例，29 次 native；projected 5/15、full 6/15；输入下降 80.20%、total 79.01%，另有 10 API-only replay。

## 解释边界与失败记录

判定：**部分**。规划失败仍在分母中；目录变化还影响语义，不证明同等质量或闭环提速。

## 复现与证据定位

本次只读取与离线复算；历史 runner、日志、协议、依赖指纹保留在下列原件。不同阶段的补丁和环境不能用一个背景 commit 替代。未明确记录的 seed、硬件或启动命令保持未知，不从今天服务器配置倒推。

| 证据原件（实验室现址） | SHA256 |
|---|---|
| cases.csv（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/11_catalogue_ablation/19_catalogue_ablation_20261029T051109Z/cases.csv`） | `92ae7a2f0e4a28bbd630da7fcc78a48d927b2c0ddd40a4b87c4fa7cea2b67f1d` |
| protocol.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/11_catalogue_ablation/19_catalogue_ablation_20261029T051109Z/protocol.json`） | `ab59cf220a52e90d576ba062b9d031f7adc72c1fac89b9da36e612eec902c25c` |
| COMPLETION.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/11_catalogue_ablation/19_catalogue_ablation_20261029T051109Z/COMPLETION.json`） | `4b86a0a85d2b9c72b6caf043f3702731a95268b32fdcb4e8435169076861c9a5` |
| source-pins.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/11_catalogue_ablation/19_catalogue_ablation_20261029T051109Z/source-pins.json`） | `84cd57248c4e6a24f603108105cb71eb68c2e6fb4a1337b212a95d8b3904cbbf` |
| suite-report-v2.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/11_catalogue_ablation/19_catalogue_ablation_20261029T051109Z/suite-report-v2.json`） | `b1e62114bfce375ff097fad18b905454ac8a89e29cbc522c99892885f21b0a38` |
| report.launch.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/11_catalogue_ablation/19_catalogue_ablation_20261029T051109Z/report.launch.log`） | `a6677aaeb7e95d0515b66e01d33980be1e4786e2681ecb02b5182348f3db177b` |
| suite-report.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/11_catalogue_ablation/19_catalogue_ablation_20261029T051109Z/suite-report.json`） | `77150135aec400e3fda254d5faee479b5cfb6dc279816d556a74a2ed81c4c747` |
| video-manifest.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/11_catalogue_ablation/19_catalogue_ablation_20261029T051109Z/video-manifest.json`） | `a95cdf40be33a824e4495b6991b33fd512492b9709d0184577413630d82ffa52` |
| archive-manifest.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/11_catalogue_ablation/19_catalogue_ablation_20261029T051109Z/archive-manifest.json`） | `40b777727442dae5e43e35a9e59fa18fb41a888451dc0ab77e846b0d24ffbd8e` |
| controller-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/11_catalogue_ablation/19_catalogue_ablation_20261029T051109Z/controller-status.json`） | `6b84622eb7e83504831020f93e93782275464c7031eebaa5c80b6a8b98d0090d` |
| experiment-summary.txt（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/11_catalogue_ablation/19_catalogue_ablation_20261029T051109Z/experiment-summary.txt`） | `18fb471821a336bb4859eca8b8811c7c9f48f653564d9cbcf3804525de5a5118` |
| finalization-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/11_catalogue_ablation/19_catalogue_ablation_20261029T051109Z/finalization-status.json`） | `b6cb3ec25f5cf2dc6b2396d3329cee21014f4d2a213b409d86b88b870ec193fe` |
| experiment-summary-v2.txt（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/11_catalogue_ablation/19_catalogue_ablation_20261029T051109Z/experiment-summary-v2.txt`） | `5d38b6afc82b36a202590c1d451663e5127daf1f64e1a587747130fcb53e14a7` |
| experiment-summary-zh.txt（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/11_catalogue_ablation/19_catalogue_ablation_20261029T051109Z/experiment-summary-zh.txt`） | `88e852a6e0cef2994341bc80397a690116cb4baa3d049f52747ddbe2e42e4f92` |
| r1_layout01_projected/native-result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/11_catalogue_ablation/19_catalogue_ablation_20261029T051109Z/r1_layout01_projected/native-result.json`） | `8ae6a937232fc1b8c6d1e3b297a60df76889c266a3fa45274dc4e42ae609b509` |
| r1_layout01_unprojected/native-result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/11_catalogue_ablation/19_catalogue_ablation_20261029T051109Z/r1_layout01_unprojected/native-result.json`） | `8ae6a937232fc1b8c6d1e3b297a60df76889c266a3fa45274dc4e42ae609b509` |
| r1_layout01_projected/api/call-001-response.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/11_catalogue_ablation/19_catalogue_ablation_20261029T051109Z/r1_layout01_projected/api/call-001-response.json`） | `54f7c3c0d2009d423ebb7ce328f4e8ce471585cc0cf45ab25714e18c734f6bc4` |
| r1_layout01_unprojected/api/call-001-response.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/11_catalogue_ablation/19_catalogue_ablation_20261029T051109Z/r1_layout01_unprojected/api/call-001-response.json`） | `514285517ba34fefb42c2833915117f9cdae9ce10617ae1c3c8cb9051c10e35e` |
| analysis-sources/analyze_catalogue_payload.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/11_catalogue_ablation/19_catalogue_ablation_20261029T051109Z/analysis-sources/analyze_catalogue_payload.py`） | `b6294f435627ef2e48354502fee4b4ae9040360e91a97be83783c2bb54863367` |
| analysis-sources/cloud_catalogue_analysis_corrections.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/11_catalogue_ablation/19_catalogue_ablation_20261029T051109Z/analysis-sources/cloud_catalogue_analysis_corrections.py`） | `539f385db7cd28a97f334d11375e067a15f9b2b53c0a390738243dbb7a61a3ac` |
| analysis-sources/cloud_catalogue_archive.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/11_catalogue_ablation/19_catalogue_ablation_20261029T051109Z/analysis-sources/cloud_catalogue_archive.py`） | `fbac39349b7c5536ac697be8e7d91df80e58cdf039712011a1fbb1121d57e6c7` |

### 原协议中可直接定位的字段

来源 `result/11_catalogue_ablation/19_catalogue_ablation_20261029T051109Z/protocol.json`：
- `registered_utc` = `2026-10-29T05:11:09.095457+00:00`
- `task` = `general_pickup`
- `model` = `qwen3.7-plus`
- `enable_thinking` = `True`
- `seed` = `0`


### 本次独立离线复算

`core-metric-verification.json` 中的 `catalogue` 已通过。原始数据、使用字段和逐源 SHA256 均保留；未重新请求模型或重跑仿真。

```json
{
  "projected": {
    "logical_cases": 15,
    "native_completed": 15,
    "successes": 5,
    "input_tokens_mean": 11550.8,
    "total_tokens_mean": 12437.866666666667
  },
  "unprojected": {
    "logical_cases": 15,
    "native_completed": 14,
    "successes": 6,
    "input_tokens_mean": 58336.8,
    "total_tokens_mean": 59264.666666666664
  }
}
```

## 阅读覆盖与下一步

本单元 1503 个可读普通文件、1013 种不同字节内容已完整读入并校验；逐文件清单见 审计账本（原始归档位置：`../../evidence/readthrough_20261102/file-review-ledger.jsonl.gz`），按 `HIST-029` 检索。JSON/日志/代码等做对应结构分析，重点协议、结果、失败和计量证据用于本条解释；这不声称所有依赖副本逐行人工精读，或全部视频逐帧人工审片。

下一步：本阶段记录封存至 11 月 2 日结束。后续实验另登记；如需补证，先定位本条限制对应原件，不自动重跑。
