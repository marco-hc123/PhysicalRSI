# HIST-067 · H100规划和两种预训练策略离线验收

- 原始事件：2026-11-04 20:54–21:14:42，北京时间；未留存精确时间的事件只标日期，不从mtime推算。
- 登记：2026-11-05 16:46（北京时间）；本期科学证据截点：2026-11-05 16:15:35（北京时间）。
- 性质：离线GPU验收。周志：[EXP-2026W45-008](../../LOGS/2026-W45.md#exp-2026w45-008)

## 目的

验证路径可行性与固定权重输出有限值，不把推理验收当作任务成功。

## 实际完成的工作

v5仅修新诊断脚本的资源绑定与数值堆叠检查。用户暂停时停止自有调度器，已经运行的pi05自然完成；恢复后v6_sparse只补剩余sparse，不重跑API。完成时间与暂停/恢复分别保留。

## 指标及结果

24次规划=8条件×3 solver seeds：layout1抬高20cm为0/3，15/10/5cm分别3/3；layout3、4左臂各0/3，右臂各3/3。pi05和sparse各3次合成输入推理，输出均有限、拼接形状50×14。pi05秒数7.370293/0.056747/0.053586；sparse9.694970/0.101436/0.086016。sparse有效历史帧0/1/1，reset清空。

## 解释与限制

已有权重推理与部分目标的规划可运行；不能由此宣称抓取、分类或记忆改善。

首轮包含初始化/编译，后两次不能直接当完整回合耗时；seed重复是求解器重复。左右臂比较同时改变四元数，非纯手臂单变量；可行路径不等于抓取。未训练、无RGB原生回合、无API。

## 复核与下一步

本次没有重跑上述历史任务。冻结协议、源代码与原始执行回执是复现依据；历史脚本不能原地再次执行覆盖产物。

后续用真实RGB及冻结候选确认任务效果，分开记录各级开销。

## 原件与来源

- [protocol.json](../../../../experiments/system2_followup_through_20261105/stages/28_h100_acceptance/20261104_v5/protocol.json) — SHA256 `5f743a40bc73332bc563bb1e6bbead3cf5e24a0f26ad4e706377ef37daf7a915`
- [PAUSE-REPORT.txt](../../../../experiments/system2_followup_through_20261105/stages/28_h100_acceptance/20261104_v5/PAUSE-REPORT.txt) — SHA256 `421fc5d6b77e3734024a89c80bbb8ebaa792f119d38da901cb344fbb70cc0b0c`
- [inference.json](../../../../experiments/system2_followup_through_20261105/stages/28_h100_acceptance/20261104_v5/pi05/inference.json) — SHA256 `a15439e82b8423b44a42757103e05af804418e791c7025a596215726a1ec2221`
- [inference.json](../../../../experiments/system2_followup_through_20261105/stages/28_h100_acceptance/20261104_v6_sparse/sparse/inference.json) — SHA256 `23dcd0119f462a254f95b2406aede33cfe513201dd9af49d1bacd995ccf6e9dc`
- [status.json](../../../../experiments/system2_followup_through_20261105/stages/28_h100_acceptance/20261104_v6_sparse/status.json) — SHA256 `8c2501b5e1384265371271f2f9cb31d958ae4e5942fc8f89380d52d8dbf72137`
- [planning-feasibility.csv](../../../../experiments/system2_followup_through_20261105/stages/30_lab_summary/planning-feasibility.csv) — SHA256 `d270310e2f9f42cdda4e7ea565518b589b24e6d6b2a2d5c57afce6347e56f0fc`
- [policy-acceptance.csv](../../../../experiments/system2_followup_through_20261105/stages/30_lab_summary/policy-acceptance.csv) — SHA256 `c142ab1e2f767790fd48fe2a9e40b681fb4c5ee64733018deaf7d191f066f8b1`
