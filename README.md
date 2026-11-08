# PhysicalRSI：仿真复现、Token与技能改进研究

**复现PhysicalRSI的有限任务流程，解释语言开销，并追踪System 2为何没有稳定超过父策略。**

这是个人研究与证据仓库，基于[PhysicalRSI上游项目](https://github.com/PhysicalRSI/PhysicalRSI)。研究包括原生任务对照、Token与耗时分析、模型替换、失败机制诊断、受控人工干预，以及冻结选择后的独立布局验收。GPT-as-Policy仅作公开数据参照，没有重新部署或运行。

**当前观察范围：2026-11-08本次实验室取证时刻。** 原始代码、失败记录、得分与出处均按批次保留；本次仓库整理没有启动新实验或模型请求。

## 研究沿着什么问题推进

```mermaid
flowchart LR
    A[有限范围原生复现] --> B[Token与耗时拆分]
    B --> C[System 2负结果定位]
    C --> D[接口与动作链受控干预]
    D --> E[冻结候选搜索与选择]
    E --> F[两任务与独立布局验收]
```

这条路线从“能否复现、为何少用Token”，推进到“候选实际执行到哪里、局部修正能否形成任务收益”。[完整研究总览](docs/RESEARCH_OVERVIEW_ZH.md)串联结论与证据；[研究路线图](docs/RESEARCH_ROADMAP.md)区分已完成阶段和仍待回答的问题。

## 目前得到了什么

| 研究问题 | 当前证据支持的结论 | 需要保留的边界 |
|---|---|---|
| 为何语言Token较少 | 被测分类Agent每回合一次高层选择，后续由本地代码/VLA执行；目录精简还能降低单次输入 | 本地控制仍有计算成本；跨项目模型、质量与缓存条件不同 |
| 能完成哪些任务 | 固定code、Agent和有限扩展任务出现原生成功；不同任务与路线差异明显 | 已完成有限复现，尚非官方完整benchmark或同等质量比较 |
| System 2是否产生收益 | 历史轮次、模型替换及11月7–8日冻结搜索均保留各自父策略 | 不能写成未做System 2，也不能把所有候选都概括为零分 |
| 失败定位到什么 | 感知判断、规划目标、轨迹执行、夹爪命令、包装返回和任务覆盖分别影响动作推进 | 修好局部环节、完成调用或物体送达代理不等于整任务成功 |
| 第二任务是否改变结论 | 11月8日抓取候选存在原生成功，但没有单个候选超过开发父策略3/5 | 两条件各3个生成样本；独立父策略各有一例中断，不能补零 |

详细数字、对应分母和来源见[结果总表](docs/RESULTS.md)。截至当前，低语言开销已有机制与账目依据，**本期仍未选出优于父策略的新技能**；两者需要分别评价。

## 原生质量与生成改进分开读

历史分类参考矩阵为2任务×4路线×5布局。固定code在普通/语言分类分别成功2/5、1/5，历史Qwen Agent分别1/5、1/5；11月2日GPT Agent补测分别1/5、2/5。图像与模型配置并非严格单变量，得分差别不能直接归因于高层选择更好。

11月8日增加分类与抓取两任务，每任务两反馈条件、每条件3候选。分类六候选全0分；抓取basic候选均分60/60/40，执行反馈40/60/60，父策略均分60，按冻结规则全部保留parent。独立父策略分类0/4成功、抓取1/4成功；各计划5布局，另1例跟踪中断无终态评分。相同父策略视图共用一次验收，不能重复计数。

[历史任务矩阵与Token对照](docs/RESULTS.md) · [最新批次32–43](experiments/system2_diagnostics_20261106_20261108/README.md) · [本周逐回合数据](reports/research_week_20261102_20261108/03_data/native_episodes_all.csv)

## 按目的进入仓库

| 你想了解 | 从这里开始 |
|---|---|
| 研究问题、方法和完整进展 | [研究总览](docs/RESEARCH_OVERVIEW_ZH.md) · [路线图](docs/RESEARCH_ROADMAP.md) |
| 各实验结论与限制 | [结果总表](docs/RESULTS.md) · [按问题查证据](docs/EVIDENCE_INDEX.md) |
| 上游、适配代码和模型候选分别在哪里 | [代码导览](docs/CODE_GUIDE.md) · [仓库地图](docs/REPOSITORY_MAP.md) |
| 原始实验与每次改动 | [实验入口](experiments/README.md) · [科研日志与讨论](research/README.md) |
| 准备汇报或离线阅读 | [完整周报告、图表与精选媒体](reports/README.md) |
| 核验结果或准备复跑 | [复现条件](docs/REPRODUCE.md) · [只读工具](tools/README.md) |
| 追溯文件来源和上传边界 | [来源覆盖](provenance/week-coverage-20261108.json) · [资料范围](docs/SCOPE.md) |

## 证据组织与当前账目

11月2–8日已核对账目为 **312个有原生终态评分的执行、44次API请求、562,306 Token**；这不是项目全部历史执行的总数，也不是统一成功率分母。11月8日89个评分执行含1个准备smoke，另有2次中断、分数未知。CPU探针、未准入候选、复用对照和选择视图分别记账。

本仓库公开冻结上游、历史集成层、各批候选与诊断程序、逐回合结果、请求用量、科研记录及可验证的文本证据。完整权重、环境、原视频和逐帧大文件继续保存在实验室；周包中的媒体是注明来源的精选示例。原始成功、失败、接口说明错误和后续更正同时保留。

```bash
# 在仓库根目录离线核验；不启动模型或仿真
python3 -B tools/verify_results.py
python3 -B tools/verify_research_evidence.py
python3 -B tools/verify_followup_evidence.py
python3 -B tools/verify_weekly_package.py --package reports/research_week_20261102_20261108
```

原生复跑还需要相同依赖、权重、资产、布局和新的输出目录；归档runner不是一键安装入口。上游许可证和第三方出处见[THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES.md)。

[更新记录](CHANGELOG.md) · [11月5日结果快照](docs/archive/RESULTS_through_20261105.md) · [本次更新前的首页](docs/archive/README_before_20261108.md)
