# HIST-056 · 实验室环境补齐与有限离线验收

- 历史记录范围（北京时间）：2026-11-01 至 2026-11-01。
- 时间依据：来源：原记录日期/登记目录；不把文件传输时间当实验开始时间。
- 本次回溯补录：2026-11-05 11:40，不是重跑日期。
- 类型：`environment`；原批次：`23_lab_environment_setup`。
- 原件现址：`/mnt/data/joey_tr/physical-RSI/result/23_lab_environment_setup/`。历史文件中的旧执行路径保留作来源，本次导航统一指向实验室。
- 周志性质：协议、准备、审计或管理节点，未作为新的物理实验累计。

## 做了什么与得到什么

安装 analysis、agent、simulator 并保留原策略环境。

33项步骤完成，5个启动入口可用；analysis/agent依赖检查通过，IsaacLab/Starlette不一致明确保留。

## 解释边界与失败记录

判定：**部分**。截至此阶段未做真实 checkpoint、付费API或 renderer 执行，不能把安装完成写成 H100 原生复现。

## 复现与证据定位

本次只读取与离线复算；历史 runner、日志、协议、依赖指纹保留在下列原件。不同阶段的补丁和环境不能用一个背景 commit 替代。未明确记录的 seed、硬件或启动命令保持未知，不从今天服务器配置倒推。

| 证据原件（实验室现址） | SHA256 |
|---|---|
| 20261101T111000Z/status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/23_lab_environment_setup/20261101T111000Z/status.json`） | `2ee1368a6dec6f20ce739e17e9d3f9fb9f273f7c2826678fa2e6f7e6ffb131fc` |
| 20261101T111000Z/acceptance-summary.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/23_lab_environment_setup/20261101T111000Z/acceptance-summary.json`） | `0b91315c7be98947e6b797fb648e8a021fc27a09a103288fb559bb7585e86c9e` |
| 20261101T111000Z/resource-bindings-verification.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/23_lab_environment_setup/20261101T111000Z/resource-bindings-verification.json`） | `3c3f99f953455581a635cf5752305f624a2003d5ec7aa258f8dadd8d9a78242d` |
| 20261101T111000Z/after.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/23_lab_environment_setup/20261101T111000Z/after.json`） | `cfe654e72823bbb0aec5db409d01763c05c6650856b8999aa2cd693aee53c4fb` |
| 20261101T111000Z/before.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/23_lab_environment_setup/20261101T111000Z/before.json`） | `c37f69051a4c4dedd48973900b1ad8997fbf76e2719f45d018b7f98c6d6cd494` |
| 20261101T111000Z/controller.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/23_lab_environment_setup/20261101T111000Z/controller.log`） | `4d9cc555c083ad11bc0c0d9812a935cb59b08c269ac490077b7b830535d4bdbe` |
| 20261101T111000Z/install_lab.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/23_lab_environment_setup/20261101T111000Z/install_lab.py`） | `befe6807d8886ba1922b63ba42bc98060c7905a3db995422339ef5db90075d30` |
| 20261101T111000Z/finalize_lab.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/23_lab_environment_setup/20261101T111000Z/finalize_lab.py`） | `7a08b594b004f7b305df66ecf3d455d9beb4e44939f06a097e8f7ea1ed204ef8` |
| 20261101T111000Z/agent_demo.1.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/23_lab_environment_setup/20261101T111000Z/agent_demo.1.log`） | `c8f999f46829b19f6bb66f8ef511f1e5d6dbe7dd5d6e17b27835f365d1383639` |
| 20261101T111000Z/impact-audit.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/23_lab_environment_setup/20261101T111000Z/impact-audit.json`） | `a55807dd61fed3ddfd75b729fea9b478d747364677fba3dbc619f66eb15e5fe8` |
| 20261101T111000Z/agent_freeze.1.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/23_lab_environment_setup/20261101T111000Z/agent_freeze.1.log`） | `b358ba06bbcba1278e9182f383ac679f22714debda4c3a6dd6634d4d7262fbe7` |
| 20261101T111000Z/analysis-smoke.csv（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/23_lab_environment_setup/20261101T111000Z/analysis-smoke.csv`） | `9d167b3aba4eaf8fdb036711a0a8528fac6b94152e8b889fd9c33a80277e8e8c` |
| 20261101T111000Z/create_agent.1.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/23_lab_environment_setup/20261101T111000Z/create_agent.1.log`） | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| 20261101T111000Z/isaacsim_5_1.1.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/23_lab_environment_setup/20261101T111000Z/isaacsim_5_1.1.log`） | `251318c452cd152c19797caf52da50f2b079e43a06b1ecd15940ceee43665e5c` |
| 20261101T111000Z/install_lab.attempt1.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/23_lab_environment_setup/20261101T111000Z/install_lab.attempt1.py`） | `f7be093bd8ec788c0ca131b7f1968bb193953d76c565aaba581825d7b407b055` |

## 阅读覆盖与下一步

本单元 93 个可读普通文件、87 种不同字节内容已完整读入并校验；逐文件清单见 [审计账本](../../evidence/readthrough_20261102/file-review-ledger.jsonl.gz)，按 `HIST-056` 检索。JSON/日志/代码等做对应结构分析，重点协议、结果、失败和计量证据用于本条解释；这不声称所有依赖副本逐行人工精读，或全部视频逐帧人工审片。

下一步：本阶段记录封存至 11 月 2 日结束。后续实验另登记；如需补证，先定位本条限制对应原件，不自动重跑。
