# HIST-012 · 原生依赖部署

- 历史记录范围（北京时间）：2026-10-28T21:12:32.023451+08:00 至 2026-10-28T21:12:32.023451+08:00。
- 时间依据：original structured timestamp fields; observed record range is not necessarily physical rollout duration
- 本次回溯补录：2026-11-05 11:40，不是重跑日期。
- 类型：`environment`；原批次：`07_native_deployment_20261028`。
- 原件现址：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/07_native_deployment_20261028/`。历史文件中的旧执行路径保留作来源，本次导航统一指向实验室。
- 周志性质：协议、准备、审计或管理节点，未作为新的物理实验累计。

## 做了什么与得到什么

安装固定来源的仿真依赖并检查资源下载入口。

simulator_packages 状态 complete；资产端点可响应与权重 payload_verified 分别记录。

## 解释边界与失败记录

判定：**部分**。可访问下载入口不等于已经验证模型资产，后续下载/安装记录负责该证据。

## 复现与证据定位

本次只读取与离线复算；历史 runner、日志、协议、依赖指纹保留在下列原件。不同阶段的补丁和环境不能用一个背景 commit 替代。未明确记录的 seed、硬件或启动命令保持未知，不从今天服务器配置倒推。

| 证据原件（实验室现址） | SHA256 |
|---|---|
| status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/07_native_deployment_20261028/status.json`） | `2929f31de2964b54d2ede49a83abf3c34098f6d25d5e3e09a84fd8ea03733ad6` |
| scene_payload_status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/07_native_deployment_20261028/scene_payload_status.json`） | `39d30e7cc9c97dc5ec03db0fb8473322ac95a0944e1bbbc30b337285ce9ba6ed` |
| isaacsim_install_report.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/07_native_deployment_20261028/isaacsim_install_report.json`） | `3d8c0d2b01d0627e0d0a9076f2dc79f3ea34b57882e4f7de194b02599a461466` |
| asset_download_endpoint_status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/07_native_deployment_20261028/asset_download_endpoint_status.json`） | `7b6b9270e0e0ab1327e46680f256c10a5c14807dc4c2a6f5267575e9eb261fdc` |
| fetch_sources.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/07_native_deployment_20261028/fetch_sources.py`） | `f2306d8dd0a32d890b7ecf80576c9a414bce14af55815335caef844b9bd58e55` |
| setup_framework.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/07_native_deployment_20261028/setup_framework.py`） | `93e961ef99adcf61227699a6a0ecf992367cc7f3620a844395a0902462a24576` |
| fetch_submodules.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/07_native_deployment_20261028/fetch_submodules.py`） | `9ba232e442ae8a1304de20d3b308f76c7c876bfefc8801fffa682cbedd0bd8fd` |
| resume_bootstrap.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/07_native_deployment_20261028/resume_bootstrap.py`） | `6642d986a1a3e9a8098914fa7af896b44c4d3223ff0fd2c50807c6cb7e6f5fb4` |
| adapter_overlay.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/07_native_deployment_20261028/adapter_overlay.json`） | `50fcadd5049071df7bfbe588e13006b8650a28784e63cf859d908d6436ec2cec` |
| fetch_asset_index.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/07_native_deployment_20261028/fetch_asset_index.py`） | `07e7645834f019d0e3c176f5c52b68888c6764f1b16339c0de05d09587cba3b5` |
| source_versions.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/07_native_deployment_20261028/source_versions.json`） | `ca23c7cd126cfe2ea71b9a60be9d148627c517baee96a31d98bb6f46679c2746` |
| api_access_policy.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/07_native_deployment_20261028/api_access_policy.json`） | `a76c74204524ce736ab40f4e4b633bce185646d7045325b86aa06b2d1feac9d7` |
| bootstrap_simulator.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/07_native_deployment_20261028/bootstrap_simulator.py`） | `f94644be88affd6df43e21ad4722a387de7177dce7870db22278c7342418d333` |
| curobo_source_diff.txt（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/07_native_deployment_20261028/curobo_source_diff.txt`） | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| download_scene_payloads.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/07_native_deployment_20261028/download_scene_payloads.py`） | `a0ed60818dcebaaefc08a86c2579ac4c2ae2a199588eac3632465ea9d2ac722d` |

## 阅读覆盖与下一步

本单元 161 个可读普通文件、153 种不同字节内容已完整读入并校验；逐文件清单见 [审计账本](../../evidence/readthrough_20261102/file-review-ledger.jsonl.gz)，按 `HIST-012` 检索。JSON/日志/代码等做对应结构分析，重点协议、结果、失败和计量证据用于本条解释；这不声称所有依赖副本逐行人工精读，或全部视频逐帧人工审片。

下一步：本阶段记录封存至 11 月 2 日结束。后续实验另登记；如需补证，先定位本条限制对应原件，不自动重跑。
