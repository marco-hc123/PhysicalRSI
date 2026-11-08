# 新对话入口：PhysicalRSI 最新实验结论

更新日期：2026-11-02（北京时间）。GPT System1 补测和 GPT System2 单轮补测均已完成，PPT 未修改。以下状态替代此前“GPT System2 尚未启动”的说明。

## 优先读取

最新 System2 目录：`/mnt/data/physical-RSI/result/38_system2_gpt61sol_20261102/`
- `RESULTS_ZH.md`：完整中文结果与限制。
- `analysis-summary.json`、`episode-results.csv`：成绩、选择决定、每次启动明细。
- `proposal-api/call-0001/`：原始 GPT 请求、响应、usage 和输入比对。
- `model-candidate.py`：实际生成和验证的候选，未经人工修正。
- `verification.json`、`local-verification.json`：原生凭据、官方选择器及本地费用核对。
- `recovery-01/`：欠费停机后的显式恢复登记、预算快照和恢复源码。
- `budget-ledger.json`：包含此前System1费用上界的累计账本。

System1 目录：`/mnt/data/physical-RSI/result/37_gpt61sol_supplement_20261102/`
该目录 `RESULTS_ZH.md` 和 `analysis-summary.json` 仍只描述 System1，不能混作本轮 System2。

## 最新 System2 结论

本轮只将候选生成器由千问换成GPT-6.1 Sol/medium：原始提示词和用户输入逐字相同，保留旧开发反馈、primitive接口、父pi05、控制上限1100步和0.04秒间隔。不增强反馈、不精简目录、不训练VLA、不手工修复候选。

普通分类一个候选、5个匹配验证布局：
- 新执行父pi05：成功0/5，平均Score0。
- 新GPT候选：成功0/5，平均Score0。
- 官方选择器决定retain_parent，保留父pi05。
- 对应历史千问轮的父/候选也均0/5、Score0。本轮未观察到任务性能提升，不能推广为所有GPT模型/候选都无效。
- 同一份候选生成输入：旧千问26363 Token，本次GPT5476 Token，下降约79.2%。这是一份方案的生成用量，不是每个仿真回合的用量；减少Token不等于任务效果改善。
- GPT候选按篮子dims计算xy范围，与旧候选固定大范围不同。这是代码结构差异，不是物理判定正确或任务成功的独立证据。

本轮实际只有一次模型请求，无重试、无截断，input3138/output2338，其中reasoning512已包含在output。cache_write3135是缓存写入，不是命中缓存。
本次新增费用按标准价估算约0.0312美元；含此前System1补测的累计模型费用保守上界0.332955美元，停止门槛20美元；ECS费用另计。

## 停机恢复及分母

用户确认ECS欠费停机，充值后要求继续。4个完成的父策略回合复用；第5次启动的中断记录保留、评分未知，不当作0分或策略失败。恢复后仅补该布局和5个候选回合，没有重新调用模型。
总计11次仿真启动尝试、10个正常结束的计划验证回合、1次基础设施中断。每组成功率仍按5个自然结束的预定布局统计。开发10个回合的原有证据复用，不计为新执行。

## 已完成的 System1 补测

两任务各布局5–9，原技能目录不变：普通分类GPT平均11661.6 Token、成功1/5、Score47；语言分类11719.4 Token、成功2/5、Score46。千问对应1/5、Score32与1/5、Score30。两模型在对应回合选的技能完全相同，不能把执行成绩差异直接归因于GPT路由更好。
A仍为GPT-as-Policy固定公开数据、GPT-6 Astra/xhigh；B为本轮Sol/medium。并未进行同模型、同布局、等质量跨项目对照。

## 历史 System2 与未执行范围

旧千问两轮均保留父pi05。旧固定pi05的独立验收是两任务各0/10，不是本轮GPT候选的独立验收成绩。
历史正式记录：`/mnt/data/physical-RSI/result/31_system2_final_validation_20261030T121000Z/`
旧候选诊断：`/mnt/data/physical-RSI/result/36_system2_mechanism_20261031T010000Z_v3/`
本轮只完成一轮GPT候选补测，没有完成两轮全新GPT实验、没有20个新布局的独立最终验收，也没有反馈闭环修复。

仿真进程已结束。读取结论无需调用API。OpenAI密钥未保存到服务器；临时客户端和SSH转发已关闭。完整原生视频和执行证据保留云端。
