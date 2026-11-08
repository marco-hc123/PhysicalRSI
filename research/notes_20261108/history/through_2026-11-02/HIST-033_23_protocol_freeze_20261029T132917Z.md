# HIST-033 · 冻结 System 1 与 System 2 协议

- 历史记录范围（北京时间）：2026-10-29T21:29:46.614729+08:00 至 2026-10-29T21:33:36.496180+08:00。
- 时间依据：original structured timestamp fields; observed record range is not necessarily physical rollout duration
- 本次回溯补录：2026-11-05 11:40，不是重跑日期。
- 类型：`protocol`；原批次：`23_protocol_freeze_20261029T132917Z`。
- 原件现址：`/mnt/data/joey_tr/physical-RSI/result/14_protocol_freeze/23_protocol_freeze_20261029T132917Z/`。历史文件中的旧执行路径保留作来源，本次导航统一指向实验室。
- 周志性质：协议、准备、审计或管理节点，未作为新的物理实验累计。

## 做了什么与得到什么

固定任务、布局、控制预算、模型接口和选择规则。

两分类任务、4 路线×5 布局；seed=0、1100 控制步、0.04 秒；System 2 最多两轮，每轮一个候选，平分保留父策略。

## 解释边界与失败记录

判定：**N**。minimum_vla_score=0.6 是平均归一化部分分阈值，不是全任务成功率 60%。

## 复现与证据定位

本次只读取与离线复算；历史 runner、日志、协议、依赖指纹保留在下列原件。不同阶段的补丁和环境不能用一个背景 commit 替代。未明确记录的 seed、硬件或启动命令保持未知，不从今天服务器配置倒推。

| 证据原件（实验室现址） | SHA256 |
|---|---|
| protocol.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/14_protocol_freeze/23_protocol_freeze_20261029T132917Z/protocol.json`） | `ba90cca004a0839582405bad04e8fa2bb01c612eba4e8612edf4f13a3c62110c` |
| COMPLETION.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/14_protocol_freeze/23_protocol_freeze_20261029T132917Z/COMPLETION.json`） | `a35b770aaf3ec79e053b5793a04f2e123076d3cacd8e828b5e83f91f99cb7b4a` |
| status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/14_protocol_freeze/23_protocol_freeze_20261029T132917Z/status.json`） | `9a4751afc4c4dcacc30a5d4706fe5070fe7fedfe21e19cdffcb0f42acc150c67` |
| archive-manifest.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/14_protocol_freeze/23_protocol_freeze_20261029T132917Z/archive-manifest.json`） | `2dd7e480a23e3422a614e5ae2eecdb256c151f18fc60ca8142f5052a320bce1f` |
| final-verification.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/14_protocol_freeze/23_protocol_freeze_20261029T132917Z/final-verification.json`） | `a25ce137039686869b51b5260889ce54428bea7c34de34eba714f49b3dc5cadb` |
| freeze.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/14_protocol_freeze/23_protocol_freeze_20261029T132917Z/freeze.log`） | `826761e8406409d3cdb767c6e373d77a6e2e0fc1d474ed2f50e0ad43f7ae07c1` |
| launchers.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/14_protocol_freeze/23_protocol_freeze_20261029T132917Z/launchers.json`） | `b7591fdff2dae4d754e8aa55bbe31fc8b8d216372428d6f3039794a6ccafef48` |
| data-splits.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/14_protocol_freeze/23_protocol_freeze_20261029T132917Z/data-splits.json`） | `7eb5bb57d99bad4b22e712bd4638b38a239d94f66a42d4e988d55ac446f98ee8` |
| secret-scan.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/14_protocol_freeze/23_protocol_freeze_20261029T132917Z/secret-scan.json`） | `6de3a7e1f55b6b4e9d56c7a32577f02fd063ceff2c6846af26ccc217e0079891` |
| 工作顺序与第一步冻结说明.txt（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/14_protocol_freeze/23_protocol_freeze_20261029T132917Z/工作顺序与第一步冻结说明.txt`） | `0cefabb2c40de5ee619ca502bd55f8510576ed1937df93e9ff62db42a71ff464` |
| host-snapshot.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/14_protocol_freeze/23_protocol_freeze_20261029T132917Z/host-snapshot.json`） | `869f96b643ee524deba50602fdde82bcb7930dd364981bb19a8cd5610ef0348d` |
| source-freeze.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/14_protocol_freeze/23_protocol_freeze_20261029T132917Z/source-freeze.json`） | `010effc43b44bcdba50df48c5f69fad396dddf3de50e9380e699c5712791cc30` |
| policy-packages.txt（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/14_protocol_freeze/23_protocol_freeze_20261029T132917Z/policy-packages.txt`） | `33da6cf11b0c0792cedefea3350ea99ad5059ffc7a0f87996b184d3d7e314b8e` |
| skill-profiles.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/14_protocol_freeze/23_protocol_freeze_20261029T132917Z/skill-profiles.json`） | `1056f7cf7c23062f7f3e7ff8dff02a13375555ca430c218bdf83e2a188bd56c0` |
| analysis-sources/cloud_protocol_freeze.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/14_protocol_freeze/23_protocol_freeze_20261029T132917Z/analysis-sources/cloud_protocol_freeze.py`） | `b93c6a0d73ca9ec84fb2183d24ea9842fbb1c03eaaa46c2edd6dffa44af324ff` |

### 原协议中可直接定位的字段

来源 `result/14_protocol_freeze/23_protocol_freeze_20261029T132917Z/protocol.json`：
- `registered_utc` = `2026-10-29T13:29:46.614729+00:00`
- `seed` = `0`
- `collect_interval` = `10`
- `system2.task` = `classify_objects`


## 阅读覆盖与下一步

本单元 27 个可读普通文件、27 种不同字节内容已完整读入并校验；逐文件清单见 [审计账本](../../evidence/readthrough_20261102/file-review-ledger.jsonl.gz)，按 `HIST-033` 检索。JSON/日志/代码等做对应结构分析，重点协议、结果、失败和计量证据用于本条解释；这不声称所有依赖副本逐行人工精读，或全部视频逐帧人工审片。

下一步：本阶段记录封存至 11 月 2 日结束。后续实验另登记；如需补证，先定位本条限制对应原件，不自动重跑。
