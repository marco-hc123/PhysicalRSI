# 仓库地图

[完整研究总览](RESEARCH_OVERVIEW_ZH.md) · [研究路线图](RESEARCH_ROADMAP.md) · [代码导览](CODE_GUIDE.md)

本仓库为个人PhysicalRSI有限复现与研究证据库。当前整理范围截止2026-11-08本次服务器取证时刻；保留现有目录和冻结实验身份，以统一导航区分当前结论、历史记录和原件。

| 位置 | 用途 | 入口 |
|---|---|---|
| docs | 当前结论、研究机制、证据导航、复现条件 | [最新结果](RESULTS.md)、[复现](REPRODUCE.md) |
| experiments | 各批协议、候选、逐例数据、无损原件 | [实验入口](../experiments/README.md) |
| research | 研究问题、讨论、模板周志、逐日记录 | [科研记录](../research/README.md) |
| reports | 带日期的历史报告、图表、视频与PPT | [报告入口](../reports/README.md) |
| tools | 标准库只读证据检索与复算 | [工具说明](../tools/README.md) |
| provenance | 来源指纹、范围、历史版本与整理审计 | [本次覆盖](../provenance/week-coverage-20261108.json)、[核验](../provenance/week-verification-20261108.json) |
| upstream/PhysicalRSI | 固定上游快照 | 根UPSTREAM.json及原许可证 |
| integration/framework-validation-v3 | 历史冻结集成实现 | 与上游区别见复现说明 |
| procedures/historical_server | 当时执行/整理脚本 | 历史追溯，非当前一键安装入口 |
| environment、configs | 依赖记录和配置样例 | 不含完整环境、权重与实际凭据 |
| third_party | 外部依赖许可 | [第三方来源](../THIRD_PARTY_NOTICES.md) |

阅读顺序：当前结论 → 对应研究问题 → 批次协议 → 逐例结果 → 原件哈希。核验现有数据先运行只读工具；实际重新运行仿真另外需要冻结依赖与新输出目录。

旧PPT、暂停和草案保持原日期。目录数、原件数、视频数、CPU探针与原生回合不互相替代。


本次新增的主要入口：`experiments/system2_diagnostics_20261106_20261108/`保存批次32–43与读取指引；`reports/research_week_20261102_20261108/`保留完整可携带周包；`research/notes_20261108/`保存接续模板科研档案。旧`system2_followup_through_20261105/`与`notes_20261107/`维持原日期，避免把历史快照当作当前全项目结论。
