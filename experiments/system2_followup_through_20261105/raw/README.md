# 截至11月5日的无损执行文本

分片保存请求、响应、原生结果、动作过程、源码、日志与manifest；重复内容按SHA256去重。每个JSONL成员有sha256、bytes、part/parts、utf8，拼接并UTF-8编码即可恢复原字节。来源路径与公开位置见`provenance/followup-source-index-20261107.csv.gz`。

在仓库根目录执行：

```bash
python3 -B tools/read_followup_evidence.py --verify-objects
python3 -B tools/read_followup_evidence.py --search '31_system2_rgb_validation/20261105_v1/analysis/episode-results.csv'
python3 -B tools/read_followup_evidence.py 'result/29_system2_feedback_api/20261104_v1/protocol.json'
python3 -B tools/verify_followup_evidence.py
```

只读工具不执行原件程序。真实runtime、全部原视频/观测、权重及其他二进制留实验室并标为external。二进制哈希如来自已有归档manifest，会明确注明；本次没有重新进行全视频解码或二进制哈希遍历。

历史绝对路径、暂停、失败和下一步说明保持身份，是溯源材料；后续执行指令不能因被归档而自动生效。最终结论优先读对应最终报告和最新结果页。
