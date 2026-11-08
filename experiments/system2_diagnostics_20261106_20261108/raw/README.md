# 无损原始文本证据

原件按 SHA256 去重，以 gzip 压缩的 UTF-8 JSONL 分片保存。每条成员含原字节大小、SHA256、分片编号与原文；读取器验证完整拼接后的原字节。索引覆盖本次收集的结果24–43及科研管理快照，目录/文件数量不是实验次数。

已公开的11月5日前原件沿用旧压缩分片；新增分片只保存没有已有精确文件或旧无损对象的文本。实际 runtime 和命中凭据模式的整种内容不公开，所有相同字节别名一并标为外部保留。视频、权重等二进制原档仍在实验室，索引没有声称本次重新读取所有二进制字节。

在仓库根目录运行 `python3 -B tools/read_week_evidence.py --search 43_system2_multitask` 检索，运行 `python3 -B tools/read_week_evidence.py --verify-objects` 核对新旧无损对象。给读取器完整的 `source_path` 可输出原始文本，读取不会执行归档代码。
