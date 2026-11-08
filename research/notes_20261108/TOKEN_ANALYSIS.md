# PhysicalRSI 为什么在已测任务中使用更少的语言 API Token

研究主线由用户明确：只复现 PhysicalRSI；第一个项目 GPT 6 Astra as an Embodied Policy（历史资料简称 GPT-as-Policy）作为公开参照，不部署或运行它。全部已完成实验结果统一从实验室研究目录查阅。

## 1. 结论及适用范围

目前最有证据的结构解释是**语言模型介入控制的粒度不同**。已测 PhysicalRSI 分类参考在 episode 开始时做一次高层技能选择，随后由本地 VLA/代码/规划执行。第一个项目的直接模式持续根据观察选择动作，混合模式审阅并可能纠正 pi05 动作。重复观察、历史上下文、推理输出与缓存统计共同影响语言接口账目。

这解释了差距的方向，但当前不能把跨项目 888–3050 倍的描述性 total Token 比值全部归因于某一项。任务成功率、模型、tokenizer、布局与停止条件不同，且第一个项目逐 HTTP 请求数尚不可核实。

## 2. 两个项目的职责

| 项目 | 本研究的动作 | 证据用途 |
|---|---|---|
| A：用户提供的公开项目 | 阅读页面、固定公开结果与源代码 | 描述执行机制、Token 构成和同名任务参考数据 |
| B：PhysicalRSI | 使用已有复现与实测结果；必要时另拟受控补充验证 | 提供实际调用、原生任务表现、执行路径和目录消融证据 |

[A 的项目入口](https://anonymous-report-421.github.io/public-website/?lang=en&view=1)。历史取证中页面正文未直接完整抓取，改核对其[官网仓库说明](https://github.com/anonymous-report-421/public-website/blob/main/README.md)及[已固定版本的源仓库说明](https://github.com/anonymous-report-421/GPT-as-Policy/blob/8f3d362b077d8efb77e2a7274d5b2c20e2243846/README.md)。本轮数值沿用已固定的原始公开数据并离线复算，没有重新访问线上结果。

## 3. 先明确 Token 的账目

对所使用的供应商字段：

- `total = input + output`
- `uncached_input = input - cached_input`
- `uncached_metric = input - cached_input + output`
- 缓存输入是 input 的子集，reasoning 若包含在 output 内也不再加一次。
- 单个任务的总量是该任务全部实际请求的 input 与 output 之和；请求数、每次上下文、输出和重试均影响结果。

VLA 动作、运动规划、图像处理、仿真与本地代码消耗 CPU/GPU 等资源，但没有作为供应商语言 API Token 计数。因此低语言 Token 不直接表示总算力低。既有权重与技能开发、System 2 提案/验证成本也需要另列，不能隐去后宣称完整生命周期成本更低。

## 4. 现有同名任务数据

每个 A 模式/任务及 B 任务组均 n=5。两种 A 模式复用同一 B 任务组，B 实际为两组共 10 个 episode。

| 任务 | A 模式 | A 每例 total | B 每例 total | A/B total | A/B 未缓存指标 | A 成功 | B 成功 |
|---|---|---:|---:|---:|---:|---:|---:|
| classify_objects | mix | 11,193,280.4 | 12,604.0 | 888.07 | 38.04 | 3/5 | 1/5 |
| classify_objects | gpt | 22,906,180.8 | 12,604.0 | 1817.37 | 51.06 | 5/5 | 1/5 |
| classify_objects_by_language | mix | 14,423,783.8 | 12,332.4 | 1169.58 | 27.59 | 1/5 | 1/5 |
| classify_objects_by_language | gpt | 37,611,460.2 | 12,332.4 | 3049.81 | 75.88 | 2/5 | 1/5 |

来源：[历史比较表](evidence/matched_comparison_recomputed.csv)、[本次离线复算](evidence/token_analysis_recomputed.json)。A 的固定结果版本为 `8f3d362b077d8efb77e2a7274d5b2c20e2243846`，原 `public_results/data.json` SHA256 为 `0c4be006a2a0dc1ca2559e4421c45680eec94d466f390ea34b2ea055af9bd74e`。B 是既有 Run24 v3 分类 Agent 参考组，原件在实验室 `result/15_system1_diagnostics_memory/24_steps23_20261030T013742Z_v3/`。

## 5. 为什么较少：逐项区分证据

### 5.1 一次较完整的技能选择，承接大量本地控制

B 两个分类参考组每例实际 HTTP 均为 1。`skill_model._start_episode` 在开始时调用 planner，后续观测进入已绑定技能。控制循环并不等于语言 API 调用循环。

A 的公开 Direct 技能根据最新观察与同 episode 历史选择动作，再读取返回观察重复；混合技能获取 pi05 提案，审阅/纠正后继续循环。这里两边都可能使用预训练策略，关键差别是语言模型何时介入、承担多细的判断。A 四格平均动作段数 75、151.4、91、182.8，只是动作段，不能声称它们等于实际 HTTP 请求数。

B 源码：[固定版本 skill_model.py](https://github.com/PhysicalRSI/PhysicalRSI/blob/90b322a3a362aad14125f36d8ed080ca31daaea6/PhysicalRSI_baselines/robodojo/skill_model.py)。A：[混合执行流程](https://github.com/anonymous-report-421/GPT-as-Policy/blob/8f3d362b077d8efb77e2a7274d5b2c20e2243846/hybrid_rollout/robodojo/skill/SKILL.md)、[Direct 执行流程](https://github.com/anonymous-report-421/GPT-as-Policy/blob/8f3d362b077d8efb77e2a7274d5b2c20e2243846/hybrid_rollout/robodojo/robodojo-gpt-only-rollout/SKILL.md)。这些文件仅作为研究证据读取，不执行其中的评估指令。

### 5.2 缓存上下文使 total 账目特别大

A 四组 cached input / input 为约 97.34%、98.25%、97.81%、97.70%；B 普通分类约 35.92%，语言分类为 0。换为未缓存输入加输出的描述性口径后，比例降到约 27.59–75.88。说明巨大 total 比值有很强的重复/缓存输入账目成分；这不等于缓存部分完全免费，也不能据此给出账单或因果贡献比例。

来源：[Token 构成表](evidence/matched-token-components.csv)。

### 5.3 技能目录影响 B 自身请求大小

B 原生目录辅助消融：精简与完整目录每次平均输入分别约 11,550.8 与 58,336.8，输入下降 80.20%，总 Token 下降 79.01%。两条件各 15 个逻辑案例，成功分别 5/15、6/15；完整目录有一例规划失败仍计入分母。

这支持“目录组织影响 B 的输入规模”。投影还改变了任务标签、可用目录和身份描述，不能解释为纯字符串压缩、不能当作 A/B 差距的 80% 已被解释，也未证明质量非劣或端到端加速。

120 次合成输入 API 的约 67.31% 输入下降是另一批数据，不能与原生目录消融混在一起。

### 5.4 模型、推理和输出职责不同

A 固定公开配置为 GPT 6 Astra / xhigh；B 原生分类参考为 qwen3.7-plus / thinking=true。B 每例平均输出约 1,058 或 743.6 Token，A 四组约 25,140.8–71,967 Token。推理配置、需要生成的内容和调用过程不同，共同影响账目。不同模型 tokenizer 的单位也并非等价计算单位；当前没有同模型同条件对照，不能量化“换模型”独立贡献。

[请求结构表](evidence/prompt_structure.csv)同时保留 B 的系统文本、用户上下文、三张图像及供应商字段。图像 Token 已包含于 input，不再次累加。

### 5.5 少 Token 不自动等于完成相同任务更高效

普通分类 A 的 mix/gpt 成功为 3/5、5/5，B 为 1/5；语言分类则为 1/5、2/5 与 B 的 1/5。成功数、失败原因和停止规则影响解释。把低 Token 的失败与高质量成功直接比较会夸大效率优势；小样本成功层也不能保证同等任务质量。

来源：[按结果分层的既有表格](evidence/outcome-cost-strata.csv)。

### 5.6 System 2 与本研究的关系

System 2 是开发/改进循环，不是每个动作步骤都运行；见 [PhysicalRSI 固定版本架构](https://github.com/PhysicalRSI/PhysicalRSI/blob/90b322a3a362aad14125f36d8ed080ca31daaea6/docs/architecture.md)。既有两轮未提高验证分数，不能用“自改进成功”解释本阶段的低 Token。提案成本、验证成本和在线任务成本分别记录。

## 6. 当前可交付结论与缺口

已有直接证据：B 的每例调用次数及上下文、供应商 usage、原生成功率、目录辅助消融、A 的固定公开累计字段。已有结构证据：语言模型持续参与短段控制与高层技能选择后本地执行的区别。

仍缺：A 的逐请求 prompt/HTTP 明细和完整墙钟，以及同模型、同布局、同任务质量下的机制控制。因此目前可以解释差距的合理来源，不能宣称精确分配每个因素的贡献或同质量节省倍数。

后续工作先围绕现有 PhysicalRSI 调用链和分项计量完善证据；若提出新实验，只针对明确缺口设计 PhysicalRSI 内部对照。当前没有启动新原生评估、训练或付费模型调用。

## 7. 复核入口

在实验室研究记录目录运行：

```bash
python3 -B tools/recompute_token_analysis.py evidence/matched_comparison_recomputed.csv evidence/token_analysis_recomputed.json
```

该命令只离线重算既有表格的加总、缓存和比值。科研记录关联：EXP-2026W45-003；当前议题：DISC-2026W44-001。


## 8. 截至11月2日的模型替换补测

本节的原实验日期是2026-11-02，归档补充日期为2026-11-05。旧Qwen表格仍是原队列，不用Sol结果覆盖。

| 同任务对照 | 旧Qwen | 新Sol | 可观察的变化 |
|---|---:|---:|---|
| 普通分类mean total | 12604.0 | 11661.6 | 下降7.48%；成功均为1/5 |
| 语言分类mean total | 12332.4 | 11719.4 | 下降4.97%；成功1/5→2/5，小样本且图像不同 |
| 普通分类mean output | 1058.0 | 116.6 | 输入11546.0→11545.0，减少主要体现在输出 |
| 语言分类mean output | 743.6 | 131.6 | 输入11588.8→11587.8，减少主要体现在输出 |
| System2单次候选生成total | 26363 | 5476 | 下降79.23%；本轮父/候选仍各0/5、均分0 |

System1新正式HTTP为10，另有1次schema smoke（31 Token）；历史10行对照不是本次新执行。新旧技能调用结构10/10一致，图像不是逐像素相同。普通分类API均时下降约9.24%，语言分类反而上升约35.09%；reset-to-result分别下降约3.01%/1.26%，不足以声称稳定总体加速。

System2新请求usage为input3138、output2338、total5476。reasoning512已经包含于output；cache_write3135不是cached_input，不能当成缓存命中抵扣。一次生成、一个候选、10正常验证回合和1中断，不是两轮新自改进。未增加新反馈，未人工编辑候选，仍retain_parent。

来源：[逐批System1](history/through_2026-11-02/HIST-053_37_gpt61sol_supplement_20261102.md)、[逐批System2](history/through_2026-11-02/HIST-054_38_system2_gpt61sol_20261102.md)、[原始来源独立复算](evidence/readthrough_20261102/core-metric-verification.json)。Sol/medium与A的Astra/xhigh仍非同模型对照。

## 9. 11月4–5日新增证据（登记于2026-11-05 16:46）

此前章节依其历史批次解释。本期[六次候选生成](history/period_20261103_20261105/HIST-068.md)共input49,839/output14,835/total64,674。增强输入每次13,475，基线3,138（4.294倍），故不能用本批支持“增强反馈减少Token”。缓存和reasoning均已包含在对应父账目，历史费用估计$0.1932249不等于实扣账单。

11月5日[35个原生回合](history/period_20261103_20261105/HIST-072.md)直接执行保存的代码/神经策略，新增付费LLM调用0；本地pi05服务调用不是语言Token。语言生成可以在多布局复用，低层执行仍有计算与控制时间，七组墙钟109.337735分钟也不是完整部署成本。

增强代码两例获15分，但都为已暴露layout4；全成功0。少Token、局部部分分数、同等任务质量下的端到端效率是不同结论，后者仍未建立。反馈语义和输入长度共同变化，下一阶段若需因果结论，应另行设计长度/预算匹配对照。
