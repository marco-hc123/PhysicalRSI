# PhysicalRSI 科研记录工作区

本目录已按用户选择启用 **expert（老手）模式**。研究范围：有限范围复现 PhysicalRSI，解释 Token 与耗时差异，并如实记录 System 2 的负结果。已有结果统一从实验室服务器研究目录查阅。

## 从这里继续

1. [CONTINUATION.md](CONTINUATION.md)：当前状态、已完成工作、下一步。
2. [idea.md](idea.md)：研究目标、历史实验范围、指标与通俗说明。
3. [HISTORY.md](HISTORY.md)：实验室全部结果目录入口与重点结论。
4. [Discussion.md](Discussion.md)：当前议题与待解决问题。
5. [method.md](method.md)：现有方法与指标定义。
6. [本周记录](LOGS/2026-W44.md)：四组代表性历史实验导入；登记日期不代表实验日期。

## 会话开始

在实验室服务器执行：

```bash
cd /mnt/data/joey_tr/physical-RSI/research
python3 -B tools/session_check.py
```

先读简报和当前议题，再推进工作。工具负责记录与检查；这条命令不启动训练、仿真或 API 调用。

## 目录关联

| 内容 | 实验室位置 |
|---|---|
| 研究根目录 | `/mnt/data/joey_tr/physical-RSI` |
| 原始实验结果 | [../result/](../result/) |
| 项目代码与历史快照 | [../repos/](../repos/) |
| 实验脚本 | [../experiments/](../experiments/) |
| 环境、配置、资源和权重 | `../envs/`、`../configs/`、`../data/`、`../models/` |
| 研究记录与下一步 | 本目录 |

新实验产物继续放在研究根目录 `result/` 的独立批次目录，并在此登记。已有运行记录、失败结果和源码快照保留原样。目录数、API 次数和机器人评估次数分别统计。

[协作协议](AGENTS.md)与[工具说明](tools/README.md)保留模板原有规则。代码运行环境与本记录工具分别管理；初始化只使用系统 Python 标准库。Git 提交钩子未安装，本目录尚未建立独立 Git 仓库；当前以状态记录、原始模板备份和文件哈希追溯初始化变更。
