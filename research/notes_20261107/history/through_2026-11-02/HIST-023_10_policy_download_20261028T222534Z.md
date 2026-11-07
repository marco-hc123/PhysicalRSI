# HIST-023 · 固定资产下载与分片验证

- 历史记录范围（北京时间）：2026-10-29T07:19:17.339499+08:00 至 2026-10-29T07:19:17.339499+08:00。
- 时间依据：original structured timestamp fields; observed record range is not necessarily physical rollout duration
- 本次回溯补录：2026-11-05 11:40，不是重跑日期。
- 类型：`assets`；原批次：`10_policy_download_20261028T222534Z`。
- 原件现址：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/10_policy_download_20261028T222534Z/`。历史文件中的旧执行路径保留作来源，本次导航统一指向实验室。
- 周志性质：协议、准备、审计或管理节点，未作为新的物理实验累计。

## 做了什么与得到什么

获取并核对发布的策略和技能资源。

32/32 分片通过 SHA256，verified_bytes=31895797760；无 API、未在此步骤安装。

## 解释边界与失败记录

判定：**N**。下载不是训练或物理评估；分片数不是实验次数。

## 复现与证据定位

本次只读取与离线复算；历史 runner、日志、协议、依赖指纹保留在下列原件。不同阶段的补丁和环境不能用一个背景 commit 替代。未明确记录的 seed、硬件或启动命令保持未知，不从今天服务器配置倒推。

| 证据原件（实验室现址） | SHA256 |
|---|---|
| status.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/10_policy_download_20261028T222534Z/status.json`） | `76a56b5f8725b5d690a25a2a7a92dc5cb3748c7f3766b630c8a6c0d5c51aa34c` |
| assets.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/10_policy_download_20261028T222534Z/assets.json`） | `0eed83202427dc6b4c75cde613246f8f6e606cac6c8da3bd71ebc6798d6963d2` |
| launcher.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/10_policy_download_20261028T222534Z/launcher.log`） | `56dc428a0854db583a863c13004ef458756ed9135e32bf450c5be99bca0190ee` |
| logs/code-skills.tar.part000.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/10_policy_download_20261028T222534Z/logs/code-skills.tar.part000.log`） | `e6d499d55c1319daa59b574f2d4fd9a71fca219d1897d2c352cb6ea915e7fa83` |
| logs/code-skills.tar.part001.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/10_policy_download_20261028T222534Z/logs/code-skills.tar.part001.log`） | `762dad1f0525b75102604240750be2327e0ad740dfc247e598ae3f68107dcd3a` |
| logs/code-skills.tar.part002.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/10_policy_download_20261028T222534Z/logs/code-skills.tar.part002.log`） | `74d9ddfccad03c17538adb10ef3f336646edaa5939a5bba9e8c5bb351df652e4` |
| logs/code-skills.tar.part003.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/10_policy_download_20261028T222534Z/logs/code-skills.tar.part003.log`） | `1fd6e67101f184c044ed30ef9d2f896fed3571bd3172da01d38fc4c82a586e57` |
| logs/code-skills.tar.part004.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/10_policy_download_20261028T222534Z/logs/code-skills.tar.part004.log`） | `a10dfa7d903fd4cead03ddfd394dc327e916781bab61c6e7ed8e26e0c2538556` |
| logs/code-skills.tar.part005.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/10_policy_download_20261028T222534Z/logs/code-skills.tar.part005.log`） | `4c07eaa739c27f81a244f7eb94db6e2833f538658785a21609eb6c5c779fb9d2` |
| logs/code-skills.tar.part006.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/10_policy_download_20261028T222534Z/logs/code-skills.tar.part006.log`） | `22ed0845eece89eabeff33a8f5f59c6fdeaf8f18c95fa8285a81b11ec3d69f1d` |
| logs/pi05-weights.tar.part000.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/10_policy_download_20261028T222534Z/logs/pi05-weights.tar.part000.log`） | `391c59f60153e243103b43331d12b92a855848dabf78b3b9d7dcf14da63da873` |
| logs/pi05-weights.tar.part001.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/10_policy_download_20261028T222534Z/logs/pi05-weights.tar.part001.log`） | `7687b59379412ccf6e390ffc9c817ab2b9b54e376ab40a3ea3cbe68625bab333` |
| logs/pi05-weights.tar.part002.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/10_policy_download_20261028T222534Z/logs/pi05-weights.tar.part002.log`） | `4d07c8da65887cff35a5389cd275e7c86a6600a29d223f437848c97d6718e11d` |
| logs/pi05-weights.tar.part003.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/08_simulation_setup/10_policy_download_20261028T222534Z/logs/pi05-weights.tar.part003.log`） | `3224c5c02d296d7df01c5f23092839d3456caca33f03b9f1d92823a5495f8fdb` |

## 阅读覆盖与下一步

本单元 35 个可读普通文件、35 种不同字节内容已完整读入并校验；逐文件清单见 审计账本（原始归档位置：`../../evidence/readthrough_20261102/file-review-ledger.jsonl.gz`），按 `HIST-023` 检索。JSON/日志/代码等做对应结构分析，重点协议、结果、失败和计量证据用于本条解释；这不声称所有依赖副本逐行人工精读，或全部视频逐帧人工审片。

下一步：本阶段记录封存至 11 月 2 日结束。后续实验另登记；如需补证，先定位本条限制对应原件，不自动重跑。
