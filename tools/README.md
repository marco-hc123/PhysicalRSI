# 离线证据工具

从仓库根目录执行，均使用Python标准库，不请求模型、不训练、不启动仿真。

```bash
python3 -B tools/verify_results.py
python3 -B tools/verify_research_evidence.py
python3 -B tools/verify_followup_evidence.py
```

分别核对原始公开补测、11月2日研究证据和11月4–5日后续。第三条从6个供应商响应、35个唯一有效receipt/raw result及30个代码候选动作过程独立复算；不同批次不重复相加。

```bash
python3 -B tools/read_research_evidence.py --search 'protocol'
python3 -B tools/read_followup_evidence.py --search '31_system2_rgb_validation'
python3 -B tools/read_followup_evidence.py --verify-objects
```

旧manifest期待的文档版本保存在provenance/manifest_archive。evidence_integrity只在当前文件不匹配旧哈希时读取对应冻结版本，并继续检查原哈希/字节数，不跳过失败或把当前文档冒充旧版本。SOURCES.csv和ADDITIONS_20261107.csv描述当前文件。

实验目录中的历史runner不属于上述只读检查；管理协议另存snapshot文本，不激活自动实验或服务。
