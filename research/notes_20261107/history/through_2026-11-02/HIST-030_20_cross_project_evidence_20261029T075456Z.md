# HIST-030 · 公开项目对照与早期分类计量

- 历史记录范围（北京时间）：2026-10-29T16:02:20.375744+08:00 至 2026-10-29T17:03:21.492892+08:00。
- 时间依据：original structured timestamp fields; observed record range is not necessarily physical rollout duration
- 本次回溯补录：2026-11-05 11:40，不是重跑日期。
- 类型：`comparison`；原批次：`20_cross_project_evidence_20261029T075456Z`。
- 原件现址：`/mnt/data/joey_tr/physical-RSI/result/12_cross_project_measurement/20_cross_project_evidence_20261029T075456Z/`。历史文件中的旧执行路径保留作来源，本次导航统一指向实验室。
- 周志：[ EXP-2026W44-018 ](../../LOGS/2026-W44.md#exp-2026w44-018)。同一批次已有摘要/续接副本不新增实验计数。

## 做了什么与得到什么

固定公开 A 证据并测量 B 两个分类任务。

公开 100 条结果及固定源码留存；B 初版冷/连续运行中有格式与执行失败，后续由 closing 批次补齐。

## 解释边界与失败记录

判定：**部分**。A 不重跑；累计 usage、动作段和实际 HTTP 是不同量，初版 complete=false 的状态不能被最终归档状态覆盖。

## 复现与证据定位

本次只读取与离线复算；历史 runner、日志、协议、依赖指纹保留在下列原件。不同阶段的补丁和环境不能用一个背景 commit 替代。未明确记录的 seed、硬件或启动命令保持未知，不从今天服务器配置倒推。

| 证据原件（实验室现址） | SHA256 |
|---|---|
| protocol.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/12_cross_project_measurement/20_cross_project_evidence_20261029T075456Z/protocol.json`） | `dfe989bcb67364ef055aa649fd59c10c54c805ef7580178243d2b894a1e9e665` |
| COMPLETION.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/12_cross_project_measurement/20_cross_project_evidence_20261029T075456Z/COMPLETION.json`） | `971c2665c59c694ff2754fe64ff59c59efb248a362a03bc1bd9392a4fca893a2` |
| final-report.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/12_cross_project_measurement/20_cross_project_evidence_20261029T075456Z/final-report.log`） | `aad300f6a7c702aa11a91df0e6e82f27b7ab90733c86b54f1c8cade8d6d5d658` |
| partial-report.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/12_cross_project_measurement/20_cross_project_evidence_20261029T075456Z/partial-report.log`） | `b3c71d6ed4dd4f691fd7ca26ba87441e49e732faae68665b2cc0b0814226be91` |
| analysis-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/12_cross_project_measurement/20_cross_project_evidence_20261029T075456Z/analysis-status.json`） | `59fa85759478f276461f5cfdab2221af767a02ee8aa225fc3061228b8375c903` |
| archive-manifest.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/12_cross_project_measurement/20_cross_project_evidence_20261029T075456Z/archive-manifest.json`） | `c22da9676b200179929b11bf03b79f1cd944e8a2321a505051b30021f970fa8f` |
| controller-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/12_cross_project_measurement/20_cross_project_evidence_20261029T075456Z/controller-status.json`） | `4d24eee571aac4c8a3f80c8b4575a522e4cc67972d0cc16e81d6537b26988db8` |
| existing-b-summary.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/12_cross_project_measurement/20_cross_project_evidence_20261029T075456Z/existing-b-summary.json`） | `6c2c76cebcaa1d24e1d63f372a78a3ef48c89316b8b7e364afe0e396d807c463` |
| preparation-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/12_cross_project_measurement/20_cross_project_evidence_20261029T075456Z/preparation-status.json`） | `985a90eec1edb4e1d3dfa100d06fe790d2de6f7885787fd54dd6edb0584f63bd` |
| finalization-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/12_cross_project_measurement/20_cross_project_evidence_20261029T075456Z/finalization-status.json`） | `b298dc483f95937ca47ad428f0e3d2be700bff0866b62695da7f614d960d8c19` |
| controller-v2-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/12_cross_project_measurement/20_cross_project_evidence_20261029T075456Z/controller-v2-status.json`） | `9062495fe7fc96795d690c73b16745ea9c723fa452557b162bb8c887f0c6693e` |
| cross-project-report.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/12_cross_project_measurement/20_cross_project_evidence_20261029T075456Z/cross-project-report.json`） | `14ff7190f099391a9fb1abbb15153f6143e1b67d13667b045ba1cd0c4858024b` |
| cross-project-report-zh.md（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/12_cross_project_measurement/20_cross_project_evidence_20261029T075456Z/cross-project-report-zh.md`） | `ed23e4e66811d17f9da025d15b9aad563349a334b8884303a62093798334bc64` |
| final-findings-manifest.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/12_cross_project_measurement/20_cross_project_evidence_20261029T075456Z/final-findings-manifest.json`） | `f13587d37923d34fa4eb41bc99a979d70af11ae9fac1b8f314df2261dde76ffb` |
| classify_objects_by_language_cold_l0/native-result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/12_cross_project_measurement/20_cross_project_evidence_20261029T075456Z/classify_objects_by_language_cold_l0/native-result.json`） | `8c273ffc559ef02dc3afe12fa5576c3d7134ee39ff3b67f9c98dada9cd2b0358` |
| classify_objects_by_language_cold_l1/native-result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/12_cross_project_measurement/20_cross_project_evidence_20261029T075456Z/classify_objects_by_language_cold_l1/native-result.json`） | `f8226da9aafb10e942314b78b1f13f4ff00fcb85e07d0bca760dca783044bbb1` |
| classify_objects_by_language_cold_l0/api/call-001-response.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/12_cross_project_measurement/20_cross_project_evidence_20261029T075456Z/classify_objects_by_language_cold_l0/api/call-001-response.json`） | `7b7e027a67d6375416cb583c431a3d042a152e8bf72f4bcd3908f8267d2e38d0` |
| classify_objects_by_language_cold_l1/api/call-001-response.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/12_cross_project_measurement/20_cross_project_evidence_20261029T075456Z/classify_objects_by_language_cold_l1/api/call-001-response.json`） | `b9e4c6d8e7425b5e5c4ea60be2898d39bf867f0773faddca03a1173191985e44` |
| analysis-sources/cloud_comparison_audit.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/12_cross_project_measurement/20_cross_project_evidence_20261029T075456Z/analysis-sources/cloud_comparison_audit.py`） | `8e3c7bd3a04e12ef40ebc1847b3c73fa73e4f9f43c270b974884f5960d1699b1` |
| analysis-sources/cloud_comparison_controller.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/12_cross_project_measurement/20_cross_project_evidence_20261029T075456Z/analysis-sources/cloud_comparison_controller.py`） | `ae19a993e51ecffe82b5dfadb883f67524402162735095c738015bfbc1d082cd` |
| analysis-sources/cloud_comparison_controller_v2.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/12_cross_project_measurement/20_cross_project_evidence_20261029T075456Z/analysis-sources/cloud_comparison_controller_v2.py`） | `5a5ef3b713b557ad20d6149aa2ed8d2268259ec6e0951cce46158f4a144b3918` |

### 原协议中可直接定位的字段

来源 `result/12_cross_project_measurement/20_cross_project_evidence_20261029T075456Z/protocol.json`：
- `model` = `qwen3.7-plus`


## 阅读覆盖与下一步

本单元 4161 个可读普通文件、3967 种不同字节内容已完整读入并校验；逐文件清单见 审计账本（原始归档位置：`../../evidence/readthrough_20261102/file-review-ledger.jsonl.gz`），按 `HIST-030` 检索。JSON/日志/代码等做对应结构分析，重点协议、结果、失败和计量证据用于本条解释；这不声称所有依赖副本逐行人工精读，或全部视频逐帧人工审片。

下一步：本阶段记录封存至 11 月 2 日结束。后续实验另登记；如需补证，先定位本条限制对应原件，不自动重跑。
