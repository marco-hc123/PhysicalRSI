# HIST-072 · 七条件35个有效RGB原生回合

- 原始事件：2026-11-05（至15:33:06完成），北京时间；未留存精确时间的事件只标日期，不从mtime推算。
- 登记：2026-11-05 16:46（北京时间）；本期科学证据截点：2026-11-05 16:15:35（北京时间）。
- 性质：原生仿真诊断矩阵。周志：[EXP-2026W45-012](../../LOGS/2026-W45.md#exp-2026w45-012)

## 目的

检验增强反馈保存候选是否改变真实执行与任务评分。

## 实际完成的工作

7条件×5个历史已暴露布局0–4：pi05、baseline1、augmented1、augmented2、baseline2、baseline3、augmented3。每候选源码与Nov4供应商响应逐字/AST核对；冻结布局哈希与35个receipt和raw result一致。3个baseline是基线提示生成的代码，不是神经pi05。

## 指标及结果

有效回合35；完整成功0/35。pi05 0/5、均分0；baseline三个各0/5、均分0；augmented1/2各0/5、均分3/100，augmented3均分0。两例15/100均来自layout4；增强组平均2/100、基线组0，描述差+2。105个三视角视频；7组墙钟合计109.337735分钟。新API0、训练0。

## 解释与限制

出现局部部分得分，不能再用“所有新候选都零分”概括本期；完整任务仍未完成，稳定提升与独立泛化尚无证据。

5个布局此前暴露，框架split名validation不使其成为独立heldout；15个增强回合不是15个全新布局。两例部分分数仅覆盖一个布局。15/40/100是评分阶段阈值，不能加成155；部分达成可能不持续到末帧。1100步自然终止含5个未完成调用仍是有效回合；setup崩溃不能混计。墙钟含组启动/执行/清理/核验，不含资源下载、失败部署、报告和迁移。

## 复核与下一步

本次没有重跑上述历史任务。冻结协议、源代码与原始执行回执是复现依据；历史脚本不能原地再次执行覆盖产物。

利用调用序列定位局部收益和停止原因；新独立验收需预先审查布局暴露并冻结单变量方案。

## 原件与来源

- [diagnostic-matrix-v1.json](../../../../experiments/system2_followup_through_20261105/stages/31_rgb_validation/protocol/diagnostic-matrix-v1.json) — SHA256 `60816ebccd9fc07bae5e252efb67d8806a941adadbe84d788bbb7695d81d665d`
- [campaign.json](../../../../experiments/system2_followup_through_20261105/stages/31_rgb_validation/native-campaign/campaign.json) — SHA256 `86c02a6793d600411721340880ad836bb80b14e4fa9418262583667f9f97bd1b`
- [outcomes.json](../../../../experiments/system2_followup_through_20261105/stages/31_rgb_validation/native-campaign/outcomes.json) — SHA256 `dbe905c1baca44f24f41586c4c55e8a39af46d8840eaaeccbaf7c0721f1a23a9`
- [episode-results.csv](../../../../experiments/system2_followup_through_20261105/stages/31_rgb_validation/analysis/episode-results.csv) — SHA256 `1fadbdf3726a2bd651501768bff81807bf1eb59b5906c94430169cb2c4860abc`
- [cohort-summary.csv](../../../../experiments/system2_followup_through_20261105/stages/31_rgb_validation/analysis/cohort-summary.csv) — SHA256 `ca389968c3e89cb1cd3678382210033cb5d7d47161bf520d1ff8c4ade44d2217`
- [REPORT.txt](../../../../experiments/system2_followup_through_20261105/stages/31_rgb_validation/analysis/REPORT.txt) — SHA256 `76cc1c95f814edd10dd7f7768bd40bd6860e29b13d19f9492ca2516317683fc3`
- [video-index.csv](../../../../experiments/system2_followup_through_20261105/stages/31_rgb_validation/analysis/video-index.csv) — SHA256 `47783b8d356982b5b787968bcf61c7b673396b0ef1a95e35fd52af7f95a18db8`
