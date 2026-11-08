# HIST-068 · 基线与增强反馈六次候选生成

- 原始事件：2026-11-04 20:46:09–20:51:36，北京时间；未留存精确时间的事件只标日期，不从mtime推算。
- 登记：2026-11-05 16:46（北京时间）；本期科学证据截点：2026-11-05 16:15:35（北京时间）。
- 性质：新LLM候选生成（历史执行）。周志：[EXP-2026W45-009](../../LOGS/2026-W45.md#exp-2026w45-009)

## 目的

比较原反馈与包含拒绝候选代码、失败归因、纠序观察的增强反馈所产生的代码。

## 实际完成的工作

固定gpt-6.1-sol/medium、max_completion_tokens=12000、JSON、standard、无工具及自动重试。按base1→aug1→aug2→base2→base3→aug3交错调用。增强输入包含诊断信息，没有追加手工修复答案。父策略仍为pi05。

## 指标及结果

6次调用均为合法JSON/Python。input49839、output14835、total64674；baseline三次input9414/output7058/total16472；augmented三次40425/7777/48202。每次输入3138→13475（4.294倍）。按当时记录费率复算估计$0.1932249；$10为预算，$2.447298为预留，不是实扣。

## 解释与限制

本批是增加诊断上下文的候选生成研究，不是进一步减少Token的实验。候选字节与供应商响应及次日冻结协议一致。

内容与长度共同改变，不能隔离语义反馈的因果作用；reasoning已经包含在output，缓存是input子集不能重复加。billing-reviewed取代初始低估cache-write的ledger；费用为历史usage估算，未核对实际账单。

## 复核与下一步

本次没有重跑上述历史任务。冻结协议、源代码与原始执行回执是复现依据；历史脚本不能原地再次执行覆盖产物。

使用保存候选先做CPU及原生验证，避免为验证重生成；未来若做因果研究需匹配Token预算。

## 原件与来源

- [protocol.json](../../../../experiments/system2_followup_through_20261105/stages/29_feedback_generation/protocol.json) — SHA256 `7e00e1f452a1db09945884c64f1c14521ff8dc0221a619a0c88ade9a7cfb62dc`
- [status.json](../../../../experiments/system2_followup_through_20261105/stages/29_feedback_generation/status.json) — SHA256 `5003e91d34f43cc91aea3c49ac91982207e59891d76e1e1e0f898923009f11b6`
- [billing-reviewed.json](../../../../experiments/system2_followup_through_20261105/stages/29_feedback_generation/billing-reviewed.json) — SHA256 `f892f15b4d6e664e69b27593046c814d288b9eb418b29f9b2c28361894084bec`
- [ledger.json](../../../../experiments/system2_followup_through_20261105/stages/29_feedback_generation/ledger.json) — SHA256 `363964910e7dfc57cd7efc59ee87a4d7a41ecbc1c0cc2cd57fa27ee7d4fcd91d`
- [api-usage.csv](../../../../experiments/system2_followup_through_20261105/stages/30_lab_summary/api-usage.csv) — SHA256 `a882f6683c0dde837e01e9737bf6626d2ea58fd2f53a1ffcec6fc0683b70f139`
- [diagnostic-matrix-v1.json](../../../../experiments/system2_followup_through_20261105/stages/31_rgb_validation/protocol/diagnostic-matrix-v1.json) — SHA256 `60816ebccd9fc07bae5e252efb67d8806a941adadbe84d788bbb7695d81d665d`
