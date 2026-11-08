# PhysicalRSI 仿真复现与 Token 消耗分析

本仓库记录本人基于 [PhysicalRSI](https://github.com/PhysicalRSI/PhysicalRSI) 开展的仿真复现、Token 用量分析，以及将高层模型由千问替换为 GPT 的补测。已完成实验整理至 **2026-11-05**；仓库更新于 **2026-11-07**。

这是个人复现与实验记录仓库。上游原始代码、本人使用的集成程序、模型生成候选和实验输出分别保留出处。原项目的功能与本次实际验证的范围应分开阅读。

## 从这里开始

- **看结论**：[最新结果](../../docs/RESULTS.md)、[完整研究总览](../../docs/RESEARCH_OVERVIEW_ZH.md)。
- **找实验**：[11月4–5日后续批次](../../experiments/system2_followup_through_20261105/README.md)、[按问题查证据](../../docs/EVIDENCE_INDEX.md)。
- **看过程**：[科研问题、讨论与日志](../../research/README.md)、[更新记录](../../CHANGELOG.md)。
- **核验或复现**：[离线核验与依赖](../../docs/REPRODUCE.md)。
- **理解目录**：[仓库地图](../../docs/REPOSITORY_MAP.md)、[上传范围](../../docs/SCOPE.md)。
- **查历史汇报**：[报告、图表与PPT](../../reports/README.md)，各自保留原日期与统计范围。

## 最新进展：11月4–5日

11月4日完成旧候选CPU诊断、H100离线验收和基线/增强反馈各3个候选生成，6次请求共64,674 Token。随后完成150项候选CPU检查。离线探针不是机器人任务回合。

11月5日完成7条件×5历史布局的35个有效原生回合：完整成功0；增强候选两例各得15/100，均为layout4。增强组三候选15例均分2/100，基线生成代码15例均分0，神经父pi05另列5例。**局部得分已经出现，稳定改进和独立泛化尚未建立。**

首次approach拒绝由基线12/15降为增强0/15，完成approach为9与50；候选动作推进改变，但任务仍未完整完成。augmented_3的动态抬升判断与读取器固定名义Z不匹配，是局部机制证据，不能直接断言真实抓取失败或唯一根因。未重跑正式选择器，也没有候选晋升。

[后续实验、逐回合数据与原件](../../experiments/system2_followup_through_20261105/README.md) · [最新结论和限制](../../docs/RESULTS.md) · [独立核验](../../provenance/followup-verification-20261107.json)

## 截至11月2日的基线结果与机制

以下按现有汇报的主线组织：**研究目标与机制 → 原生任务表现 → Token 与缓存 → System 2 → 目录消融与运行时间 → 下一步**。历史实验与 GPT 补测分别标明；整理日期为 2026-11-04，实验数据截至 2026-11-02。

### 1. 研究目标与复现范围：已经验证了什么

本研究希望回答：**PhysicalRSI 如何利用已有技能减少高层模型调用；这种执行方式在任务质量、Token 与运行时间上有什么收益和限制；System 2 能否进一步改进技能？**

- **跨项目分工**：GPT-as-Policy（项目 A）仅使用官方公开说明和数据；PhysicalRSI（项目 B）进行实际复现与测量。没有重新部署或运行项目 A。
- **执行机制**：在本次分类实验中，System 1 的 Agent 每回合进行一次高层规划，选择技能组合与操作，后续由本地 code／VLA 执行多个机器人动作。System 2 在回合之间生成候选代码，再通过验证和选择决定是否替换父策略；本研究未训练或更新 VLA 权重。
- **已完成范围**：已有技能与 Agent 的原生任务对照、对应任务的 Token 核算、目录精简消融、历史两轮 System 2、独立最终验收、状态恢复、失败机制诊断，以及 GPT 模型替换补测。这里的 native 指调用 RoboDojo 原生仿真评测；是否产生动作、是否正常完成及是否取得评分分别记录。
- **条件边界**：固定 PhysicalRSI `90b322a` 及记录在案的集成补丁，使用 RoboDojo、ARX X5、Isaac Sim 5.1、RGB 观测与 L20 GPU。完成的是有限任务和布局的复现，**尚未完成官方完整 RoboDojo 评分复现，也未证明集成层与作者完整系统数值等价**。

截至11月2日的阶段结论是：**已观察到较低的语言Token用量，当时的正式System 2选择未测得得分提升。** 后续11月5日候选出现局部部分得分，但完整成功与稳定提升仍未建立，见上方最新进展。

来源：[复现条件](../../docs/REPRODUCE.md)、[冻结协议](../../experiments/history/protocol_freeze/protocol.json)、[完整研究总览](../../docs/RESEARCH_OVERVIEW_ZH.md)。

### 2. 原生任务表现：先确认机器人能完成多少任务

正式参考矩阵为 **2 个分类任务 × 4 条路线 × 5 个布局，共 40 个原生回合**。每个单元格分别报告“完全成功数；平均 Score”。Score 为归一化部分得分乘以 100，满分 100；部分得分与完全成功率不是同一个指标。

| 执行路线（历史参考） | 普通分类 `classify_objects` | 语言分类 `classify_objects_by_language` |
|---|---:|---:|
| 固定 `pi05` | 0/5；Score 0 | 0/5；Score 0 |
| 固定 `pi05-sparse-memory` | 0/5；Score 17 | 0/5；Score 2 |
| 固定 code 技能 | 2/5；Score 51 | 1/5；Score 40 |
| Qwen Agent 选择技能 | 1/5；Score 32 | 1/5；Score 30 |

在这组小样本中，Agent 未超过固定 code 技能；固定技能运行时不消耗高层语言 API Token，但仍消耗本地推理、控制与仿真资源。两种 VLA 使用不同的发布权重，不能把二者差异当成纯粹的 memory 开关消融。

另完成三项有限扩展任务，各 5 个正式布局；每任务的预跑单独记录，不加入下表分母。

| 扩展任务 | 完全成功数 | 平均归一化部分得分（满分 1） |
|---|---:|---:|
| `stack_bowls` 叠碗 | 1/5 | 0.20 |
| `cover_blocks` 覆盖 | 3/5 | 0.64 |
| `insert_tubes` 插管 | 4/5 | 0.88 |

这些结果说明任务间表现差异明显，不能用某一任务的成功或失败概括整个框架；也不能与不同布局、样本量和配置下的官方榜单直接对齐。更早的 `general_pickup` 最小闭环与开发对照共 59 个案例，其中 58 个有效原生结果、1 次规划失败，另有 6 次 API-only；它们与上面的冻结参考矩阵分开，不能合并成一个成功率。详见[早期开发与逐阶段核查](../../reports/research_archive_20261101/05_逐阶段完整复核与补充分析.md)。

来源：[40 回合参考矩阵](../../reports/evidence/tables/system1_reference_matrix.csv)、[三项扩展明细](../../reports/evidence/tables/limited_extension_formal.csv)、[任务汇总](../../experiments/history/task_extension_and_final_test/exports/task-summary.csv)。

### 3. Token、调用与缓存：如何解释跨项目差距

先比较对应的普通／语言分类任务，再区分原始 total 与去缓存账目。项目 A 的每个任务／方法按 5 次公开尝试核算用量，B 的每个分类任务为 5 个实测回合。下表范围来自两个任务及 A 的两种执行模式。

| B 的实测条件 | A/B 平均 total Token 比值范围 | A/B 去缓存指标比值范围 |
|---|---:|---:|
| 历史 Qwen Agent | 约 888–3,050 倍 | 约 27.59–75.88 倍 |
| 后续 GPT Agent 补测 | 约 960–3,209 倍 | 约 27.59–79.84 倍 |

**这是有条件的账目比较，不是等质量的节省比例、费用倍数或因果改进幅度。** A 的输入中约 97%–98% 为缓存命中；A、B 的模型、推理配置、布局和成功率不同。A 普通分类 Hybrid／Direct 分别成功 3/5、5/5；语言分类 Hybrid 为 1/5，Direct 是 5 次公开尝试中 4 次可评分、2 次成功，另 1 次评分未知但已发生的 Token 保留在成本统计中。B 的表现见本页对应表格。

统一口径为 `total = input + output`，去缓存指标为 `input − cached input + output`。缓存输入是 input 的子集，reasoning 若已含在 output 中就不重复相加；“去缓存指标”是账目重算，**没有另做关闭缓存的运行实验**。

机制上，B 的分类 Agent 每回合只有一次实际高层 HTTP 请求，之后使用本地技能；A 公开记录中的 action segments 不能直接视为 HTTP 请求次数。因此，现有证据支持“高层决策与低层技能执行分离有助于减少语言调用”的解释，但尚未隔离模型、缓存、任务完成程度等因素各自的贡献。

**后续 GPT 模型替换补测**保留原任务、布局和技能目录，使用 `gpt-6.1-sol / medium`，新增 10 个正式原生回合、10 次实际高层 HTTP 请求：

| 任务 | 历史 Qwen Agent | GPT Agent 补测 | 平均 total Token 变化 |
|---|---|---|---:|
| 普通分类 | 1/5 成功；Score 32；12,604 Token | 1/5 成功；Score 47；11,661.6 Token | −7.48% |
| 语言分类 | 1/5 成功；Score 30；12,332.4 Token | 2/5 成功；Score 46；11,719.4 Token | −4.97% |

两组输入用量接近，总量下降主要来自输出缩短。**两模型对应的技能组合与操作 10/10 一致**；请求文本一致，但图像并非逐像素相同，且未做交错重复。因此不能把成功数或 Score 的差异归因为 GPT 的高层决策更好。普通分类的缓存命中也发生变化，total 下降不意味着去缓存指标同步下降。

来源：[历史跨项目复算表](../../reports/evidence/tables/matched_comparison_recomputed.csv)、[公开尝试与可评分分母](../../reports/evidence/tables/public-A-per-task-reviewed.csv)、[Token 分项](../../reports/evidence/tables/matched-token-components.csv)、[GPT 分类补测完整结果](../../experiments/system1_gpt/RESULTS_ZH.md)。

### 4. 历史System 2：完成了改进流程，当时未测得得分收益

System 2 的验证链为“开发反馈 → 生成候选 → 接口检查 → 原生匹配验证 → 选择父策略或候选”。以下是验证集结果，**接口检查通过不等于动作完整执行，更不等于完成任务**。

| 实验轮次 | 父策略 pi05 | 生成候选 | 选择结果 |
|---|---|---|---|
| 历史 Qwen 第 1 轮 | 0/5 成功；Score 0 | 0/5 成功；Score 0 | 保留父策略 |
| 历史 Qwen 第 2 轮 | 0/5 成功；Score 0 | 0/5 成功；Score 0 | 保留父策略 |
| GPT 新增一轮匹配验证 | 0/5 成功；Score 0 | 0/5 成功；Score 0 | 保留父策略 |

历史两轮的生成、验证和选择均已完成；**正确结论是“未观察到自改进收益”，不是“尚未开展 System 2”或“所有候选均未进入执行”**。

生成成本与机器人验证分开核算：历史两次正式候选生成共 51,070 Token；其中与 GPT 补测对应的一次请求为 26,363 Token，GPT 的一次新候选生成为 5,476 Token，下降约 **79.23%**。这只是一次候选生成的用量差异，不能解释为整个机器人实验节省 79.23%，也未带来本轮得分提升。若连同历史接入和失败提案，四次唯一生成合计 405,876 Token；正式两次的 51,070 已包含其中，不能重复相加。

GPT 补测仅生成 **1 个新候选**，复用历史开发证据，重新完成父策略与候选各 5 个布局；不是两轮全新自改进，也没有新增 20 布局最终验收。一次基础设施停机中断单列为评分未知，恢复后只补未完成回合，没有重新生成候选。历史提案复用、逻辑回合和实际执行分别记账，不按目录数重复累计。

来源：[历史两轮汇总](../../reports/evidence/tables/system2_rounds.csv)、[提案账目](../../experiments/history/task_extension_and_final_test/final-review/system2-proposal-details.csv)、[阶段核算](../../experiments/history/task_extension_and_final_test/final-review/phase-accounting-final.csv)、[GPT System 2 补测](../../experiments/system2_gpt/RESULTS_ZH.md)。

### 5. 独立验收、恢复与诊断：零分发生在哪里

**独立最终验收**评估的是最终保留的固定 `pi05`：普通分类 0/10、语言分类 0/10，共 20 个独立布局。它不是整套 Agent 的成绩，也不能与前面的 Agent 1/5 混作一组。

**状态恢复**完成了保存／加载、跳过已完成回合、拒绝无效候选和回滚等检查，并执行 baseline／restored 各 1 次原生回合，两次均得分 0。这证明本次软件状态恢复路径可以继续运行，不证明任务能力提高。

**机制诊断**包含 9 次原生启动：5 次自然结束得分 0，4 次异常终止的最终任务评分未知；另有 24 次离线规划检查，不计作机器人任务回合。代表性发现包括：

| 观察与干预 | 已有证据支持的结论 | 尚不能得出的结论 |
|---|---|---|
| 历史第二轮候选用篮筐中心 x/y 各 ±0.2 m 判断已入筐；布局 2 原始策略没有执行移动 | 判定范围过宽会导致错误跳过；修订后出现 5 次 approach、4 次 gripper 调用，得分仍为 0 | 不能说修正边界已完成抓取，也不能用此原因解释第一轮或所有布局 |
| 固定目标的离线规划：20 cm 高度为 0/3 可行，降低到 15／10／5 cm 后分别为 3/3 | 目标设置影响规划可行性 | 规划可行不等于轨迹被正确执行或任务成功 |
| 发现无可行路径、执行预算不足、轨迹跟踪中止，以及新类别映射异常 | 失败分布在判断、规划和执行等不同位置，需要逐段检查 | 消除一个异常或增加动作，不能直接当成 System 2 获得收益 |
| 候选生成反馈缺乏上一失败候选的细粒度 RPC 轨迹 | 值得受控测试更完整的失败反馈 | 不能仅凭 `current_code` 为空认定接口丢消息，也尚未证明增强反馈必然提高得分 |

篮筐大范围判断可在历史第二轮模型生成候选中直接定位；它不能直接归为官方发布固定技能中已有的同一错误。现有证据也不足以把全部零分统一归为实验操作错误或 PhysicalRSI 方法本身无效。人工诊断修订与系统自主生成的改进必须分别报告。

来源：[独立验收明细](../../experiments/history/task_extension_and_final_test/exports/independent-final-episodes.csv)、[恢复结果](../../experiments/history/state_recovery/step6-results.json)、[诊断对照原件](../../experiments/history/system2_diagnostics/verified-control-results.csv)、[离线规划表](../../reports/evidence/tables/planning_feasibility.csv)、[候选原件与执行档案](../../experiments/raw_execution_archive/README.md)。

### 6. 目录精简消融：单次输入为什么能够减少

“目录精简”指向高层模型提供与当前任务相关的技能描述，而非完整技能目录。它检验 PhysicalRSI 内部的提示词组织方式，**不是 A、B 两项目的公平对比**。

| 实验层级 | 设计与分母 | 观测结果 | 解释边界 |
|---|---|---|---|
| 固定输入 API 对照（Qwen3-VL-Plus） | 20 个合成场景 × 2 条件 × 3 次重复，共 120 次调用 | input −67.31%；total −66.87%；HTTP 时间 −31.65%；120/120 通过接口与输出契约检查 | 没有机器人执行；输出格式合格不等于任务成功 |
| `general_pickup` 原生目录对照 | 5 个开发布局 × 3 次重复 × 2 条件，共 30 次尝试；29 次完成 native | input −80.20%；total −79.01%；完整目录成功 6/15，精简目录 5/15 | 一例 Agent 规划输出失败保留在分母；未证明任务质量不下降或完整墙钟同比改善 |

原生目录消融的 Token 降幅按各 15 次尝试核算，包含未进入 native 的那次规划失败；不能只挑选 29 次完成回合，也不能将重复运行算作 15 个独立布局。该投影还恢复了静态任务标签与代码身份，并非仅缩短同义文本。**约 80% 的输入降幅只属于这项自身消融，不代表跨项目节省比例。**

此前的 80 次 API 探索用于检查提示词、投影及输出契约，其中 HTTP 成功与输出契约有效需要区分；不与后续 120 次固定输入对照混作同一统计组。更早的代码／提示词审计、调度分析与 CPU 代理实验是机制准备证据，不计作真实机器人评分或实测语言 API Token。

来源：[80／120 次 API 原件入口](../../experiments/fixed_input_api/README.md)、[120 次原始用量复算](../../reports/evidence/tables/api120-raw-recomputed.json)、[目录消融汇总](../../reports/evidence/tables/catalogue_ablation.csv)、[逐次原生尝试](../../experiments/history/catalogue_ablation/cases.csv)、[机制审计](../../experiments/mechanism_audit/)。

### 7. 运行时间：Token 少不代表整任务同比加速

历史 Qwen Agent 正式矩阵中，每任务 5 个布局的均值如下。`reset-to-result` 是从重置到结果的计时窗口，不包含整套安装、模型加载或 System 2 生成流程，不能与物理仿真时长混用。

| 任务 | 平均 reset-to-result | 平均 API 时间 | API 占上述窗口比例 |
|---|---:|---:|---:|
| 普通分类 | 236.53 s | 17.40 s | 7.36% |
| 语言分类 | 214.76 s | 12.27 s | 5.71% |

在这两组中，语言 API 只占所测执行窗口的一小部分；其余还包括技能推理、控制、渲染、通信和未细分开销，不能全部称作 GPU 计算时间。因此降低 Token 或 API 延迟，并不必然按相同比例缩短机器人回合。

针对性 cold／continuous 计时补测共 **3 对运行**，平均 reset-to-result 分别约 231.92 s／236.71 s，未观察到连续运行更快；样本少且没有清除所有系统、GPU 和 API 缓存，只能描述这组结果。GPT 补测的 API 计时还包含客户端与 SSH 转发，不能据此推断供应商纯接口速度。

**项目 A 的完整墙钟时间仍未知，因此当前不给出跨项目加速倍数。**

来源：[分类分项计时](../../experiments/history/task_extension_and_final_test/comparison-analysis/timing-interval-summary.csv)、[三对针对性计时](../../experiments/history/task_extension_and_final_test/final-review/targeted-timing-pairs.csv)、[计时与 Token 解释边界](../../experiments/history/task_extension_and_final_test/final-review/token-time-interpretation-zh.txt)。

### 8. 当前结论与下一步：从低 Token 走向可验证的改进

当前研究已将问题分成三层：**调用机制可以解释部分 Token 差异；原生任务质量必须单独衡量；System 2 的流程完成尚未转化为得分收益。** 模型替换降低了本轮生成用量，但没有解决候选的验证零分问题。

下一步优先围绕 System 2 做可归因的小实验，而不是直接扩大调用次数：

1. **定位并验证执行契约**：逐段记录观察、几何判断、规划、动作完成和失败反馈；检查可达／不可达请求、坐标与尺寸语义、控制步频和终止条件。先确认候选实际执行到哪一步。
2. **单变量修正已知问题**：固定候选、布局、评分与预算，只改边界判断或某一执行问题；同时检查“局部行为是否修好”和“最终任务得分是否提高”。
3. **检验反馈改进假设**：保持模型、生成次数、可修改范围和验证预算一致，对比原有反馈与加入候选代码、逐步失败记录的反馈；以完成率、成功率、部分得分、Token 和墙钟共同验收，再使用新的保留布局确认收益。

这部分为下一轮计划，不计为已取得的性能改进。各阶段原件、重复证据和 API-only 记录分开保留；若旧摘要与原始表格表述冲突，本页采用核对后的原始记录口径。

来源：[按研究问题组织的证据导航](../../docs/EVIDENCE_INDEX.md)、[下一轮实验草案](../../reports/evidence/tables/next-experiments-preregister-draft.csv)。

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

PhysicalRSI 固定提交：`90b322a3a362aad14125f36d8ed080ca31daaea6`。源码位于 `upstream/PhysicalRSI`，保留原 `LICENSE`、`NOTICE` 和子模块信息；与研究无关的上游演示 MP4 未重复上传。其他依赖及许可见 [第三方说明](../../THIRD_PARTY_NOTICES.md) 和 [UPSTREAM.json](../../UPSTREAM.json)。

补充资料：参见[原始执行档案](../../experiments/raw_execution_archive/README.md)与[二次资料核对报告](../../provenance/SECOND_REVIEW_20261102_ZH.md)。这是已有实验的原始证据补齐，不增加实验样本数。
