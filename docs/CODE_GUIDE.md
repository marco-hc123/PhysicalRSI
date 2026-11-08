# 代码导览：原项目、实验适配与研究产物

本仓库同时保存上游、历史集成、模型生成候选、人工诊断和核验代码。它们承担不同角色；判断某次运行采用什么实现，应使用该批协议与SHA256绑定，不把当前Git提交或最新适配倒填成旧实验版本。

## 先找你要阅读的代码层

| 层次 | 仓库入口 | 怎样使用 |
|---|---|---|
| 冻结上游 | [upstream/PhysicalRSI](../upstream/PhysicalRSI/)、[版本来源](../UPSTREAM.json) | 理解作者实现；保留原许可证和子模块身份 |
| 历史执行集成 | [framework-validation-v3](../integration/framework-validation-v3/) | 对照早期实验实际适配；不是所有后续批次的最新运行时 |
| System 1模型补测 | [system1_gpt](../experiments/system1_gpt/) | 控制器、请求/响应、同布局结果及分析源程序 |
| 单次System 2模型替换 | [system2_gpt](../experiments/system2_gpt/) | 原生成候选、父/候选验证、选择及历史执行脚本 |
| 反馈生成与早期诊断 | [批次27–31](../experiments/system2_followup_through_20261105/) | baseline/augmented候选、CPU检查和35回合验证 |
| 后续诊断与冻结搜索 | [批次32–43](../experiments/system2_diagnostics_20261106_20261108/) | 各批源码、接口、人工修订、原生回执和深层文本索引 |
| 原始历史实验程序 | [procedures/historical_server](../procedures/historical_server/) | 追溯历史调用与路径，不直接覆盖原目录重跑 |
| 分析与汇报方法 | [周包08_methods](../reports/research_week_20261102_20261108/08_methods/) | 保留制表/分析/制图源码出处；部分依赖原工作区布局 |
| 独立离线核验 | [tools](../tools/README.md) | 检索来源、校验哈希、重算评分与usage，不执行归档策略 |

## 原生执行与选择的对应入口

上游[code_execution.py](../upstream/PhysicalRSI/PhysicalRSI_baselines/robodojo/code_execution.py)与[历史集成版本](../integration/framework-validation-v3/PhysicalRSI_baselines/robodojo/code_execution.py)可用于对照候选执行包装；上游[selection.py](../upstream/PhysicalRSI/PhysicalRSI_core/self_harness/selection.py)用于理解框架选择逻辑。后续研究有逐批冻结的实验选择规则，不能仅凭上游文件推断某批已执行的具体选择。

11月7日发现的“零动作规划拒绝字典转换为RuntimeError”来自本研究适配层，候选因而未进入已有换臂分支。实际修正及[历史归因更正](../reports/research_week_20261102_20261108/06_batch_evidence/40_system2_rejection_contract/20261107_v1/HISTORICAL_CONTRACT_CORRECTION.txt)随批次40保留。旧集成目录原样保存，使差异可审计。

## 如何区分生成候选和人工干预

- 模型生成候选保留原始源码、proposal、请求及usage，源码哈希与原生revision绑定。例如[11月4日候选](../experiments/system2_followup_through_20261105/stages/29_feedback_generation/candidates/)和[11月8日十二份候选](../reports/research_week_20261102_20261108/06_batch_evidence/43_system2_multitask/20261108_v1/native-validation/candidates/)。
- 人工guard旁路、轨迹筛选、夹爪命令、运输目标、循环和包装返回修正按各批协议标注，不能列作模型自主生成或晋升成果。
- 批次42两份含`nonlocal`的第二轮代码因研究准入规则被拒；源代码和[准入审计](../reports/research_week_20261102_20261108/06_batch_evidence/42_system2_search_execution_controls/20261107_v1/native-validation/admission-contract-audit.json)保留，未赋原生零分。
- 批次43的[接口定义](../reports/research_week_20261102_20261108/06_batch_evidence/43_system2_multitask/20261108_v1/native-validation/interfaces/)及[冻结协议](../reports/research_week_20261102_20261108/06_batch_evidence/43_system2_multitask/20261108_v1/native-validation/protocol.json)约束候选能力、预算和准入；其中抓取父策略为研究编写的起点，不能冒称发布官方技能。

## 沿一条证据链阅读

以批次43为例：先读冻结协议的任务、源哈希及选择规则，再看候选源码与接口；用[selection](../reports/research_week_20261102_20261108/06_batch_evidence/43_system2_multitask/20261108_v1/native-validation/selection/)核对为什么保留父策略；随后核查每阶段原始回执及[逐回合账目](../reports/research_week_20261102_20261108/03_data/native_episodes_all.csv)。最后才使用汇总图表。未准入、准备smoke、中断null和复用视图的处理在[结果总表](RESULTS.md)解释。

精选周包用于便携阅读，全部已公开源路径可在证据索引中检索：

```bash
python3 -B tools/read_week_evidence.py --search '43_system2_multitask'
python3 -B tools/read_week_evidence.py --search 'structured_feedback.py'
python3 -B tools/read_followup_evidence.py --search '29_system2_feedback_api'
```

读取器按路径定位精确副本或去重文本对象，并核对原字节哈希；它不会执行找到的历史脚本。[覆盖清单](../provenance/week-coverage-20261108.json)说明未公开或外部保留的材料。

## 可以直接做什么，复跑还需要什么

在仓库根目录可以运行[四项标准库只读核验](../tools/README.md)，查看CSV/JSON、候选与协议，并在下载仓库后打开周包目录中的`index.html`。制图与历史runner保留方法出处，未统一改写成跨机器一键执行程序。

新原生运行还需冻结依赖、Isaac Sim/RoboDojo资产、权重、相同布局与私密服务配置，使用新的输出目录，并明确研究协议。不要运行归档脚本覆盖既有结果；本次展示整理没有触发任何新生成或仿真。详细条件见[REPRODUCE](REPRODUCE.md)，完整目录职责见[仓库地图](REPOSITORY_MAP.md)。
