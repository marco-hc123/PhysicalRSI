# HIST-014 · 仿真与策略环境分离安装

- 历史记录范围（北京时间）： 至 。
- 时间依据：run ID timestamp only; exact execution times not inferred
- 本次回溯补录：2026-11-05 11:40，不是重跑日期。
- 类型：`environment`；原批次：`11_environment_setup_20261028T222805Z`。
- 原件现址：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/11_environment_setup_20261028T222805Z/`。历史文件中的旧执行路径保留作来源，本次导航统一指向实验室。
- 周志性质：协议、准备、审计或管理节点，未作为新的物理实验累计。

## 做了什么与得到什么

建立原生 simulator 和 policy 两条依赖路径。

simulator 原生依赖和 OpenPI 同步完成；adapter 仍报告依赖冲突，后续修复过程保留。

## 解释边界与失败记录

判定：**部分**。不能把局部安装成功写成整个运行栈无冲突。

## 复现与证据定位

本次只读取与离线复算；历史 runner、日志、协议、依赖指纹保留在下列原件。不同阶段的补丁和环境不能用一个背景 commit 替代。未明确记录的 seed、硬件或启动命令保持未知，不从今天服务器配置倒推。

| 证据原件（实验室现址） | SHA256 |
|---|---|
| policy-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/11_environment_setup_20261028T222805Z/policy-status.json`） | `12d4f8efe0899d11c70e8ddb09616ebb0eebfabc5d734facdaf80086facc4a29` |
| adapter-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/11_environment_setup_20261028T222805Z/adapter-status.json`） | `74326491f3f5b4161b923ffdd703e5c2b8184433d4b7100da5cc07911e8db0c7` |
| simulator-status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/11_environment_setup_20261028T222805Z/simulator-status.json`） | `d3008e7216d59bfeaa0a3a43347bb559bad2d666af8acf3cf525995263159e7e` |
| apt-update.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/11_environment_setup_20261028T222805Z/apt-update.log`） | `9f83b563fb78433b27869faaa687fb7dd1ef216c0f4ceba45fda570116749dfc` |
| native_h5py.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/11_environment_setup_20261028T222805Z/native_h5py.log`） | `6d7e3592336e51ccb6c09a9da5403564fe39c0e0dae40818fe93c859b0dd6d02` |
| policy-sync.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/11_environment_setup_20261028T222805Z/policy-sync.log`） | `3c1a2360a0a66e6d1f27e024b4eef65b5c3a498d761a0cfcf89077afa4a35f58` |
| native_hidapi.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/11_environment_setup_20261028T222805Z/native_hidapi.log`） | `e31cc3acc797a4b9170a468cb3f6777300f3b52172b30721925d5d6609074c8e` |
| curobo_install.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/11_environment_setup_20261028T222805Z/curobo_install.log`） | `c5b2910be8381b1c22c3f2fc2d672310846026bfaff203823b1d9496d171ed39` |
| ffmpeg-install.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/11_environment_setup_20261028T222805Z/ffmpeg-install.log`） | `2a5d775f820e2477c742708456392a54aa5eaa644e442d231bbf0a10367269a4` |
| adapter-install.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/11_environment_setup_20261028T222805Z/adapter-install.log`） | `9cec5a5c73e9358f2e4dec36811222cde66128629c82250303d51a6dad5b5483` |
| policy-launcher.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/11_environment_setup_20261028T222805Z/policy-launcher.log`） | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| setup_policy_env.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/11_environment_setup_20261028T222805Z/setup_policy_env.py`） | `1cd992ff572cc7c32b1e14a95195b2031afa301fa8043dfffb0202401a6f650d` |
| adapter-launcher.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/11_environment_setup_20261028T222805Z/adapter-launcher.log`） | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| policy-pip-check.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/11_environment_setup_20261028T222805Z/policy-pip-check.log`） | `e341e19d840cdfbad2465973a6685b2f6ffbc8713b6f4930cf8604db9a1c2bf3` |
| install_policy_adapter.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/11_environment_setup_20261028T222805Z/install_policy_adapter.py`） | `ac86e88fe67a4c944fa3e03dab0e43a81ab50892800f9a26430a2d6334003d8d` |
| setup_native_dependencies.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/11_environment_setup_20261028T222805Z/setup_native_dependencies.py`） | `2e64f8fd373bb3b0ca531e498a61a8e65e32b7241c435c136c5085ebe47a22a5` |

## 阅读覆盖与下一步

本单元 29 个可读普通文件、26 种不同字节内容已完整读入并校验；逐文件清单见 [审计账本](../../evidence/readthrough_20261102/file-review-ledger.jsonl.gz)，按 `HIST-014` 检索。JSON/日志/代码等做对应结构分析，重点协议、结果、失败和计量证据用于本条解释；这不声称所有依赖副本逐行人工精读，或全部视频逐帧人工审片。

下一步：本阶段记录封存至 11 月 2 日结束。后续实验另登记；如需补证，先定位本条限制对应原件，不自动重跑。
