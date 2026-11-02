# 原始执行证据补充（2026-11-02）

本目录补充已有实验的可核查原件。新增模型调用、原生机器人回合和训练均为 0；原成功率、得分、Token 与计时结论保持原口径。

## 保存了什么

- 旧档案库缺失的 7,595 个独特执行文本对象：原生 API 请求/响应、提示与模型选择、候选/提案/轮次记录、代码执行轨迹、RPC/服务日志、独立验收、恢复与失败机制诊断。
- 新核对实验室资料的 169 个独特文本对象：环境重建/入口配置、归档迁移映射、客户端脚本、GPT 补测的执行契约与 GPU 采样等。与已经发布或刚补齐的对象相同时只建立引用；已有脱敏版本保持脱敏。
- 60 个独特小型二进制附件：合成 API 输入图片、历史图表、HDF5/Parquet/video 兼容性样本等。**合成视频与兼容性样本不属于机器人任务结果**，具体角色见附件索引。

全部新文本共 7,764 个 SHA256 对象，恢复后 487,308,985 字节。来源路径、重复副本、相机视角、程序对象数量均不等于实验回合或 API 调用数。

## 索引与读取

- [历史执行文本来源索引](../../provenance/raw-execution-source-index-20261102.csv.gz)：源路径、原字节数/SHA256、无损容器路径。
- [本次实验室只读来源索引](../../provenance/lab-readonly-source-index-20261102.csv)：已有精确文件、已有无损对象、已有脱敏派生版本或新对象。
- [小型附件索引](../../provenance/auxiliary-evidence-index-20261102.csv)：原路径、角色、SHA256 与附件路径；同内容共用一个文件。
- [原件恢复核验](../../provenance/raw-execution-verification-20261102.json)。

```bash
python tools/read_raw_execution_evidence.py --verify
python tools/read_raw_execution_evidence.py --search /proposal-api/
python tools/read_raw_execution_evidence.py --search cpu-contract-gate
```

搜索后将完整 `source_path` 作为参数，即可将原件输出到标准输出。gzip JSONL 每项保留原 SHA256、原字节数、`part/parts` 和 UTF-8 文本；按序连接分片再编码即可恢复原字节。工具仅读取，不执行其中的脚本或请求 API。记录中的 PID、路径和启动状态为历史状态，不能据此启动或接管实验。

## 外部原件与边界

[实验室二进制清单](../../provenance/lab-binary-inventory-20261102.csv.gz)仅列出原件路径、大小和 mtime。它包含逐帧图像、多个相机视角视频、NPZ/NPY 观测等；是目录元数据快照，未声称本次逐一验证全部二进制内容，也不是新增独立实验清单。代表性真实视频见 [展示材料](../../reports/evidence/media/README.md)。模型权重、完整已安装环境、下载/编译缓存和官方整套场景资产不在本目录。

历史原执行根路径用于溯源；当前整理后位置由已归档的迁移映射说明。没有连接旧云主机，没有写入实验室服务器。有关待验证问题和下一轮研究见 [研究总览](../../docs/RESEARCH_OVERVIEW_ZH.md)。
