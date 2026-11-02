# PhysicalRSI 仿真复现与 Token 消耗分析

本仓库记录本人基于 [PhysicalRSI](https://github.com/PhysicalRSI/PhysicalRSI) 开展的仿真复现、Token 用量分析，以及将高层模型由千问替换为 GPT 的补测。数据截至 **2026-11-02**。

这是个人复现与实验记录仓库。上游原始代码、本人使用的集成程序、模型生成候选和实验输出分别保留出处。原项目的功能与本次实际验证的范围应分开阅读。

## 先看哪些文件

- [全研究阶段原件库及读取方法](experiments/evidence_archive/README.md)
- [研究计划、讨论与周记](research/README.md)

- [完整研究总览：机制、全部阶段、结果与下一步](docs/RESEARCH_OVERVIEW_ZH.md)
- [按研究问题组织的证据导航](docs/EVIDENCE_INDEX.md)
- [历史详细报告、场景与汇报大纲](reports/research_archive_20261101/README.md)
- [新增图表、可编辑数据及代表性真实视频](reports/evidence/README.md)

- [汇报 PPT（2026-11-02，6 页）](reports/presentations/PhysicalRSI_report_20261102.pptx)

- [最新实验结论与限制](docs/RESULTS.md)
- [实验条件与复现说明](docs/REPRODUCE.md)
- [上传范围及资料来源](docs/SCOPE.md)
- [GPT 分类补测详细报告](experiments/system1_gpt/RESULTS_ZH.md)
- [GPT System 2 补测详细报告](experiments/system2_gpt/RESULTS_ZH.md)
- [历史任务结果表](experiments/history/task_extension_and_final_test/exports/task-summary.csv)
- [历史完整阶段报告](experiments/history/task_extension_and_final_test/final-review/report-final-zh.txt)

## 当前主要结果

| 实验 | 历史千问 | 本次 GPT 补测 | 当前解释 |
|---|---|---|---|
| 普通分类 | 1/5 成功，Score 32；平均 total Token 12,604 | 1/5 成功，Score 47；平均 total Token 11,661.6 | 总量下降约 7.48%，主要来自输出缩短 |
| 语言分类 | 1/5 成功，Score 30；平均 total Token 12,332.4 | 2/5 成功，Score 46；平均 total Token 11,719.4 | 总量下降约 4.97%，成功数差异尚未隔离执行波动 |
| System 2 对应一次候选生成 | 26,363 Token | 5,476 Token | 候选生成用量下降约 79.2% |
| System 2 新一轮匹配验证 | 历史对应父策略和候选均 0/5，Score 0 | 本轮父策略和 GPT 候选均 0/5，Score 0 | 未测得成绩提升，选择器保留父策略 pi05 |

GPT 分类补测使用 `gpt-6.1-sol / medium`，两任务各 5 个布局；10 个正式回合共 10 次实际高层 HTTP 请求。**两模型对应的技能选择全部一致**，输入文本一致但图像不逐像素相同，因此成绩差异不能直接归因于 GPT 决策更好。

System 2 补测只生成 **1 个 GPT 候选**，复用历史开发证据，父策略与候选各验证 5 个布局。它不是两轮全新自改进，也没有新增 20 布局最终验收。一次欠费停机造成的中断单列记录，没有作为策略 0 分，也没有重新生成候选。

## 仓库结构

```text
upstream/PhysicalRSI/          实验使用的上游代码快照及原许可证
integration/                  实际使用的冻结集成层
experiments/system1_gpt/      GPT 分类补测：代码、协议、请求响应和结果
experiments/system2_gpt/      GPT 自改进补测：候选代码、验证和选择记录
experiments/history/          原生分类、目录消融、恢复、扩展任务、计时与失败诊断
experiments/fixed_input_api/  80/120 次合成输入 API 原件、协议与分析
experiments/mechanism_audit/  版本化提示词、调度和 CPU 机制证据
experiments/public_reference/ 项目 A 公开资料快照，不属于本研究新执行
procedures/historical_server/  历史服务器实验程序，供追溯检查
environment/                  环境版本记录
configs/                      不含密钥的配置示例
tools/                        离线核验工具
docs/                         结论、复现条件与资料范围
provenance/                   来源索引、SHA256 和上传检查记录
```

## 离线查看与核验

阅读 Markdown、CSV 和 JSON 不需要 GPU 或模型 API。克隆后运行：

```bash
python tools/verify_results.py
python tools/verify_research_evidence.py
```

此命令仅复算归档结果和检查文件哈希，不发起付费 API 请求、不启动仿真。

## 证据边界

2026-11-02 仓库补充按已有代码与实验材料核对；未重新运行实验，现有 PPT 未修改。原始记录分散在不同时间和版本中，不能把目录数、副本数和 API-only 当作新的机器人回合。

- GPT-as-Policy 是公开参考项目；跨项目模型、布局及成功率未完全对齐，Token 比值不等于公平条件下的等质量省费倍数。
- `total = input + output`；缓存命中是 input 的子集；reasoning 若已包含在 output，不应重复相加。
- 历史固定 pi05 两任务各 0/10，属于固定父策略的独立验收，不能描述为整个 PhysicalRSI Agent 的成绩。
- 历史失败机制诊断与本次 GPT 候选单独记录；手工边界修订不是系统自主获得的改进。
- 模型权重、完整仿真资产、私密运行配置和全部逐帧数据保留在原服务器。仓库包含必要源码、协议、结果和选定证据，不是整台服务器镜像。

## 上游与许可

PhysicalRSI 固定提交：`90b322a3a362aad14125f36d8ed080ca31daaea6`。源码位于 `upstream/PhysicalRSI`，保留原 `LICENSE`、`NOTICE` 和子模块信息；与研究无关的上游演示 MP4 未重复上传。其他依赖及许可见 [第三方说明](THIRD_PARTY_NOTICES.md) 和 [UPSTREAM.json](UPSTREAM.json)。
