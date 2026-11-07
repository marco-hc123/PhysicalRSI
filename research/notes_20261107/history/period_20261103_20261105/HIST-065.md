# HIST-065 · 旧候选CPU契约与单变量诊断

- 原始事件：2026-11-04（初批19:50，后续纠序另见completion），北京时间；未留存精确时间的事件只标日期，不从mtime推算。
- 登记：2026-11-05 16:46（北京时间）；本期科学证据截点：2026-11-05 16:15:35（北京时间）。
- 性质：CPU诊断，非机器人实验。周志：[EXP-2026W45-006](../../LOGS/2026-W45.md#exp-2026w45-006)

## 目的

检查旧候选的篮筐判定、类别映射、错误传播与memory发布契约。

## 实际完成的工作

复用10个历史候选回合、78条RPC指纹。先做27组候选×fixture、14个单变量修复副本、4个exact-driver虚拟I/O检查。原10个历史前缀按文件名排序有误；保留错误批次，followup_v2重新按调用序号生成10个前缀，解释以纠序版本为准。

## 指标及结果

总计65个异构CPU探针=27+14+4+10+10。第二轮±0.2m的XY判定匹配3/6，手工改为半尺寸副本匹配6/6；watch映射原本KeyError，另一个人工映射副本能到首次approach。冻结mock下100次RPC=18 scene+49 approach+33 gripper。

## 解释与限制

发现几何、类别与接口契约问题，但这些都是诊断或人工修复副本，不能称模型自主修复成功。原driver确实传播no_path错误。

memory修改未从原返回schema发布，副本counter可1→2，但不能据此证明历史原生零分的原因；这也不是sparse VLA历史缓存。静态场景mock循环不等于机器人循环。普通用户chroot/user namespace受限，未修改权限。

## 复核与下一步

本次没有重跑上述历史任务。冻结协议、源代码与原始执行回执是复现依据；历史脚本不能原地再次执行覆盖产物。

针对真实执行可观察量设计候选反馈；原始/修复副本与错误排序结果全部保留。

## 原件与来源

- [REPORT.txt](../../../../experiments/system2_followup_through_20261105/stages/27_offline_diagnostics/REPORT.txt) — SHA256 `fd872d5ebfcb22a6fc29fe0a25e10fe4a0acfaedc731de7b9025877dec34b4e3`
- [protocol.json](../../../../experiments/system2_followup_through_20261105/stages/27_offline_diagnostics/protocol.json) — SHA256 `8d0d9b094e86143dc7a0d235e33f5a923c80c1bd3ce0f17b5a647a4da34c76ce`
- [REPRODUCE.txt](../../../../experiments/system2_followup_through_20261105/stages/27_offline_diagnostics/REPRODUCE.txt) — SHA256 `04b4f0e25bade27707d4d02ea982a768cf457bb4b5f3f9a718040130837ea60a`
- [driver-memory-and-error-contract.json](../../../../experiments/system2_followup_through_20261105/stages/27_offline_diagnostics/driver-memory-and-error-contract.json) — SHA256 `ad42dbb8f9c1bb7cd322394001f80aa4414d6ac7607632cb0bfcf149b69f0b1a`
- [recorded-observation-prefix.json](../../../../experiments/system2_followup_through_20261105/stages/27_offline_diagnostics/followup_v2/recorded-observation-prefix.json) — SHA256 `b9e360ce3c2b61dcdfe88b5fad4f3027ded1adf2c4dabc30980433c80215dc67`
- [completion.json](../../../../experiments/system2_followup_through_20261105/stages/27_offline_diagnostics/followup_v2/completion.json) — SHA256 `18cba5970df613c6ee2b80da47e404e85809282706319e1b23b9f4f583db5297`
