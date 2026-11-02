# 固定输入 API 实验：80 次探索与 120 次扩展

这是合成输入的真实付费 API 记录，不运行物理机器人；模型为历史 `qwen3-vl-plus`。它用于隔离目录投影对单次请求语言开销的影响，不能提供机器人成功率。

## API80

`api80/all_calls.csv` 共 80 行，含三种 suite：example_2_compositions 40 次、registry_22_operations 10 次、registry_22_operations_schema 30 次。最初 registry 条件的输出存在契约失败，修订后组单独列出，不删除失败记录。每组有 5 个独立合成输入，重复不增加独立场景数。

`summary.json` 汇总采用 `100*(1-projected均值/unprojected均值)`；某些早期逐对统计采用其他聚合方式，不直接混用。`failure_analysis.json` 保留格式及注册技能检查。原脚本用于追溯，不应不改输出路径就重新执行。

## API120

20 场景 × projected/unprojected × 3 次，共 120 请求，60 对。原生机器人回合为 0。input 平均 27,437.3 → 8,969.3（−67.31%）；total 平均 27,598.92 → 9,144.37（−66.87%）；HTTP 平均 14.4324 → 9.8643 s（−31.65%）。120/120 通过本实验定义的 JSON、输出契约和作者标签一致性检查。

源输入、未发送的标签与执行 schedule 位于 `api120/inputs/`。`calls.csv` 的 provider_id 用于识别实际响应；三次重复共享两条件的 40 份请求输入，不是 120 个不同请求模板。缓存是输入子集；表中时间来自 HTTP 调用，不是机器人墙钟。没有核对最终发票。

## 为什么有 JSONL 容器

为便于 Git 审阅和避免数百个相似小文件，`requests*.jsonl`、`responses*.jsonl`、`raw_responses*.jsonl` 按大小分片。每行包含原相对 `path`、原 `sha256`、原 `bytes` 和 `utf8` 字符串。

`record['utf8'].encode('utf-8')` 可恢复该成员原字节；并非重新生成的响应或只保留摘要。原始 JSON 的缩进与换行包含在该字符串内。API80 responses 是原始计量封装，API120 同时提供服务商 raw response 与对应封装，二者不能算两次调用。API80 没有凭空补造缺失的服务商独立 raw 文件。

运行 `python tools/verify_research_evidence.py` 会检查成员哈希、200 行 calls 账目、120 原始响应 usage 及目录消融的分母，不发起网络请求。真实实验脚本会产生费用，离线阅读不需要执行它们。
