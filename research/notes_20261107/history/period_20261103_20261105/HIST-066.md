# HIST-066 · H100验收失败与新诊断脚本修订

- 原始事件：2026-11-04 20:42–20:51，北京时间；未留存精确时间的事件只标日期，不从mtime推算。
- 登记：2026-11-05 16:46（北京时间）；本期科学证据截点：2026-11-05 16:15:35（北京时间）。
- 性质：历史基础设施失败尝试。周志：[EXP-2026W45-007](../../LOGS/2026-W45.md#exp-2026w45-007)

## 目的

排查离线GPU验收执行链是否可用，保留失败原因。

## 实际完成的工作

v1（20:42:15）、v2（20:46:40）、v3（20:48:36）均在新诊断控制器的隔离约束下CUDA初始化失败。v4（20:51:41）改为每个worker隔离后CUDA通过，但规划丢失URDF/mesh相邻路径绑定；策略检查器误把动作字典列表当成数值数组。

## 指标及结果

4个版本的失败/部分失败原件分别保留；这些不是4个原生零分任务。v4日志不能作为已通过的策略输出验收。

## 解释与限制

当时失败主要发生在新诊断脚本与资源绑定层，不是已证实的pi05/sparse模型失效。

本条是既有失败的追溯登记，不是当前会话重试；本次没有重新启动GPU任务、修改隔离权限或改写历史日志。

## 复核与下一步

本次没有重跑上述历史任务。冻结协议、源代码与原始执行回执是复现依据；历史脚本不能原地再次执行覆盖产物。

查阅后续v5/v6成功回执；不执行旧main覆盖完成目录。

## 原件与来源

- [status.json](../../../../experiments/system2_followup_through_20261105/stages/28_h100_acceptance/20261104_v1/status.json) — SHA256 `1da69eb4d42d53cb01166c089866b66ec9a674cb515aada9d103d23b83be99cc`
- [protocol.json](../../../../experiments/system2_followup_through_20261105/stages/28_h100_acceptance/20261104_v1/protocol.json) — SHA256 `86d61ed9811bc6b94a0fdc6e46daab173d156baffb1229b3d7b0a589d03050e6`
- [status.json](../../../../experiments/system2_followup_through_20261105/stages/28_h100_acceptance/20261104_v2/status.json) — SHA256 `3489e38b20ba9d4704651eeb93fd09c70ea65338f358909ee789ab6722133548`
- [protocol.json](../../../../experiments/system2_followup_through_20261105/stages/28_h100_acceptance/20261104_v2/protocol.json) — SHA256 `8597b684b2c65f88a49a402fa70c3216f058e711c31e9f5e613831b5f42634a3`
- [status.json](../../../../experiments/system2_followup_through_20261105/stages/28_h100_acceptance/20261104_v3/status.json) — SHA256 `e587833dea3809c1882277044448372bfe47079dea3b241083c5379689634cd3`
- [protocol.json](../../../../experiments/system2_followup_through_20261105/stages/28_h100_acceptance/20261104_v3/protocol.json) — SHA256 `4449609e7e2a98f406647d49beefec2170edbd93f977d1ca2e024b19fc2d28cc`
- [status.json](../../../../experiments/system2_followup_through_20261105/stages/28_h100_acceptance/20261104_v4/status.json) — SHA256 `2d3575d215177790f9f5870bf729e6f7d4324d6411f94321b5db1a02028f0be2`
- [protocol.json](../../../../experiments/system2_followup_through_20261105/stages/28_h100_acceptance/20261104_v4/protocol.json) — SHA256 `7d6894fa0a61ef5519c2472b650ca1053bf91f0ec6366d3be0f9b12f5e690b0e`
