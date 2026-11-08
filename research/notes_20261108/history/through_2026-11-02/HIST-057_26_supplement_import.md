# HIST-057 · 四份补充 ZIP 导入与完整性核验

- 历史记录范围（北京时间）：2026-11-02 至 2026-11-02。
- 时间依据：来源：原记录日期/登记目录；不把文件传输时间当实验开始时间。
- 本次回溯补录：2026-11-05 11:40，不是重跑日期。
- 类型：`administration`；原批次：`26_supplement_import`。
- 原件现址：`/mnt/data/joey_tr/physical-RSI/result/26_supplement_import/`。历史文件中的旧执行路径保留作来源，本次导航统一指向实验室。
- 周志性质：协议、准备、审计或管理节点，未作为新的物理实验累计。

## 做了什么与得到什么

将11月2日两项补测原件归入实验室研究目录。

四份原ZIP和486成员保留，505传输成员验证，原43索引保留并扩至45；两套实验的结果包/工作包重复副本单列。

## 解释边界与失败记录

判定：**N**。导入本身 API/native/训练均0，所给包没有新执行视频；不能把四包说成四组实验。

## 复现与证据定位

本次只读取与离线复算；历史 runner、日志、协议、依赖指纹保留在下列原件。不同阶段的补丁和环境不能用一个背景 commit 替代。未明确记录的 seed、硬件或启动命令保持未知，不从今天服务器配置倒推。

| 证据原件（实验室现址） | SHA256 |
|---|---|
| 20261102T105827Z/status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/26_supplement_import/20261102T105827Z/status.json`） | `0e71e96f004c133827d3c98d1efd337005a47f9a04d37ec11ca9337934efc908` |
| 20261102T105827Z/payload_manifest.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/26_supplement_import/20261102T105827Z/payload_manifest.json`） | `20e76387511a6cd20f1f29bd9e034440ab89373cf7992010728cff35626c9c49` |
| [20261102T105827Z/final_verification.json](../../../../reports/research_week_20261102_20261108/06_batch_evidence/26_supplement_import/20261102T105827Z/final_verification.json) | `6733185c2f51b9ae8f6966ba15441f3242685ec2151d9099a0d944e86fc845f9` |
| [20261102T105827Z/initial_verification.json](../../../../reports/research_week_20261102_20261108/06_batch_evidence/26_supplement_import/20261102T105827Z/initial_verification.json) | `5a8fd9e142590e11c71825ce47b9b1214267aa9671b67c7fe91c810a2db7809c` |
| [20261102T105827Z/offline_verification.json](../../../../reports/research_week_20261102_20261108/06_batch_evidence/26_supplement_import/20261102T105827Z/offline_verification.json) | `6ae9a8ade3d0ea7b62ea73cb81b54facf46dc553340142e38b305fa5b262b79b` |
| [20261102T105827Z/payload-verification.json](../../../../reports/research_week_20261102_20261108/06_batch_evidence/26_supplement_import/20261102T105827Z/payload-verification.json) | `9a990584f6b6d6c6a04ccb20765749596d13ea02ddcfdfc8af6f1f41ad223332` |
| 20261102T105827Z/research_addendum_manifest.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/26_supplement_import/20261102T105827Z/research_addendum_manifest.json`） | `03fa4717eb2aa5031b6f0f4db1619b779197ee5262152097a3094147b43cc016` |
| 20261102T105827Z/before/research/history/index_status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/26_supplement_import/20261102T105827Z/before/research/history/index_status.json`） | `69028e932a7b5bee330bc2a3b069b02215f871c93878fb939d71e4037604c7cb` |
| 20261102T105827Z/before/research/history/result_inventory.csv（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/26_supplement_import/20261102T105827Z/before/research/history/result_inventory.csv`） | `86d2ad2479db39fa3f9a3a83b66258650b97f655f9b9fb29efdb6cfc7ada4ad9` |
| 阶段说明.txt（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/26_supplement_import/阶段说明.txt`） | `f334b81b36c2ca0844618fd6192b0d4ffc1441c1630949082a6ad658e4d25dc2` |
| 20261102T105827Z/preparation.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/26_supplement_import/20261102T105827Z/preparation.log`） | `0543788003262c511987d0de5a1a9df0430949adf6d2837ad7451aad176cc21d` |
| [20261102T105827Z/path-mapping.csv](../../../../reports/research_week_20261102_20261108/06_batch_evidence/26_supplement_import/20261102T105827Z/path-mapping.csv) | `a2b67fc8f124361f622f8428eb8df28dbe51ea0646d3dfe690057c860e805ab0` |
| 20261102T105827Z/registration.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/26_supplement_import/20261102T105827Z/registration.log`） | `9c219e45456d746e1697ba80f824f7fc7a23f93128b7770f481444450b916204` |
| 20261102T105827Z/before_hashes.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/26_supplement_import/20261102T105827Z/before_hashes.json`） | `72cff95e3417b40f10b622f824fcec2a99629b1dff10934f6b7f2ec2d8b77dee` |
| 20261102T105827Z/register_lab_import.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/26_supplement_import/20261102T105827Z/register_lab_import.py`） | `ea8b01b6f772506a975c81784c9ef9da4e46c13dcbcc9c9abb66eb88ff3de34d` |

## 阅读覆盖与下一步

本单元 33 个可读普通文件、33 种不同字节内容已完整读入并校验；逐文件清单见 [审计账本](../../evidence/readthrough_20261102/file-review-ledger.jsonl.gz)，按 `HIST-057` 检索。JSON/日志/代码等做对应结构分析，重点协议、结果、失败和计量证据用于本条解释；这不声称所有依赖副本逐行人工精读，或全部视频逐帧人工审片。

下一步：本阶段记录封存至 11 月 2 日结束。后续实验另登记；如需补证，先定位本条限制对应原件，不自动重跑。
