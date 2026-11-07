# HIST-045 · System 2 两轮完成与选择

- 历史记录范围（北京时间）：2026-10-30T20:09:59.787382+08:00 至 2026-10-30T20:56:30.504455+08:00。
- 时间依据：original structured timestamp fields; observed record range is not necessarily physical rollout duration
- 本次回溯补录：2026-11-05 11:40，不是重跑日期。
- 类型：`system2`；原批次：`31_system2_final_validation_20261030T121000Z`。
- 原件现址：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/31_system2_final_validation_20261030T121000Z/`。历史文件中的旧执行路径保留作来源，本次导航统一指向实验室。
- 周志：[ EXP-2026W44-003 ](../../LOGS/2026-W44.md#exp-2026w44-003)。同一批次已有摘要/续接副本不新增实验计数。

## 做了什么与得到什么

核实正式两轮父/候选验证和保留项。

两轮父/候选各 5 个验证布局均 0 分、0 成功，均 retain_parent；40 逻辑开发/验证中续接复用 30、新执行10，正式提案总51070 Token。

## 解释边界与失败记录

判定：**Y**。四个唯一提案含接入/失败总405876 Token，子集不能再次相加；流程完成没有带来任务增益。

续接工作区、候选响应复用和物理 dispatch 应按来源 ID/哈希分别核对。中断成本保留；没有有效最终评分的尝试标为未知。不能将各目录摘要中的累计数相加为全局新实验数。

## 复现与证据定位

本次只读取与离线复算；历史 runner、日志、协议、依赖指纹保留在下列原件。不同阶段的补丁和环境不能用一个背景 commit 替代。未明确记录的 seed、硬件或启动命令保持未知，不从今天服务器配置倒推。

| 证据原件（实验室现址） | SHA256 |
|---|---|
| protocol.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/31_system2_final_validation_20261030T121000Z/protocol.json`） | `f6a5b2a276a3c91c5cb9df41e6b969129ee1528aacd632282970474623e24b3f` |
| workspace/rounds/round-000000/selection.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/31_system2_final_validation_20261030T121000Z/workspace/rounds/round-000000/selection.json`） | `530114c2bb4d7aabdea5fcf7f225f6c12b01b8533ef1e47058c85732f44bc083` |
| step5-results.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/31_system2_final_validation_20261030T121000Z/step5-results.json`） | `82be03b9722d725af5048a648d563abc82002a87bd61858bbe5a873381e8b73d` |
| postrun-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/31_system2_final_validation_20261030T121000Z/postrun-status.json`） | `74aed8fa4b358d6b89eeff1528dc5f3cc5e6b340c5a615ee83ccc2fa50f56347` |
| round-00-result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/31_system2_final_validation_20261030T121000Z/round-00-result.json`） | `eb677430f0da342a9cfe55e00d945820eeba08971c7d9c261d210bd8af35c306` |
| iteration-result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/31_system2_final_validation_20261030T121000Z/iteration-result.json`） | `bdf7930c315c2a3dde82baa84c1d1bc7fa5e37238ed656f791ea65ee10761d14` |
| controller-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/31_system2_final_validation_20261030T121000Z/controller-status.json`） | `004411e240a73a2821d28ff5e11d0ba786b48eed929f9f89cae6b28273a9e59a` |
| reused-offline-gate-verification.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/31_system2_final_validation_20261030T121000Z/reused-offline-gate-verification.json`） | `aa71b6d67e53f912d4c9464ea381ce2359e583c2d7afd3be2591efb23191d7b5` |
| final-audit/verification.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/31_system2_final_validation_20261030T121000Z/final-audit/verification.json`） | `adb88f9b0989eee30088be21bada3b00cb80bc608ade9c8fa1948ef0d1a4a776` |
| workspace/rounds/round-000000/development-results.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/31_system2_final_validation_20261030T121000Z/workspace/rounds/round-000000/development-results.json`） | `c58e6ccc02010f3c778903a9a63a6f98e166a7095a836da59272dd0b348d117f` |
| workspace/rounds/round-000000/validation-layouts/generated/manifest.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/31_system2_final_validation_20261030T121000Z/workspace/rounds/round-000000/validation-layouts/generated/manifest.json`） | `4a24ac7df6e060d036491e4aba9d8ad9fc4be7bf27f1df793bc96f13e96eba3a` |
| workspace/rounds/round-000000/development-layouts/generated/manifest.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/31_system2_final_validation_20261030T121000Z/workspace/rounds/round-000000/development-layouts/generated/manifest.json`） | `22cb0623385cdc73d4187597f0168c2cfd49b69902206d34a5fe76aa8af2b024` |
| workspace/rounds/round-000000/proposals/classify_objects/cpu-contract-gate/gate-result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/31_system2_final_validation_20261030T121000Z/workspace/rounds/round-000000/proposals/classify_objects/cpu-contract-gate/gate-result.json`） | `c7afc275b4c4c1a3da0ab4478c7562b0997164cce5b3521f88dfdddef1d5ee48` |
| workspace/rounds/round-000000/proposals/classify_objects/cpu-contract-gate/empty/result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/31_system2_final_validation_20261030T121000Z/workspace/rounds/round-000000/proposals/classify_objects/cpu-contract-gate/empty/result.json`） | `38e0b9de817f645c4bec37c0d4a3e58baecccb040f5718dc069a72c7385a0bed` |
| procedure-sources/step5_feedback.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/31_system2_final_validation_20261030T121000Z/procedure-sources/step5_feedback.py`） | `822132f0e6f16fe0b4d26df48dcd80bb73f99c91d77a0aa4d97227113d700ef6` |
| procedure-sources/step5_final_audit.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/31_system2_final_validation_20261030T121000Z/procedure-sources/step5_final_audit.py`） | `0f7903bd5f8589b8fb62724f061a28244921306693b415704c8ff4fe9bf35644` |
| procedure-sources/step5_final_finish.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/17_system2_iterations/31_system2_final_validation_20261030T121000Z/procedure-sources/step5_final_finish.py`） | `af8d883c5bc3da01f283c91595cd89dac065f5580af332e444ada249f355b41f` |

### 原协议中可直接定位的字段

来源 `result/17_system2_iterations/31_system2_final_validation_20261030T121000Z/protocol.json`：
- `automatic_http_retries` = `0`
- `collect_interval` = `10`
- `control_dt` = `0.04`
- `model_profile.enable_thinking` = `True`
- `model_profile.model` = `qwen3.7-plus`
- `registered_utc` = `2026-10-30T12:09:59.787382+00:00`
- `task` = `classify_objects`

来源 `result/17_system2_iterations/31_system2_final_validation_20261030T121000Z/workspace/rounds/round-000000/validation-layouts/generated/manifest.json`：
- `seed` = `1290156389136020199`

来源 `result/17_system2_iterations/31_system2_final_validation_20261030T121000Z/workspace/rounds/round-000000/development-layouts/generated/manifest.json`：
- `seed` = `663050387014311974`


### 本次独立离线复算

`core-metric-verification.json` 中的 `system2_two_formal_selections` 已通过。原始数据、使用字段和逐源 SHA256 均保留；未重新请求模型或重跑仿真。

```json
{
  "selections": [
    {
      "path": "result/17_system2_iterations/29_system2_api_20261030T101800Z/workspace/rounds/round-000000/selection.json",
      "decision": "retain_parent",
      "metrics": {
        "candidate_round-000000": {
          "normalized_score": 0.0,
          "per_task": {
            "classify_objects": 0.0
          },
          "success_rate": {
            "classify_objects": 0.0
          }
        },
        "initial": {
          "normalized_score": 0.0,
          "per_task": {
            "classify_objects": 0.0
          },
          "success_rate": {
            "classify_objects": 0.0
          }
        }
      }
    },
    {
      "path": "result/17_system2_iterations/31_system2_final_validation_20261030T121000Z/workspace/rounds/round-000000/selection.json",
      "decision": "retain_parent",
      "metrics": {
        "candidate_round-000000": {
          "normalized_score": 0.0,
          "per_task": {
            "classify_objects": 0.0
          },
          "success_rate": {
            "classify_objects": 0.0
          }
        },
        "initial": {
          "normalized_score": 0.0,
          "per_task": {
            "classify_objects": 0.0
          },
          "success_rate": {
            "classify_objects": 0.0
          }
        }
      }
    }
  ],
  "note": "Distinct formal-round selections in continuation lineage; duplicated workspace copies are not added."
}
```

## 阅读覆盖与下一步

本单元 25049 个可读普通文件、1526 种不同字节内容已完整读入并校验；逐文件清单见 审计账本（原始归档位置：`../../evidence/readthrough_20261102/file-review-ledger.jsonl.gz`），按 `HIST-045` 检索。JSON/日志/代码等做对应结构分析，重点协议、结果、失败和计量证据用于本条解释；这不声称所有依赖副本逐行人工精读，或全部视频逐帧人工审片。

下一步：本阶段记录封存至 11 月 2 日结束。后续实验另登记；如需补证，先定位本条限制对应原件，不自动重跑。
