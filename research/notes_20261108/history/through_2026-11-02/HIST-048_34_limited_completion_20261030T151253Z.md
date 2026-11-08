# HIST-048 · 扩展任务与独立最终验收

- 历史记录范围（北京时间）：2026-10-30T23:12:53.077386+08:00 至 2026-10-31T07:40:57.321264+08:00。
- 时间依据：original structured timestamp fields; observed record range is not necessarily physical rollout duration
- 本次回溯补录：2026-11-05 11:40，不是重跑日期。
- 类型：`native_comparison`；原批次：`34_limited_completion_20261030T151253Z`。
- 原件现址：`/mnt/data/joey_tr/physical-RSI/result/19_extended_tasks_final_acceptance/34_limited_completion_20261030T151253Z/`。历史文件中的旧执行路径保留作来源，本次导航统一指向实验室。
- 周志：[ EXP-2026W44-004 ](../../LOGS/2026-W44.md#exp-2026w44-004)。同一批次已有摘要/续接副本不新增实验计数。

## 做了什么与得到什么

检验保留策略和其他技能在登记的新布局上的表现。

保留 pi05 两分类各 0/10；扩展正式 stack_bowls 1/5、cover_blocks 3/5、insert_tubes 4/5；3 smoke+15 formal+20 final=38 次计入本批，18 HTTP共228561 Token。

## 解释边界与失败记录

判定：**部分**。最终验收对象是 pi05，不是整个 Agent；扩展成绩与分类分母分开。

## 复现与证据定位

本次只读取与离线复算；历史 runner、日志、协议、依赖指纹保留在下列原件。不同阶段的补丁和环境不能用一个背景 commit 替代。未明确记录的 seed、硬件或启动命令保持未知，不从今天服务器配置倒推。

| 证据原件（实验室现址） | SHA256 |
|---|---|
| protocol.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/19_extended_tasks_final_acceptance/34_limited_completion_20261030T151253Z/protocol.json`） | `38febc8dd21271f7430ea8b39c044d8c378d23880f50087cf17ec94beb6624bc` |
| completion.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/19_extended_tasks_final_acceptance/34_limited_completion_20261030T151253Z/completion.json`） | `f93f75669a83e646ca566fb91b86216b37ee5b2485303c500b28f7e571988637` |
| final-test/protocol.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/19_extended_tasks_final_acceptance/34_limited_completion_20261030T151253Z/final-test/protocol.json`） | `0b8d5cf5aafaf115a293ef185c70dc3841a22caa8ae0faad5f782ab7d911dc47` |
| final-test/completion.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/19_extended_tasks_final_acceptance/34_limited_completion_20261030T151253Z/final-test/completion.json`） | `137b2dc77e8b497a4805ef53a6ea3eb6c33befd493ec832605f54498f635e468` |
| final-review/completion.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/19_extended_tasks_final_acceptance/34_limited_completion_20261030T151253Z/final-review/completion.json`） | `2b7722328c4ea0f5e7e73895b67ddc77a9a7138f0bbc107fa6505d036435a492` |
| cover-layout-check/selection.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/19_extended_tasks_final_acceptance/34_limited_completion_20261030T151253Z/cover-layout-check/selection.json`） | `e1dc69f37c29548cf744b250a7397db76ac74c52e2c87348d0e1acdf6c841cb7` |
| analysis-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/19_extended_tasks_final_acceptance/34_limited_completion_20261030T151253Z/analysis-status.json`） | `69564fa0d5274de0b7554ffc7d4827bec995aa3cb5576581c1f83a42ff35dbf9` |
| extended-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/19_extended_tasks_final_acceptance/34_limited_completion_20261030T151253Z/extended-status.json`） | `6c567c714fbf2dbe7cb171b8cf812a0efdbf4a62228a48feadb54665b615cafc` |
| pipeline-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/19_extended_tasks_final_acceptance/34_limited_completion_20261030T151253Z/pipeline-status.json`） | `6b51fa73ab445bd533a574155644615911a9ac8eb04791df8b707490598452cc` |
| preparation-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/19_extended_tasks_final_acceptance/34_limited_completion_20261030T151253Z/preparation-status.json`） | `ad679d0396a598f9c7be077e376982b6e4d8df684f25813ed11ddc0f11dee60f` |
| critical-review-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/19_extended_tasks_final_acceptance/34_limited_completion_20261030T151253Z/critical-review-status.json`） | `6c6bb0ae92c55fad03d67b9e59607ac5ab91674629663e4f178193928335f56c` |
| smoke-controller-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/19_extended_tasks_final_acceptance/34_limited_completion_20261030T151253Z/smoke-controller-status.json`） | `a05f153ca9448f31b2878a999e5a65f40dbb7843660a8e64183247c7a4382cb1` |
| formal-controller-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/19_extended_tasks_final_acceptance/34_limited_completion_20261030T151253Z/formal-controller-status.json`） | `35f022c655dda97ac79613cc924b8484fddd76ed4dc2f4e90b0891802889a5f1` |
| reproduction-verification.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/19_extended_tasks_final_acceptance/34_limited_completion_20261030T151253Z/reproduction-verification.json`） | `f61330cf26ff02f073fd3e228d013b8b285e9e9b8f357b84db3b6eee38544f0e` |
| formal_cover_blocks/native-result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/19_extended_tasks_final_acceptance/34_limited_completion_20261030T151253Z/formal_cover_blocks/native-result.json`） | `18d087c53955750abba341fa1aa227f498be4fb14d32611dab3802a2ce05c6da` |
| formal_insert_tubes/native-result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/19_extended_tasks_final_acceptance/34_limited_completion_20261030T151253Z/formal_insert_tubes/native-result.json`） | `6fcd536cc76f89b7c7383c141160309eb555defcd2f519bc389ade8b7fa099e2` |
| formal_cover_blocks/api/call-001-response.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/19_extended_tasks_final_acceptance/34_limited_completion_20261030T151253Z/formal_cover_blocks/api/call-001-response.json`） | `bf0a66568d1cbdf4a35acadddfa4dc81247aeacc610eeedc3f5c7dc0af0d91ed` |
| formal_cover_blocks/api/call-002-response.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/19_extended_tasks_final_acceptance/34_limited_completion_20261030T151253Z/formal_cover_blocks/api/call-002-response.json`） | `7f5d17a378488e15b5f725913dc7b67f629c0cd68aa035edf511f771ccb9c513` |
| analysis-sources/cloud_comparison_native.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/19_extended_tasks_final_acceptance/34_limited_completion_20261030T151253Z/analysis-sources/cloud_comparison_native.py`） | `8eed3ac4ff2a73ca1ead2b913a37cea61f846fbafe8ac8c5cdda084e5801c9c1` |
| analysis-sources/cloud_comparison_policy.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/19_extended_tasks_final_acceptance/34_limited_completion_20261030T151253Z/analysis-sources/cloud_comparison_policy.py`） | `6258f5b98d699ed454b6a7d174602ff5ab17a3d3a717f4a2f3af95b19be73217` |
| analysis-sources/cloud_comparison_run.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/19_extended_tasks_final_acceptance/34_limited_completion_20261030T151253Z/analysis-sources/cloud_comparison_run.py`） | `9e71612eb173f26cc8551e951916c2e78580641f502efc29f6b8dc77331294dc` |

### 原协议中可直接定位的字段

来源 `result/19_extended_tasks_final_acceptance/34_limited_completion_20261030T151253Z/protocol.json`：
- `registered_utc` = `2026-10-30T15:12:53.077386+00:00`

来源 `result/19_extended_tasks_final_acceptance/34_limited_completion_20261030T151253Z/final-test/protocol.json`：
- `registered_utc` = `2026-10-30T15:16:45.836011+00:00`


### 本次独立离线复算

`core-metric-verification.json` 中的 `pi05_independent_final` 已通过。原始数据、使用字段和逐源 SHA256 均保留；未重新请求模型或重跑仿真。

```json
{
  "n": 20,
  "successes": 0,
  "all_scores_zero": true
}
```

## 阅读覆盖与下一步

本单元 24603 个可读普通文件、1640 种不同字节内容已完整读入并校验；逐文件清单见 [审计账本](../../evidence/readthrough_20261102/file-review-ledger.jsonl.gz)，按 `HIST-048` 检索。JSON/日志/代码等做对应结构分析，重点协议、结果、失败和计量证据用于本条解释；这不声称所有依赖副本逐行人工精读，或全部视频逐帧人工审片。

下一步：本阶段记录封存至 11 月 2 日结束。后续实验另登记；如需补证，先定位本条限制对应原件，不自动重跑。
