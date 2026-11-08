# HIST-009 · Rerun、policy/data 与视频解码兼容性

- 历史记录范围（北京时间）：2026-10-29 至 2026-10-29。
- 时间依据：来源：原记录日期/登记目录；不把文件传输时间当实验开始时间。
- 本次回溯补录：2026-11-05 11:40，不是重跑日期。
- 类型：`environment`；原批次：`07_rerun_compatibility_20261029`。
- 原件现址：`/mnt/data/joey_tr/physical-RSI/result/07_rerun_compatibility_20261029/`。历史文件中的旧执行路径保留作来源，本次导航统一指向实验室。
- 周志性质：协议、准备、审计或管理节点，未作为新的物理实验累计。

## 做了什么与得到什么

定位解码和依赖冲突，并检查受影响的实际数据路径。

修复项目 Python/RPATH 后，post_fix/runtime 的六项合成 policy/data/解码检查通过；原 pip check 冲突继续留存。

## 解释边界与失败记录

判定：**部分**。synthetic identity inference、合成数据 roundtrip 与真实模型推理不同；未进行完整 viewer GUI 验收。

## 复现与证据定位

本次只读取与离线复算；历史 runner、日志、协议、依赖指纹保留在下列原件。不同阶段的补丁和环境不能用一个背景 commit 替代。未明确记录的 seed、硬件或启动命令保持未知，不从今天服务器配置倒推。

| 证据原件（实验室现址） | SHA256 |
|---|---|
| fix-isolation-verification.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/07_rerun_compatibility_20261029/fix-isolation-verification.json`） | `4f56185334c7f8d8e47cc079612d4b223374e6266105716c1c4634667f104fe5` |
| rerun.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/07_rerun_compatibility_20261029/rerun.log`） | `ae9c563716aa952834fb5aac61245730ce976bd1f0d3da59910276563ad8cbff` |
| rerun.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/07_rerun_compatibility_20261029/rerun.json`） | `e4b548ca4cbc7887e45b24649f924a1459c0a48b868af742202ad421e2783fe0` |
| runtime.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/07_rerun_compatibility_20261029/runtime.log`） | `822c7ce2493e1acbc66def304ec6dbde5249e322ea7a7e8ffbeac8accf2d1da1` |
| runtime.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/07_rerun_compatibility_20261029/runtime.json`） | `8326880033ceafdc73bdd2b90dcb86fc691691bcfc764cbcb47a2f5cc7a2e4d7` |
| 兼容性复核与修复说明.txt（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/07_rerun_compatibility_20261029/兼容性复核与修复说明.txt`） | `1a8261820834168699d1b03a3085683e95ff2c0c282cef4c88e359db5f55df4b` |
| probe_lab_rerun.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/07_rerun_compatibility_20261029/probe_lab_rerun.py`） | `61a146782ff9eb6a2c75acb358a5f065b5a8d3a3d0724843556be48f1dbb6386` |
| isolation-audit.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/07_rerun_compatibility_20261029/isolation-audit.log`） | `afd4e086b71cce0a5474d6261d4146e37cdec668ddfbe9b3d50a52061bccf1e4` |
| isolation-audit.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/07_rerun_compatibility_20261029/isolation-audit.json`） | `afd4e086b71cce0a5474d6261d4146e37cdec668ddfbe9b3d50a52061bccf1e4` |
| python-rpath-fix.log（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/07_rerun_compatibility_20261029/python-rpath-fix.log`） | `1e0a7fc0f5bc3818c75bc1650aa61ff12f1b99af912c826c73f18e31a400d212` |
| python-rpath-fix.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/07_rerun_compatibility_20261029/python-rpath-fix.json`） | `1e0a7fc0f5bc3818c75bc1650aa61ff12f1b99af912c826c73f18e31a400d212` |
| python-copy-probe.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/07_rerun_compatibility_20261029/python-copy-probe.json`） | `45686ded3f919b0ff4520b15b542ea5784cb10fc38c9fa30ec9f463e1fcb9c25` |
| current-environments.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/07_rerun_compatibility_20261029/current-environments.json`） | `1ee9cfd05f66b246467e80260688751271a11daf1953b9629920f02f030f9cc6` |
| fix_lab_policy_python_rpath.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/07_rerun_compatibility_20261029/fix_lab_policy_python_rpath.py`） | `acfc924182a944d3863476862adbc3280f586f385a87528515b6503fac9c851d` |
| audit_lab_environment_isolation.py（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/07_rerun_compatibility_20261029/audit_lab_environment_isolation.py`） | `cdbfa7f97923880afd1fc3da5a3077fd298f324c1e129b661ed744afebe6b089` |

## 阅读覆盖与下一步

本单元 52 个可读普通文件、37 种不同字节内容已完整读入并校验；逐文件清单见 [审计账本](../../evidence/readthrough_20261102/file-review-ledger.jsonl.gz)，按 `HIST-009` 检索。JSON/日志/代码等做对应结构分析，重点协议、结果、失败和计量证据用于本条解释；这不声称所有依赖副本逐行人工精读，或全部视频逐帧人工审片。

下一步：本阶段记录封存至 11 月 2 日结束。后续实验另登记；如需补证，先定位本条限制对应原件，不自动重跑。
