# 实验与证据

[完整研究总览](../docs/RESEARCH_OVERVIEW_ZH.md) · [研究路线图](../docs/RESEARCH_ROADMAP.md) · [代码导览](../docs/CODE_GUIDE.md)

| 范围 | 入口 | 计数边界 |
|---|---|---|
| 11月6–8日诊断、搜索及两任务反馈 | [新增批次32–43](system2_diagnostics_20261106_20261108/README.md) | 257新增有评分执行，11月8日另2中断；26次API |
| 11月4–5日System 2后续 | [后续总览](system2_followup_through_20261105/README.md) | 6次生成、35有效原生回合，同5个历史布局 |
| 11月2日System 1模型替换 | [分类补测](system1_gpt/RESULTS_ZH.md) | 10新正式回合，旧对照不重复算新 |
| 11月2日System 2模型替换 | [候选补测](system2_gpt/RESULTS_ZH.md) | 1新候选、父/候选各5，另1基础设施中断 |
| 固定输入API目录实验 | [80/120请求](fixed_input_api/README.md) | 合成输入接口检查，非机器人成功率 |
| 静态代码和调度机制 | [机制审计](mechanism_audit/README.md) | 静态/CPU代理与真实API分开 |
| 历史原生对照、恢复和诊断 | [按问题导航](../docs/EVIDENCE_INDEX.md) | 按各批协议解释，不合并总成功率 |
| 历史原件 | [文本库](evidence_archive/README.md)、[执行补库](raw_execution_archive/README.md) | 无损恢复、原日期不变 |
| 项目A公开参照 | public_reference/project_a | 公开数据及静态审计，本研究未运行A |

生成候选、人工诊断副本、上游固定技能和VLA权重分开标注。当前结论见[RESULTS](../docs/RESULTS.md)。
