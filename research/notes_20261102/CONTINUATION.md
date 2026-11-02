# PhysicalRSI 研究记录续接

更新时间：2026-11-01 20:13（北京时间）。

- **目标**：按 expert 模式维护已有阶段证据，确定后续可验证问题。
- **服务器**：gpuserver3；SSH 别名 physicalrsi-lab；用户 joey_tr。
- **研究根目录**：`/mnt/data/joey_tr/physical-RSI`。
- **记录目录**：`/mnt/data/joey_tr/physical-RSI/research`。
- **当前议题**：DISC-2026W44-001，stage-evidence-review，Open。
- **已完成**：用户模式/范围确认，idea 与 method，通俗说明，全部顶层结果导航，43 条可访问历史批次索引，四组历史日志，时间线与流水。
- **实验状态**：本次新实验、API 请求和 GPU 作业均为 0；历史记录按原件时间解释。
- **本次任务启动的长期进程/实验会话**：无；初始化程序为短时 SSH 命令，执行审计在下方结果目录。
- **初始化审计与模板备份**：`/mnt/data/joey_tr/physical-RSI/result/research_tool_initialization_20261101T120523Z`；完整命令日志和 status.json 留存。
- **结果与日志**：[HISTORY.md](HISTORY.md)、[本周实验导入](LOGS/2026-W44.md)、[操作流水](LOGS/2026-W44-activity.md)。
- **未决事项**：下一阶段干预、预算、任务/布局划分与验收标准；既有证据缺口见 evidence/unknowns-and-evidence-gaps.csv。历史原命令与所有环境字段未在本次逐条重验。
- **下一步**：读当前议题与失败机制证据，提出一个受控验证方案，再由用户确定研究决策。

会话入口：在本目录运行 `python3 -B tools/session_check.py`。开始任何新实验前重新核对对应环境、路径与实际进程；历史成功状态和 PID 不是当前运行证明。


## 补充归档完成 · 2026-11-02 19:09

- 当前任务：四份2026-11-02补充ZIP已解压并归档，登记EXP-2026W45-001、EXP-2026W45-002；没有重跑任何实验。
- 当前主机/位置：gpuserver3，/mnt/data/joey_tr/physical-RSI；按研究主题查阅。
- 新结果：result/24_system1_model_swap/37_gpt61sol_supplement_20261102、result/25_system2_model_swap/38_system2_gpt61sol_20261102。
- 首读文档：[新增证据](evidence/model_swap_20261102/README.md)、[结论与汇报添加位置](evidence/model_swap_20261102/REPORT_INTEGRATION.md)。
- 导入/备份/日志：result/26_supplement_import/20261102T105827Z；原四ZIP与486成员保留，完整性清单独立保存。
- 去重：四个包是两套实验；System1旧对照10行不新计，System2旧开发10例复用；1次中断评分未知。
- 活跃会话/实验：本任务只运行短时SSH、scp及离线登记脚本，无新长期进程；API/训练/仿真/GPU新增0，不改变已有任务状态。
- 限制：新包无执行视频；未随包的逐步证据原件未做全量重验。旧完整ZIP尚未加入这次材料，勿当作最新全量包。
- 下一步：制作汇报先读整合说明；需要视频和完整新执行证据时另补。下一轮先冻结反馈/动作契约干预与独立布局验收；未自动开展。
- 当前议题仍为DISC-2026W44-001 Open，研究目标和主指标不变；last_retro已更新2026-W45。
