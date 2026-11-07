# HIST-010 · Isaac RGB 渲染预检与失败修复

- 历史记录范围（北京时间）： 至 。
- 时间依据：run ID timestamp only; exact execution times not inferred
- 本次回溯补录：2026-11-05 11:40，不是重跑日期。
- 类型：`environment`；原批次：`08_isaac_rgb_smoke_20261028`。
- 原件现址：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/08_isaac_rgb_smoke_20261028/`。历史文件中的旧执行路径保留作来源，本次导航统一指向实验室。
- 周志性质：协议、准备、审计或管理节点，未作为新的物理实验累计。

## 做了什么与得到什么

确认程序化场景能输出有效 RGB。

保留缺图形库与 GL dispatch 等两次早期失败及最终渲染结果；最终获得 640×480 非恒定 RGB。

## 解释边界与失败记录

判定：**部分**。图像渲染成功不等于原生机器人任务成功；本批未执行机器人策略。

## 复现与证据定位

本次只读取与离线复算；历史 runner、日志、协议、依赖指纹保留在下列原件。不同阶段的补丁和环境不能用一个背景 commit 替代。未明确记录的 seed、硬件或启动命令保持未知，不从今天服务器配置倒推。

| 证据原件（实验室现址） | SHA256 |
|---|---|
| render_result.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/08_isaac_rgb_smoke_20261028/render_result.json`） | `30489936a8e98e359e901316a9c68f33cd6e553d58f5b7ce0219aac733fe6b65` |
| kit.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/08_isaac_rgb_smoke_20261028/kit.log`） | `d1c0551f7c26db1ec3a9be14e9fc1000de4a7992e6e100d06f9cd3333329a974` |
| stdout.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/08_isaac_rgb_smoke_20261028/stdout.log`） | `7bf9bd50c678c43f3b3b2b5f3e4fb30f81be6dedd26b008ed0bb445109829568` |
| run_smoke.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/08_isaac_rgb_smoke_20261028/run_smoke.py`） | `3c4585d2e39e0bbf5b60fc8577a5196d79d70d55117139030185d8aca09f8847` |
| render_rgb.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/08_isaac_rgb_smoke_20261028/render_rgb.py`） | `8035623790eba0493afc98b5229f552bf00da9f7bc4c1b48804ab342c21d106a` |
| execution.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/08_isaac_rgb_smoke_20261028/execution.json`） | `4b8ccb8aeba1ac3561ec07b336f6c148ccc9adbb3e204a2182a204f98add6611` |
| attempt02_gl_dispatch_mismatch/kit.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/08_isaac_rgb_smoke_20261028/attempt02_gl_dispatch_mismatch/kit.log`） | `26f52fdfcddf264262f17787c46a01c57532f0b6689d299f5054e047e162b808` |
| attempt02_gl_dispatch_mismatch/stdout.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/08_isaac_rgb_smoke_20261028/attempt02_gl_dispatch_mismatch/stdout.log`） | `89b3567099655ff9f8328e13ecf85bd16563ee912a169e4a1ecf3a624869ad73` |
| attempt01_missing_graphics_libraries/kit.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/08_isaac_rgb_smoke_20261028/attempt01_missing_graphics_libraries/kit.log`） | `12799d4091919ea1d4fdac1e0de4e4419a3a59bdf2714baa001107c4fa39227d` |
| attempt02_gl_dispatch_mismatch/diagnosis.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/08_isaac_rgb_smoke_20261028/attempt02_gl_dispatch_mismatch/diagnosis.json`） | `fc04a01e82eded8fb900fbc530146b412d2d4330fd26499f7367ffc5a8815ffd` |
| attempt02_gl_dispatch_mismatch/execution.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/08_isaac_rgb_smoke_20261028/attempt02_gl_dispatch_mismatch/execution.json`） | `2b16ea3127ca260545c4ea7bad1f868101143cb0567714825d8336f6c5a5095d` |
| attempt01_missing_graphics_libraries/stdout.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/08_isaac_rgb_smoke_20261028/attempt01_missing_graphics_libraries/stdout.log`） | `35c89ab5f45386bc5fe4a6023e30b19526f16baa399f40f2c2df4d4ae167638f` |
| attempt01_missing_graphics_libraries/diagnosis.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/08_isaac_rgb_smoke_20261028/attempt01_missing_graphics_libraries/diagnosis.json`） | `71a9140b2640aaad48a03c15f5ac18644442654eaf573fd48207b92b6915259b` |
| attempt01_missing_graphics_libraries/execution.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/08_isaac_rgb_smoke_20261028/attempt01_missing_graphics_libraries/execution.json`） | `6a324f013e5b3602fdaa3785642b8e80a36e821ee26a1e17e65aba391e4ec11f` |

## 阅读覆盖与下一步

本单元 20 个可读普通文件、20 种不同字节内容已完整读入并校验；逐文件清单见 审计账本（原始归档位置：`../../evidence/readthrough_20261102/file-review-ledger.jsonl.gz`），按 `HIST-010` 检索。JSON/日志/代码等做对应结构分析，重点协议、结果、失败和计量证据用于本条解释；这不声称所有依赖副本逐行人工精读，或全部视频逐帧人工审片。

下一步：本阶段记录封存至 11 月 2 日结束。后续实验另登记；如需补证，先定位本条限制对应原件，不自动重跑。
