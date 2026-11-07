# HIST-059 · 老手模式初始化与历史摘要导入

- 历史记录范围（北京时间）：2026-11-01 至 2026-11-01。
- 时间依据：来源：原记录日期/登记目录；不把文件传输时间当实验开始时间。
- 本次回溯补录：2026-11-05 11:40，不是重跑日期。
- 类型：`administration`；原批次：`research_tool_initialization_20261101T120523Z`。
- 原件现址：`/mnt/data/joey_tr/physical-RSI/result/research_tool_initialization_20261101T120523Z/`。历史文件中的旧执行路径保留作来源，本次导航统一指向实验室。
- 周志性质：协议、准备、审计或管理节点，未作为新的物理实验累计。

## 做了什么与得到什么

依据用户确认建立已有阶段的研究档案。

expert 模式、43条历史批次、4组代表摘要、52个记录文件及原模板备份完成。

## 解释边界与失败记录

判定：**N**。四组摘要不是全部实验；本轮逐文件审计用来补齐详细记录。

## 复现与证据定位

本次只读取与离线复算；历史 runner、日志、协议、依赖指纹保留在下列原件。不同阶段的补丁和环境不能用一个背景 commit 替代。未明确记录的 seed、硬件或启动命令保持未知，不从今天服务器配置倒推。

| 证据原件（实验室现址） | SHA256 |
|---|---|
| status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/research_tool_initialization_20261101T120523Z/status.json`） | `14874dc8a0ee9a95123a7e435f9cf5aa477488c8c44bf31f40cd81740a88ea64` |
| initialized_manifest.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/research_tool_initialization_20261101T120523Z/initialized_manifest.json`） | `e5832bcf0296c644ca85627543ebd39d5e93469e3ca9b7ad987ef26c222a45f1` |
| commands.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/research_tool_initialization_20261101T120523Z/commands.json`） | `8fb522d9c39ed44b94134a103fc304a4cb6d496674b9f94a6160d95ecb885eed` |
| 08_new_exp.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/research_tool_initialization_20261101T120523Z/08_new_exp.log`） | `1fc56862d7da1867cfaf47a12e2d85481e689e50e48cbfe39eaa67d24aa75427` |
| 09_new_exp.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/research_tool_initialization_20261101T120523Z/09_new_exp.log`） | `757547ad72981f206df3ac861f02c5409e4be59567308911af37112e3da3550a` |
| 10_new_exp.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/research_tool_initialization_20261101T120523Z/10_new_exp.log`） | `c996d19de997d8467f2f361b790c10ff5adbbe0e280ef521460abeb6f8295e9c` |
| 11_new_exp.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/research_tool_initialization_20261101T120523Z/11_new_exp.log`） | `31c3be4fc21830439a31962c8ac8521ea2070010f602529b7a6c9f17efb5c29f` |
| 06_new_disc.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/research_tool_initialization_20261101T120523Z/06_new_disc.log`） | `fff9ed5204967f0786b5b30a5638a2d1d3cbde3ba30d1807986acce5d5d541a1` |
| 07_new_week.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/research_tool_initialization_20261101T120523Z/07_new_week.log`） | `c3a8dc6583a672a84ba05fc38517ed2b81d9b6546bc32c7e0f835d07a8a491b2` |
| 16_timeline.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/research_tool_initialization_20261101T120523Z/16_timeline.log`） | `1e431be4d68f6c48f8486284a01dc9f6e5ba4671dfa6adfd67f2ceb2184544af` |
| 17_timeline.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/research_tool_initialization_20261101T120523Z/17_timeline.log`） | `12600474674e4be0bb99c77e004cd3a8fd9af385ea69fa10cfb85bed46dc641f` |
| 22_timeline.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/research_tool_initialization_20261101T120523Z/22_timeline.log`） | `80c584341a23dcd251587ef0b29d41a93d1ecfe403dbc0e868f1c99304b25bd8` |
| 19_eli5_sync.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/research_tool_initialization_20261101T120523Z/19_eli5_sync.log`） | `dc489d0b46e782efa16bdd5a14478208c9399c632a373c09f1929b2e857d1f52` |
| 21_eli5_sync.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/research_tool_initialization_20261101T120523Z/21_eli5_sync.log`） | `1d66024c01efea6a11fb860f795fcdf915c2b737d8288711833fd96ce13de2fb` |

## 阅读覆盖与下一步

本单元 65 个可读普通文件、64 种不同字节内容已完整读入并校验；逐文件清单见 审计账本（原始归档位置：`../../evidence/readthrough_20261102/file-review-ledger.jsonl.gz`），按 `HIST-059` 检索。JSON/日志/代码等做对应结构分析，重点协议、结果、失败和计量证据用于本条解释；这不声称所有依赖副本逐行人工精读，或全部视频逐帧人工审片。

下一步：本阶段记录封存至 11 月 2 日结束。后续实验另登记；如需补证，先定位本条限制对应原件，不自动重跑。
