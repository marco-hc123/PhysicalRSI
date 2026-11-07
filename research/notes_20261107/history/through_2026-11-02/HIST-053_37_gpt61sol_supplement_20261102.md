# HIST-053 · System 1 高层模型替换

- 历史记录范围（北京时间）：2026-11-02T08:44:50.922468+08:00 至 2026-11-02T09:25:43.469751+08:00。
- 时间依据：Original protocol registration and analysis timestamps; not episode wall-clock
- 本次回溯补录：2026-11-05 11:40，不是重跑日期。
- 类型：`model_swap`；原批次：`37_gpt61sol_supplement_20261102`。
- 原件现址：`/mnt/data/joey_tr/physical-RSI/result/24_system1_model_swap/37_gpt61sol_supplement_20261102/`。历史文件中的旧执行路径保留作来源，本次导航统一指向实验室。
- 周志：[ EXP-2026W45-001 ](../../LOGS/2026-W45.md#exp-2026w45-001)。同一批次已有摘要/续接副本不新增实验计数。

## 做了什么与得到什么

在既有技能调用结构下比较 Sol 与历史 Qwen 参考。

新增10正常回合；普通/语言分类1/5、2/5，平均total11661.6/11719.4；相同技能路由10/10；total下降7.48%/4.97%。

## 解释边界与失败记录

判定：**部分**。输入近似不变、输出缩短；模型/兼容参数同时变化，旧10行对照不计新执行。

## 复现与证据定位

本次只读取与离线复算；历史 runner、日志、协议、依赖指纹保留在下列原件。不同阶段的补丁和环境不能用一个背景 commit 替代。未明确记录的 seed、硬件或启动命令保持未知，不从今天服务器配置倒推。

| 证据原件（实验室现址） | SHA256 |
|---|---|
| protocol.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/24_system1_model_swap/37_gpt61sol_supplement_20261102/protocol.json`） | `7b961b6d46c0e274cccc50208357904e6db38f5aad5495d5b551a52625492693` |
| episode-results.csv（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/24_system1_model_swap/37_gpt61sol_supplement_20261102/episode-results.csv`） | `370f01db5afc8d10284ddec185580c963ebfbea4964e4b1f0add9761c78bbd4f` |
| analysis-summary.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/24_system1_model_swap/37_gpt61sol_supplement_20261102/analysis-summary.json`） | `913c10c39e15e827bd72bfb5dc7a7952c7fa63ab376caa11c4c78f90cdce7647` |
| group-results.csv（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/24_system1_model_swap/37_gpt61sol_supplement_20261102/group-results.csv`） | `ca4ef0ee6244653bc1457f5351b9f93154dce5612ff34b57fefea0675b041afe` |
| suite-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/24_system1_model_swap/37_gpt61sol_supplement_20261102/suite-status.json`） | `e73ead5fe6743b9cd2828613f744bb445299b79fa4b1fd4dccf157956e6036b3` |
| verification.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/24_system1_model_swap/37_gpt61sol_supplement_20261102/verification.json`） | `a68c6cc64994f788a15d7c1ce560826f6be90f8f441263bbbc063e1764ae3349` |
| file-manifest.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/24_system1_model_swap/37_gpt61sol_supplement_20261102/file-manifest.json`） | `5ef78c2bc0fc4338dc95c49c2742ac45b09153a7d8c2eeb28ba8b30aecc3c9fb` |
| analysis-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/24_system1_model_swap/37_gpt61sol_supplement_20261102/analysis-status.json`） | `0809a689d9f37eb3432c49740c387e7502359607026059dfaf7d03aaea75366d` |
| preparation-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/24_system1_model_swap/37_gpt61sol_supplement_20261102/preparation-status.json`） | `f954cbf55e5f6629fdb6e358356be5b489962ba408e4a69f2714c1e0b2a27b21` |
| evidence/gpt61sol_classify_objects_agent/status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/24_system1_model_swap/37_gpt61sol_supplement_20261102/evidence/gpt61sol_classify_objects_agent/status.json`） | `6d14d839d840df723b6b4125c6ea7122690efe38670d8acdedf801aadd1cbf06` |
| evidence/gpt61sol_classify_objects_agent/native-result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/24_system1_model_swap/37_gpt61sol_supplement_20261102/evidence/gpt61sol_classify_objects_agent/native-result.json`） | `4ebcbb1a25ebd67666f530964d93f1c2391c5542c2ce3f6223a05d4544e33089` |
| evidence/gpt61sol_classify_objects_agent/policy-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/24_system1_model_swap/37_gpt61sol_supplement_20261102/evidence/gpt61sol_classify_objects_agent/policy-status.json`） | `f3cb73a930a18c04211759d78262486cd48e1070d5ce7cf8ceaf9c7f864506a8` |
| evidence/gpt61sol_classify_objects_by_language_agent/status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/24_system1_model_swap/37_gpt61sol_supplement_20261102/evidence/gpt61sol_classify_objects_by_language_agent/status.json`） | `ce137ddde7fa38048fd3576116e6db66566c703dfb0d21fc00a9f59b080df7bd` |
| evidence/gpt61sol_classify_objects_by_language_agent/native-result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/24_system1_model_swap/37_gpt61sol_supplement_20261102/evidence/gpt61sol_classify_objects_by_language_agent/native-result.json`） | `81cbf18265a90e40a2fe6b09077faa5df99aaa33f11d1be8ef337642a15a99df` |
| evidence/gpt61sol_classify_objects_agent/api/call-001-response.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/24_system1_model_swap/37_gpt61sol_supplement_20261102/evidence/gpt61sol_classify_objects_agent/api/call-001-response.json`） | `750d89d8130996fa874d722dc14e7c761afe84afbd2c04a226f03c9f2a243e63` |
| evidence/gpt61sol_classify_objects_agent/api/call-002-response.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/24_system1_model_swap/37_gpt61sol_supplement_20261102/evidence/gpt61sol_classify_objects_agent/api/call-002-response.json`） | `ee26a59ad42d3726d57176ce7d3215b557248f978659b66a868834e894ae89a2` |
| sources/cloud_comparison_native.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/24_system1_model_swap/37_gpt61sol_supplement_20261102/sources/cloud_comparison_native.py`） | `8eed3ac4ff2a73ca1ead2b913a37cea61f846fbafe8ac8c5cdda084e5801c9c1` |
| sources/cloud_comparison_policy.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/24_system1_model_swap/37_gpt61sol_supplement_20261102/sources/cloud_comparison_policy.py`） | `7e723c54d1c47810940dc39b29988ec44b8786dcc23d53327024688a900db7d8` |
| sources/cloud_comparison_run.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/24_system1_model_swap/37_gpt61sol_supplement_20261102/sources/cloud_comparison_run.py`） | `40d5ad6fdf20d6541eeb0bb39cfe9bb1839ea3a251b9a09221dc6172d73d6c63` |

### 原协议中可直接定位的字段

来源 `result/24_system1_model_swap/37_gpt61sol_supplement_20261102/protocol.json`：
- `registered_utc` = `2026-11-02T00:44:50.922468+00:00`
- `model` = `gpt-6.1-sol`
- `reasoning_effort` = `medium`


### 本次独立离线复算

`core-metric-verification.json` 中的 `system1_sol` 已通过。原始数据、使用字段和逐源 SHA256 均保留；未重新请求模型或重跑仿真。

```json
{
  "groups": {
    "classify_objects": {
      "gpt61sol": {
        "n": 5,
        "input_tokens": 11545.0,
        "output_tokens": 116.6,
        "total_tokens": 11661.6,
        "score": 47.0,
        "api_seconds": 15.796895663800024,
        "reset_to_result_seconds": 229.41943272239996,
        "successes": 1
      },
      "qwen_reference": {
        "n": 5,
        "input_tokens": 11546.0,
        "output_tokens": 1058.0,
        "total_tokens": 12604.0,
        "score": 32.0,
        "api_seconds": 17.404910274199757,
        "reset_to_result_seconds": 236.53175448939982,
        "successes": 1
      }
    },
    "classify_objects_by_language": {
      "gpt61sol": {
        "n": 5,
        "input_tokens": 11587.8,
        "output_tokens": 131.6,
        "total_tokens": 11719.4,
        "score": 46.0,
        "api_seconds": 16.569807105400013,
        "reset_to_result_seconds": 212.05784546900003,
        "successes": 2
      },
      "qwen_reference": {
        "n": 5,
        "input_tokens": 11588.8,
        "output_tokens": 743.6,
        "total_tokens": 12332.4,
        "score": 30.0,
        "api_seconds": 12.265469193399985,
        "reset_to_result_seconds": 214.75510789399996,
        "successes": 1
      }
    }
  },
  "formal_http": 10,
  "formal_total_tokens": 116905,
  "smoke_total_tokens": 31,
  "old_reference_rows": 10
}
```

## 阅读覆盖与下一步

本单元 120 个可读普通文件、119 种不同字节内容已完整读入并校验；逐文件清单见 审计账本（原始归档位置：`../../evidence/readthrough_20261102/file-review-ledger.jsonl.gz`），按 `HIST-053` 检索。JSON/日志/代码等做对应结构分析，重点协议、结果、失败和计量证据用于本条解释；这不声称所有依赖副本逐行人工精读，或全部视频逐帧人工审片。

下一步：本阶段记录封存至 11 月 2 日结束。后续实验另登记；如需补证，先定位本条限制对应原件，不自动重跑。
