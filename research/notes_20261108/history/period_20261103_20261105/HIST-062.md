# HIST-062 · 历史System 2失败归因核对

- 原始事件：2026-11-04 11:44:27，北京时间；未留存精确时间的事件只标日期，不从mtime推算。
- 登记：2026-11-05 16:46（北京时间）；本期科学证据截点：2026-11-05 16:15:35（北京时间）。
- 性质：只读源码及历史执行审计。周志：[EXP-2026W45-004](../../LOGS/2026-W45.md#exp-2026w45-004)

## 目的

区分模型生成缺陷、人工改动、官方固定技能和执行器行为。

## 实际完成的工作

核对50份文件、10个历史候选回合及两轮候选原始来源。过宽篮筐谓词来自Qwen第二轮生成代码，不是后来人工插入，也不是已证实的官方固定技能缺陷；第一轮没有同一谓词。原current_code和memory为空符合神经父策略分支。

## 指标及结果

历史回合复用10；新原生回合0、API0。round1 SHA256 a425b904c62f1637c040765e23e49a180e4b4803c04109ce10f7b5a16346e4e8；round2 SHA256 3a0fc9f9dc6d8b49ff6a5b234feca660f4d8cc5e4259c36d4a273f9802068195。

## 解释与限制

候选特有缺陷需要归到对应生成轮次；不能用第二轮谓词解释全部历史失败。

属于历史事实核查，没有验证任何修复的原生效果；no_path在原driver里已抛RuntimeError，不应误报为新增修复。

## 复核与下一步

本次没有重跑上述历史任务。冻结协议、源代码与原始执行回执是复现依据；历史脚本不能原地再次执行覆盖产物。

把归因证据输入后续诊断，并保留未经改写的候选副本。

## 原件与来源

- [verified-evidence.json](../../evidence/period_20261103_20261105/local_receipts/attribution_review/verified-evidence.json) — SHA256 `759ea087b817a403512daaff8b1593a7386f984800d013b83e4a7b77381800c5`
- [核查说明.txt](../../evidence/period_20261103_20261105/local_receipts/attribution_review/核查说明.txt) — SHA256 `34f036ced9c492e3762727f234fa4171bd35e7bb7e747c13aeb34bbc3f090a4b`
- [round1_candidate_verified.py](../../evidence/period_20261103_20261105/local_receipts/attribution_review/round1_candidate_verified.py) — SHA256 `a425b904c62f1637c040765e23e49a180e4b4803c04109ce10f7b5a16346e4e8`
- [round2_candidate_verified.py](../../evidence/period_20261103_20261105/local_receipts/attribution_review/round2_candidate_verified.py) — SHA256 `3a0fc9f9dc6d8b49ff6a5b234feca660f4d8cc5e4259c36d4a273f9802068195`
