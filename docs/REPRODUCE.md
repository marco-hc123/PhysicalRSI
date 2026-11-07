# 实验条件与复现说明

## 离线核验现有结果

```bash
python tools/verify_results.py
python tools/verify_research_evidence.py
python3 -B tools/verify_followup_evidence.py
```

仅使用 Python 标准库，核验来源清单中的文件 SHA256，并从分类逐回合 CSV 重新计算汇总；核验 System 2 父/候选的布局配对、成绩与选择记录。不会请求模型或启动机器人。

## 查看原项目的 CPU 演示

需要 Python 3.11+。在独立环境中安装上游快照：

```bash
python -m venv .venv
# 激活刚创建的环境后执行：
python -m pip install -e ./upstream/PhysicalRSI
physicalrsi --plain --workspace /tmp/physicalrsi-demo --command '/demo'
```

CPU 演示仅证明项目入口和软件流程可运行，不证明原生仿真成功。上游视频素材未随仓库复制，需要时可从固定提交获取。

## 原生 GPU 仿真的依赖

完整复跑还需要 RoboDojo、Isaac Sim、任务资产、pi05 权重、本地 VLA 服务及相同布局。它们不随本仓库分发。固定来源见 `UPSTREAM.json`，包版本见 `environment/`；具体路径和接口以各实验的 `protocol.json` 为准。

`upstream/PhysicalRSI` 是干净上游快照；`integration/framework-validation-v3` 是本次使用的冻结集成层，二者不要混为同一个版本。子模块需按原 `.gitmodules` 的固定来源单独获取，不应把子模块缺失描述成权重已包含。

## GPT 分类补测

- 源码入口：`experiments/system1_gpt/controller.py` 与 `analysis-sources/cloud_comparison_run.py`。
- 任务：`classify_objects`、`classify_objects_by_language`；每任务布局 5–9，seed=0。
- 每回合控制上限 1100 步，控制间隔 0.04 s；技能目录保持原样。
- 模型：`gpt-6.1-sol`，reasoning medium，max_completion_tokens=16000。
- 原服务器直连模型接口超时，实际请求经本机客户端与加密 SSH 转发完成。计时包含这段路径，不能用于宣称供应商纯 API 提速。

## GPT System 2 补测

- 源码入口：`experiments/system2_gpt/procedure-sources/system2_sol_run.py`。
- 普通分类：复用历史 10 个开发回合的证据和原始模型输入，生成 1 个候选；父/候选各验证 5 个历史匹配布局。
- 模型：`gpt-6.1-sol / medium`，与旧对应请求一样未显式设输出上限。
- 正常结束 10 个回合；额外 1 次启动因欠费停机中断，保留未知评分，不作为策略失败。
- `model-candidate.py` 直接对应模型响应；候选未手工修复。

## 重新跑实验前如何使用归档程序

历史程序保留原服务器路径、协议 SHA 和防止重复启动的断言，目的是可追溯，不能直接在已经完成的目录再次运行。复跑时应创建新的输出目录，按本机资产路径生成新的私密运行配置，并重新冻结协议与来源哈希；保留新旧实验分母和费用账本。

私密运行配置与 API 客户端凭据不上传。`configs/provider.env.example` 只列出配置思路，并不声称所有历史脚本都自动读取这些变量。本次仓库整理没有启动复跑，也没有发生新模型推理费用。

## 新增历史研究材料的核验

第二个离线命令复核新增来源哈希、API80/120 逐次数据及 JSONL 原件、目录消融分母与选定视频。它不重新执行旧 live runner。两个验证脚本检验的材料范围不同，不能把它们的计数相加当作实验次数。完整流程及证据边界见 [研究总览](RESEARCH_OVERVIEW_ZH.md)。


## 11月4–5日后续证据

[批次入口](../experiments/system2_followup_through_20261105/README.md)提供生成参数、冻结候选、协议、原生评分和逐例结果。上方第三条命令只读核验；完整原生复跑还需要原依赖、权重、场景与新输出目录，不能原地重跑历史runner覆盖结果。

未重跑正式策略选择器、未训练或晋升候选，未进行新独立布局验收。旧manifest按精确历史版本核对，当前来源清单同步更新。
