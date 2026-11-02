# 全研究阶段的补充原件库

这里补齐本机预验证、固定输入 API、部署与适配、原生任务、协议与失败审计、System 2、恢复、有限扩展和机制诊断等阶段中，尚未以单文件形式进入仓库的独特文本原件。与已上传文件相同的内容不重复保存。

`provenance/research-source-index-20261102.csv` 为所有已收集来源建立逐路径分类：

- `existing_exact_file` / `new_exact_file`：原字节可在对应仓库文件读取。
- `lossless_jsonl_member`：原字节在固定输入 API 的 JSONL 成员中。
- `lossless_corpus_object`：原字节在本目录的 `records-*.jsonl.gz`；使用标准 gzip 无损压缩，同内容的不同路径共用一个 SHA256 对象。
- `external_only`：完整档案中保留的缓存、批量长文本库/索引或未选二进制观测，不声称已上传。原因逐项记录。

一个对象可能按 `part/parts` 分片；按序连接 `utf8`，再编码为 UTF-8，即恢复完整原始文件，保留原缩进与换行。`bytes`、`sha256` 对应恢复后的原件，不是分片或 JSONL 容器的大小。

```bash
python tools/read_research_evidence.py --search proposal-feedback-audit
python tools/read_research_evidence.py --verify-objects
```

搜索得到完整 source_path 后，作为唯一参数即可输出原件；重定向到新文件可另存。此工具不执行其中的代码、不请求 API、不加载模型。历史 `.py`、shell、工具说明和状态文件都是证据，不能当作当前启动指令。

完整科研报告与当前结论见 [研究总览](../../docs/RESEARCH_OVERVIEW_ZH.md)。原始路径数、对象数、ZIP 数、目录数和请求数不等于新的机器人实验数。Bulk 聚合库与未选观测继续保留在原完整资料包和实验室，不因此宣称 Git 仓库是全服务器镜像。
