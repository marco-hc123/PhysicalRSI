# HIST-074 · RGB证据回迁实验室与完整性验收

- 原始事件：2026-11-05（归档回执16:02:10，最终状态16:10:08），北京时间；未留存精确时间的事件只标日期，不从mtime推算。
- 登记：2026-11-05 16:46（北京时间）；本期科学证据截点：2026-11-05 16:15:35（北京时间）。
- 性质：证据归档与验收。周志：[EXP-2026W45-014](../../LOGS/2026-W45.md#exp-2026w45-014)

## 目的

把已完成RGB结果统一放到实验室研究目录，确认原件可追溯。

## 实际完成的工作

核验migration manifest、ARCHIVE_VERIFIED与本次字节读账本；29,299个manifest文件的大小及SHA256全部相符。当前批目录29,311个文件，比manifest多12个后续元数据文件，另有顶层README。35个回执共140,480次artifact指纹比对通过，重复引用不当成唯一文件。

## 指标及结果

manifest文件29299、逻辑字节1663174520；SHA256 e6d9dc68f95e778c227a073f5ead0d0a65c9a39d806d24bccc09ef7e54b0a090。原独立视频验收105解码通过、0失败；本次重验视频文件哈希，没有再次逐帧解码或人工看完105个视频。

## 解释与限制

原生结果、日志、视频、冻结协议和诊断证据已在实验室可追溯保存。

不包含整套模型/环境/缓存的再次镜像；归档状态不保证历史执行机或所有共享GPU当前空闲。跨主机manifest时间与回执有几十秒偏差，不据此做精细时延推断。15:40旧暂停只涉及归档复核；已被16:10最终完成状态取代。

## 复核与下一步

本次没有重跑上述历史任务。冻结协议、源代码与原始执行回执是复现依据；历史脚本不能原地再次执行覆盖产物。

使用实验室目录继续研究，先核对当前进程再开展新实验。

## 原件与来源

- source-manifest.json（原始归档位置：`/mnt/data/joey_tr/physical-RSI/result/31_system2_rgb_validation/20261105_v1/migration/source-manifest.json`） — SHA256 `e6d9dc68f95e778c227a073f5ead0d0a65c9a39d806d24bccc09ef7e54b0a090`
- [ARCHIVE_VERIFIED.json](../../../../experiments/system2_followup_through_20261105/stages/31_rgb_validation/migration/ARCHIVE_VERIFIED.json) — SHA256 `e128f5d736cbbc99390e0f49532080ed3ceeebda89670b07bc1f0bd31cf8edda`
- [independent-validation.json](../../../../experiments/system2_followup_through_20261105/stages/31_rgb_validation/analysis/independent-validation.json) — SHA256 `aad45e5812ae8ec8dd3b4252f4417d18c40941e3de39cbeddf64ce5fd5f7775b`
- [final-lab-archive-receipt.json](../../evidence/period_20261103_20261105/local_receipts/rgb_archive_receipts/final-lab-archive-receipt.json) — SHA256 `e128f5d736cbbc99390e0f49532080ed3ceeebda89670b07bc1f0bd31cf8edda`
- [status.json](../../evidence/period_20261103_20261105/local_receipts/rgb_archive_receipts/status.json) — SHA256 `63f8bf49a0bffc147d65bb02fdfebd2c1104f5162285bafbc610e2c0edb68e52`
- [PAUSED_ARCHIVE_REVIEW.json](../../evidence/period_20261103_20261105/local_receipts/rgb_archive_receipts/PAUSED_ARCHIVE_REVIEW.json) — SHA256 `711658fdd617bdd63834e4bec362589ddec81869af5921cfeb7aecee66ce0938`
