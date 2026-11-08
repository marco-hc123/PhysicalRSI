# 离线证据工具

从仓库根目录执行。以下工具使用Python标准库读取现有证据，不请求模型、不训练、不启动仿真。

```bash
python3 -B tools/verify_results.py
python3 -B tools/verify_research_evidence.py
python3 -B tools/verify_followup_evidence.py
python3 -B tools/verify_weekly_package.py --package reports/research_week_20261102_20261108
```

前三项分别核对原始公开补测、11月2日补充材料和11月4–5日后续。第四项核对完整周包的原字节清单与原生/用量账目。核验范围有交叉，不能相加成新增实验数。当前结论和本次综合核验见[RESULTS](../docs/RESULTS.md)、[本次核验回执](../provenance/week-verification-20261108.json)。

```bash
python3 -B tools/read_research_evidence.py --search 'protocol'
python3 -B tools/read_followup_evidence.py --search '31_system2_rgb_validation'
python3 -B tools/read_followup_evidence.py --verify-objects
python3 -B tools/read_week_evidence.py --search '43_system2_multitask'
```

来源读取工具检索公开索引并恢复对应文本，使用方法可看各工具`--help`。原始后台绝对路径用于标识出处；读取去重对象无需连接旧执行主机，也不会执行被读取的脚本。

旧manifest期望的文档版本保存在`provenance/manifest_archive`。`evidence_integrity`只在当前文件不匹配旧哈希时读取对应冻结版本，并继续核对原哈希/字节数，不跳过检查。当前`SOURCES.csv`与本次增补清单由发布整理同步更新，历史清单与原科学结果保留。

实验目录和周包`08_methods`里的历史runner、迁移及归档程序不属于上述只读入口；部分依赖原环境、资产和目录结构。管理协议以历史snapshot文本保存，不激活自动实验或服务。
