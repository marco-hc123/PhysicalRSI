# 11月5–8日证据与统计口径

本次将已验证周包中的关键证据复制到本研究档案，观察截至2026-11-08 19:49:30（北京时间；科研档案快照，实验结果已于19:44检查）。服务器原件仍保存在实验室PhysicalRSI研究目录；这里不是完整模型/视频数据副本。

- [原始回执及usage独立复算](audit/independent-recomputation.json)：312条终态评分、44次付费请求、324种源文件哈希；[核验脚本](audit/verify_weekly_receipts.py)按原周包路径读取，复用时需显式调整输入根目录，不在原结果位置运行实验。
- [逐批科学复核](audit/SCIENCE_REVIEW_ZH.md)：12批结果及后续历史解释更正。该文的局部审阅边界保留；服务器新鲜度由主助手另核对。
- [逐回合账本](tables/native_episodes_all.json)、[条件分组](tables/cohort_results_all.json)、[API逐请求账本](tables/api_requests.json)、[11月8日无评分中断](tables/interrupted_native_attempts_batch43.json)。
- [关键原件复制清单](copied-source-manifest.json)：协议、最终汇总、原报告及契约更正逐件SHA256。原报告中已被更正的解释不作最新结论。
- [逐项日志映射](../../history/period_20261105_20261108/README.md)：HIST076–090、EXP015–026；每批连接相应实验室路径与关键原件。

计数边界：整周312=11月2日20+11月5日35+11月6–8日257。11月8日89评分=88正式+1准备smoke，另2中断无评分；11月2日批次25的旧基础设施中断仍为未知，不因本期统计而补0。整周44API包含11月2日System1的一次接入预检；新增26=批次33六次+42八次+43十二次。缓存读/写为input子集，reasoning为output子集，费用是保存历史公式估算。多个选择视图使用同一父策略时只计一次执行。

完整字节读取、格式解析、针对性科学复核和逐帧人工审阅是不同层次。本轮不声称已逐行人工阅读所有依赖源码或逐帧检查全部视频；本次新实验、训练、API及GPU作业均为0。


[具体复现索引](reproduction/README.md)补充12批真实源入口、SHA、布局、配置seed、已保存原生argv及版本绑定；未知命令不猜填。GitHub可携带核验入口为仓库根`python3 -B tools/verify_weekly_package.py --package reports/research_week_20261102_20261108`；本目录audit脚本只保留历史本机路径来源。
