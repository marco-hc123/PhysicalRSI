# HIST-069 · 六个新候选的150项CPU比较

- 原始事件：2026-11-04，北京时间；未留存精确时间的事件只标日期，不从mtime推算。
- 登记：2026-11-05 16:46（北京时间）；本期科学证据截点：2026-11-05 16:15:35（北京时间）。
- 性质：CPU诊断，含探索性追加。周志：[EXP-2026W45-010](../../LOGS/2026-W45.md#exp-2026w45-010)

## 目的

在不新增API和仿真的前提下检查候选契约、几何与历史执行前缀。

## 实际完成的工作

主批120=54候选×fixture+36 footprint+30历史纠序前缀；后续30=24针对性几何+6变化场景跟进。后者是看到结果后追加的探索性诊断，单独标注。

## 指标及结果

150探针中未见所检fixture的非法RPC、未捕获异常或100次预算耗尽。6个候选在5个历史前缀均到首次approach；baseline首目标Z1.14，augmented1.01。footprint baseline各6/6、augmented各5/6。4点针对性几何：baseline1/4、1/4、2/4，augmented4/4、4/4、2/4。

## 解释与限制

增强反馈改变了首目标、手臂和包含判定，但部分几何规则存在新缺陷；CPU接口通过不代表任务完成。

aug3使用绝对世界Z<1，平移/篮下条件失配；另两候选8–12mm内缩使近边界判定不同，中心点代理不是物理真值。最初动态前缀使aug2在换场景前结束，纠正后6者均看到了变化却直接return；no_path/transport均在一次approach后返回，不代表恢复。

## 复核与下一步

本次没有重跑上述历史任务。冻结协议、源代码与原始执行回执是复现依据；历史脚本不能原地再次执行覆盖产物。

原生验证关注首失败阶段、实际动作和评分，并保留posthoc标签。

## 原件与来源

- [completion.json](../../../../experiments/system2_followup_through_20261105/stages/29_feedback_generation/offline-eval-v1/completion.json) — SHA256 `5b5d3ff2b9a9493c950ee81d167aeb88fa6ad734a55d862a7916b526af1363bc`
- [fixture-matrix.json](../../../../experiments/system2_followup_through_20261105/stages/29_feedback_generation/offline-eval-v1/fixture-matrix.json) — SHA256 `40b83a6c98d2ed29c8eab93763723e707cf7e56857e56d2dedcb6078197b1435`
- [geometry-matrix.json](../../../../experiments/system2_followup_through_20261105/stages/29_feedback_generation/offline-eval-v1/geometry-matrix.json) — SHA256 `a5a63ddb6d5f5854848c1a11790876b39bc9b680b7da7e0d19cae53d139ccac3`
- [recorded-prefix-matrix.json](../../../../experiments/system2_followup_through_20261105/stages/29_feedback_generation/offline-eval-v1/recorded-prefix-matrix.json) — SHA256 `f63de267388315f0380f7fe8b1248bb2a37b284f89a5f9d708c26203a4c019b2`
- geometry.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/29_system2_feedback_api/20261104_v1/offline-eval-v1/followup-v2/geometry.json`） — SHA256 `608b28d43fcb0227c4f1ebe0b5197b60a2425de29fe62c0303aa117b5db70ab2`
- dynamic.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/29_system2_feedback_api/20261104_v1/offline-eval-v1/followup-v2/dynamic.json`） — SHA256 `6663ed1134c9bedda2a3ee6f6de56f6219b784a623a3814bc07d5f2e938dd2ff`
- [REPORT.txt](../../../../experiments/system2_followup_through_20261105/stages/30_lab_summary/REPORT.txt) — SHA256 `b7c4d177383883f58e433c00e3f76bb9eaa8aab9236ab509e4b5910ccb6b03cb`
