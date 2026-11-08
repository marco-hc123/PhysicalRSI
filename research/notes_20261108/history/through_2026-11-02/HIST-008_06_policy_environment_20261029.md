# HIST-008 · H100 策略依赖环境准备

- 历史记录范围（北京时间）：2026-10-29 至 2026-10-29。
- 时间依据：来源：原记录日期/登记目录；不把文件传输时间当实验开始时间。
- 本次回溯补录：2026-11-05 11:40，不是重跑日期。
- 类型：`environment`；原批次：`06_policy_environment_20261029`。
- 原件现址：`/mnt/data/joey_tr/physical-RSI/result/06_policy_environment_20261029/`。历史文件中的旧执行路径保留作来源，本次导航统一指向实验室。
- 周志性质：协议、准备、审计或管理节点，未作为新的物理实验累计。

## 做了什么与得到什么

验证策略库导入与小规模依赖路径。

依赖安装与适配记录保留，存在 Rerun 要求 NumPy>=2 与 OpenPI 路线 NumPy<2 的版本冲突；后续兼容性验收另见下一记录。

## 解释边界与失败记录

判定：**部分**。本阶段没有下载或运行真实 checkpoint；依赖通过不能替代 VLA 或渲染验收。

## 复现与证据定位

本次只读取与离线复算；历史 runner、日志、协议、依赖指纹保留在下列原件。不同阶段的补丁和环境不能用一个背景 commit 替代。未明确记录的 seed、硬件或启动命令保持未知，不从今天服务器配置倒推。

| 证据原件（实验室现址） | SHA256 |
|---|---|
| status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/06_policy_environment_20261029/status.json`） | `6b609829586bc47af3ba3226fa5cb8099470e2710ff632053322e55f4e07adfe` |
| adapter-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/06_policy_environment_20261029/adapter-status.json`） | `3a215864649e3bd674e082cdb37b606ca1c9812309ad2feaa0690121e43db6f7` |
| setup.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/06_policy_environment_20261029/setup.log`） | `96fddd097ebc14b578c059f2a8293c7ae878397dcdcf0b8c9cd0e72ba87a285a` |
| after.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/06_policy_environment_20261029/after.json`） | `1ee9cfd05f66b246467e80260688751271a11daf1953b9629920f02f030f9cc6` |
| before.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/06_policy_environment_20261029/before.json`） | `1ee9cfd05f66b246467e80260688751271a11daf1953b9629920f02f030f9cc6` |
| 安装与验证说明.txt（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/06_policy_environment_20261029/安装与验证说明.txt`） | `4aad6a684ef83bf217810f849e99ad1371e9566e2937b6073a391b71c65b9fcc` |
| gpu-check.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/06_policy_environment_20261029/gpu-check.log`） | `23beb913ba016d478825c6f93ef56c8021a1f4a7d9bcecff0170de43d026fc1c` |
| disk-usage.txt（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/06_policy_environment_20261029/disk-usage.txt`） | `ad44e20d394740acf9d07eec9bf9c90be90095ebda97bf134b0dfda807e93c88` |
| gpu-check.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/06_policy_environment_20261029/gpu-check.json`） | `23beb913ba016d478825c6f93ef56c8021a1f4a7d9bcecff0170de43d026fc1c` |
| validation.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/06_policy_environment_20261029/validation.log`） | `0060e6cca382b4cd3d555556348cae664b7f109a6db26d2f61a2720c7eb5cb61` |
| sync_openpi.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/06_policy_environment_20261029/sync_openpi.log`） | `8286d399f8a867b040ba92185ad08ba74d7244197b0703242f5022d94790b3d6` |
| validation.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/06_policy_environment_20261029/validation.json`） | `0060e6cca382b4cd3d555556348cae664b7f109a6db26d2f61a2720c7eb5cb61` |
| bootstrap_uv.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/06_policy_environment_20261029/bootstrap_uv.log`） | `a6539c7c16bb681ededa5373c3220d1983054b12be082dbee06052f3d887ab73` |
| adapter-setup.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/06_policy_environment_20261029/adapter-setup.log`） | `83ba1ed7d4c66a9250bee23c21ce0103eab44645e32789475ca9015d2411b71c` |
| finish_lab_policy.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/06_policy_environment_20261029/finish_lab_policy.py`） | `2ff6e51505eec882eb9eee0bde94a75e98d1074380c3911a4e4d178eb7d17102` |
| patch_lab_policy_transformers.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/06_policy_environment_20261029/patch_lab_policy_transformers.py`） | `4b1f0977a2084e64a71ed58ea1fa6145dcb667585fe809ef1210cff257a0d1ea` |
| setup_lab_policy.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/06_policy_environment_20261029/setup_lab_policy.py`） | `2022908f4029b2d6912c1061bd8fa0f3ef902892eea82859061271c812027f6a` |

## 阅读覆盖与下一步

本单元 53 个可读普通文件、47 种不同字节内容已完整读入并校验；逐文件清单见 [审计账本](../../evidence/readthrough_20261102/file-review-ledger.jsonl.gz)，按 `HIST-008` 检索。JSON/日志/代码等做对应结构分析，重点协议、结果、失败和计量证据用于本条解释；这不声称所有依赖副本逐行人工精读，或全部视频逐帧人工审片。

下一步：本阶段记录封存至 11 月 2 日结束。后续实验另登记；如需补证，先定位本条限制对应原件，不自动重跑。
