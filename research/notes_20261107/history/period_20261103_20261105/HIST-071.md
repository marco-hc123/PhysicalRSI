# HIST-071 · 冻结RGB环境恢复与失败部署尝试

- 原始事件：2026-11-05（协议11:48:44冻结，运行配置12:58:39），北京时间；未留存精确时间的事件只标日期，不从mtime推算。
- 登记：2026-11-05 16:46（北京时间）；本期科学证据截点：2026-11-05 16:15:35（北京时间）。
- 性质：原生环境准备与有效性核验。周志：[EXP-2026W45-011](../../LOGS/2026-W45.md#exp-2026w45-011)

## 目的

在具备图形能力的执行环境恢复冻结依赖和资源，保证保存候选验证可比较。

## 实际完成的工作

核验Python3.11.17、Isaac Sim5.1.0、PyTorch2.7+cu128；267个模拟器包、232个策略包、741个runtime/source指纹、41个checkpoint文件、15369场景文件、10691技能文件。使用保存候选，明确冻结expert选择。记录控制器preflight失败和pi05 attempt001的ffmpeg缺失；修正可执行入口后attempt002有效。

## 指标及结果

部署失败attempt001在策略推理前结束，没有有效任务评分，不当成0分回合。有效pi05五例纳入HIST-072，不能在此再计5例。

## 解释与限制

冻结关键资源及有效性检查通过后才纳入35例矩阵，部署失败另留原件。

历史同为L20/同driver，但CPU/RAM为8核64GiB，原参考16核128GiB，墙钟非同硬件比较。历史ffmpeg精确版本未知，现有imageio-ffmpeg0.6携带ffmpeg7.0.2通过实际验收。rerun要求NumPy>=2与冻结1.26.4元数据冲突保留，不能宣称所有可选功能兼容。

## 复核与下一步

本次没有重跑上述历史任务。冻结协议、源代码与原始执行回执是复现依据；历史脚本不能原地再次执行覆盖产物。

以有效回执、冻结候选/布局哈希和原生评分评估，继续保留所有失败尝试。

## 原件与来源

- [diagnostic-matrix-v1.json](../../../../experiments/system2_followup_through_20261105/stages/31_rgb_validation/protocol/diagnostic-matrix-v1.json) — SHA256 `60816ebccd9fc07bae5e252efb67d8806a941adadbe84d788bbb7695d81d665d`
- [completion.json](../../../../experiments/system2_followup_through_20261105/stages/31_rgb_validation/resource-verification/completion.json) — SHA256 `0a13ae28984bfeb561a7c9e5b2a7da39fb3dd6101b9d617b283660d9963fa7aa`
- [pre-native-attempts.jsonl](../../../../experiments/system2_followup_through_20261105/stages/31_rgb_validation/native-campaign/pre-native-attempts.jsonl) — SHA256 `94220313c5590e45ad8902e820cc7e59060c6ebe8748481ba75391b6d0c2fb5d`
- [deployment-retry-authorization.json](../../../../experiments/system2_followup_through_20261105/stages/31_rgb_validation/native-campaign/deployment-retry-authorization.json) — SHA256 `af3fce063d8d4058c8f30dc5cb106656ec5b98633021c21060e9816ad88fdefe`
- [runtime-preflight.json](../../../../experiments/system2_followup_through_20261105/stages/31_rgb_validation/native-campaign/runtime-preflight.json) — SHA256 `e01d9cf8af81c11d2201204962750dfc107fac4ae92d9b49db042657a3533883`
- [REPORT.txt](../../../../experiments/system2_followup_through_20261105/stages/31_rgb_validation/analysis/REPORT.txt) — SHA256 `76cc1c95f814edd10dd7f7768bd40bd6860e29b13d19f9492ca2516317683fc3`
