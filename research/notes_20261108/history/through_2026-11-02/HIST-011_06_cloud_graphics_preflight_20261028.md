# HIST-011 · GPU、CUDA 与 Vulkan 前置检查

- 历史记录范围（北京时间）：2026-10-28T19:46:55.724346+08:00 至 2026-10-28T19:49:12.263351+08:00。
- 时间依据：original structured timestamp fields; observed record range is not necessarily physical rollout duration
- 本次回溯补录：2026-11-05 11:40，不是重跑日期。
- 类型：`environment`；原批次：`06_cloud_graphics_preflight_20261028`。
- 原件现址：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/06_cloud_graphics_preflight_20261028/`。历史文件中的旧执行路径保留作来源，本次导航统一指向实验室。
- 周志性质：协议、准备、审计或管理节点，未作为新的物理实验累计。

## 做了什么与得到什么

确认原生仿真运行所需的设备与图形前提。

L20 CUDA vector addition 验证 65536 个元素，Vulkan 功能与下载端点检查有原始 stdout/JSON。

## 解释边界与失败记录

判定：**N**。这是设备和接口准备，不是任务评分或完整仿真闭环。

## 复现与证据定位

本次只读取与离线复算；历史 runner、日志、协议、依赖指纹保留在下列原件。不同阶段的补丁和环境不能用一个背景 commit 替代。未明确记录的 seed、硬件或启动命令保持未知，不从今天服务器配置倒推。

| 证据原件（实验室现址） | SHA256 |
|---|---|
| summary.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/06_cloud_graphics_preflight_20261028/summary.json`） | `e552196f11c7200772c92cdf3bf1c709cd88f92d7a7aa4cc16081ddd30634d71` |
| docker_status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/06_cloud_graphics_preflight_20261028/docker_status.json`） | `e1a82ce358e8650821c5880ea9e4df31820d70b15f3d41e3246e58748baac2c2` |
| vulkan_summary.stderr.txt（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/06_cloud_graphics_preflight_20261028/vulkan_summary.stderr.txt`） | `9b8ce0d5aabd827937d81f2e3a130958edf27c3abe507ce8c54ed6cef9c82b27` |
| vulkan_summary.stdout.txt（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/06_cloud_graphics_preflight_20261028/vulkan_summary.stdout.txt`） | `c8b6f82bdf6ea16e7b8e8fff79b41910afce8507d117bdab4879405128259d45` |
| README.txt（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/06_cloud_graphics_preflight_20261028/README.txt`） | `9c4af51243e77b27f26b35f25a2e35ea68a99fb4fd76a0b7e932af1d293cccdd` |
| commands.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/06_cloud_graphics_preflight_20261028/commands.json`） | `1248959d866f067453c4586ef802b64faf0acbf9a9ad2cd453b3a3dc412050ef` |
| os.stderr.txt（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/06_cloud_graphics_preflight_20261028/os.stderr.txt`） | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| os.stdout.txt（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/06_cloud_graphics_preflight_20261028/os.stdout.txt`） | `594d5ddd35aedb47f00d9c34d140017907a5b9f93c975aba125fc924daac5c07` |
| cpu.stderr.txt（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/06_cloud_graphics_preflight_20261028/cpu.stderr.txt`） | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| cpu.stdout.txt（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/06_cloud_graphics_preflight_20261028/cpu.stdout.txt`） | `1c656bbb4594953637b72cb0ad1743e7b1f43fef14acc614163d65dc9b5b0298` |
| gpu.stderr.txt（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/06_cloud_graphics_preflight_20261028/gpu.stderr.txt`） | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| gpu.stdout.txt（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/06_cloud_graphics_preflight_20261028/gpu.stdout.txt`） | `0519c69f247ac948469735aafbf7bfba89cdd1c78fc0a02bee77a5fc9bbf6132` |
| mount.stderr.txt（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/06_cloud_graphics_preflight_20261028/mount.stderr.txt`） | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| mount.stdout.txt（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/06_cloud_graphics_preflight_20261028/mount.stdout.txt`） | `ec461c022be8372c179b85914f00b96edac6a77776f8089a8018dad1f236d9ec` |
| complete_preflight.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/06_cloud_graphics_preflight_20261028/complete_preflight.py`） | `c5be3b33ff6323909baaed6f1b335e733a5dbab0351bcf723a5d311aa6f13a9d` |
| finalize_evidence.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/06_cloud_graphics_preflight_20261028/finalize_evidence.py`） | `e5ef24610f506d512ab9f024fff50d442cee5381127cd6e82e3784516df6e561` |
| prepare_vulkan_tools.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/06_cloud_graphics_preflight_20261028/prepare_vulkan_tools.py`） | `00f276a57f3f2e95a902bc6c2eda51e7c4ef139febef97d5ff3c2be59e295339` |

## 阅读覆盖与下一步

本单元 60 个可读普通文件、35 种不同字节内容已完整读入并校验；逐文件清单见 [审计账本](../../evidence/readthrough_20261102/file-review-ledger.jsonl.gz)，按 `HIST-011` 检索。JSON/日志/代码等做对应结构分析，重点协议、结果、失败和计量证据用于本条解释；这不声称所有依赖副本逐行人工精读，或全部视频逐帧人工审片。

下一步：本阶段记录封存至 11 月 2 日结束。后续实验另登记；如需补证，先定位本条限制对应原件，不自动重跑。
