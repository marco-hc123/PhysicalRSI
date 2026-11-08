"""Write conclusions only after original results, actual wrappers and archives pass."""
from pathlib import Path
from collections import Counter
import csv,datetime,json
L=Path(__file__).resolve().parent;P=L.parent.parent/'39_system2_observation_loop/20261107_v1'
read=lambda p:json.loads(p.read_text())
assert not (L/'EVIDENCE_INDEX.json').exists()
s=read(L/'FINAL_SUMMARY.json');r=read(L/'actual-driver-replay.json');choice=read(L/'choice-filter-audit.json');chain=read(L/'recovery-chain-audit.json');cap=read(L/'current-symbolic-capacity.json');retry=read(L/'bounded-retry-fixtures.json');tracking=read(L/'transport-tracking-audit.json');coverage=read(L/'observation-coverage-audit.json')
assert s['state']=='completed' and r['state']=='passed' and r['native_replays']==5
assert cap['symbolic_cases']==10 and retry['unique_cpu_fixtures']==8
ledger=list(csv.DictReader((L/'recent-experiment-ledger.csv').open()));assert sum(int(x['cases']) for x in ledger)==133
reason=dict(Counter(x['reason'] for x in r['rows']));filter_counts=dict(Counter(y['reason'] for x in choice['rows'] for y in x['terminal_choice_filters']))
qualified=[x for x in tracking['rows'] if x['association_qualified']]
diag=dict(terminal_reasons=reason,terminal_item_filter_counts=filter_counts,rejection_phases=dict(Counter(x['phase'] for x in chain['rows'])),post_fallback_rejections=[x for x in chain['rows'] if x['earlier_fallback_in_this_cycle']],qualified_object_associations=len(qualified),close_cycles=len(tracking['rows']),lift_under_1cm=sum(x['lift_root_rise_m'] is not None and x['lift_root_rise_m']<.01 for x in qualified),missing_categories_first=[dict(layout=x['layout_id'],categories=x['missing_categories_first']) for x in coverage['rows'] if x['missing_categories_first']])
s['mechanism_review']=diag;s['accounting'].update(symbolic_capacity_unique_fixtures=10,bounded_retry_unique_fixtures=8,actual_wrapper_saved_episode_replays=5,fixture_validation_hosts=['local','lab','execution_server'],fixture_host_repetition_is_not_new_native_sample=True)
(L/'FINAL_SUMMARY.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
g=s['new_group'];old=s['reused_control'];gain=s['interpretation']
score_text='本轮出现局部得分变化，必须在固定条件下复测后再判断稳定性；人工接口修正不是System2自动改进。' if gain['any_positive_score_delta'] else '本轮没有布局得分增加。恢复分支能够执行，并不意味着物体已经正确入筐。'
text=['本阶段研究结论与接续说明','',
 '研究问题：System2候选没有提高得分，究竟是候选没写出恢复、反馈没传到候选、物理执行失败，还是任务覆盖不足？本轮把这些层次逐项区分。','',
 '一、最重要的新发现',
 '历史后台记录是错误字典，真实候选端却收到RuntimeError。候选已有字典处理和换臂分支，但包装层提前抛异常，外层except结束了程序。早期这项适配是为了遵守当时抛异常的接口描述；后来能力反馈把后台字典误称为已验证的候选接口，因此问题是实验说明、适配和候选之间不一致，不能归咎于固定官方源码本身，也不能以此认定LLM没有生成恢复能力。',
 '历史更正完整证据见HISTORICAL_CONTRACT_CORRECTION.txt。旧原生得分和视频都保留；更正的是机制解释。阶段33的低分不能再解释为“真实一致的能力反馈无效”，该比较需要在接口一致后重新进行。','',
 '二、已经完成的直接实验',
 '只把零动作规划拒绝转换异常改为原样返回字典；候选代码、memory、感知、布局、动作参数、1100步和评分均保持不变。5个新增原生回合，对照为阶段39的5回合，明确复用。',
 '原对照得分（layout0至4）：'+str(old['scores_by_layout_100'])+'；修正后：'+str(g['scores_by_layout_100'])+'。',
 '平均分：'+str(old['mean_score_100'])+' → '+str(g['mean_score_100'])+' /100；完整成功：'+str(old['successes'])+'/5 → '+str(g['successes'])+'/5。',
 '实际换臂请求：'+str(gain['alternate_arm_requests'])+'；其中完成后备approach：'+str(gain['completed_alternate_approaches'])+'。这才是恢复分支被真正触发的证据。',
 '完成approach：'+str(old['completed_approaches'])+' → '+str(g['completed_approaches'])+'；close指令：'+str(old['close_commands'])+' → '+str(g['close_commands'])+'；完成运输primitive：'+str(old['transport_completed'])+' → '+str(g['transport_completed'])+'。close次数不等于抓住物体数，primitive完成不等于物体送达。',
 score_text,
 '有效cohort墙钟：'+str(round(old['cohort_wall_seconds'],2))+' → '+str(round(g['cohort_wall_seconds'],2))+'秒；包含启动/执行/清理及回执验证，不是纯物理时间。部署失败的启动时间另外记录。',
 '真实终止分支：'+json.dumps(reason,ensure_ascii=False)+'。拒绝发生阶段：'+json.dumps(diag['rejection_phases'],ensure_ascii=False)+'。',
 '后备换臂后再次出现的拒绝：'+json.dumps(diag['post_fallback_rejections'],ensure_ascii=False),
 '含义：一次换臂能够接近物体，并不保证这只手还能完成后续运输；完整抓取—搬运链的可执行性尚未建立。不能把恢复一次等同于任务恢复。','',
 '三、起始候选能力是否有限',
 '有明确的程序能力限制，但没有证据把所有失败归结为模型本身能力不足。',
 '把感知、抓持和释放理想化的CPU检查中，当前固定6次版本在8个和7个对象布局分别仍剩2个和1个对象；仅把循环覆盖到完整初始对象数后，抽象流程可覆盖全部。10个构造检查均不是RGB实验，也不产生原生得分。真实系统仍有漏检，因此不能直接照搬初始计数作为完整任务终止条件。',
 '另外8个CPU构造检查比较一次排除和最多两次附近位置尝试：第一次抓取失败但下次可成功时，后者能够再尝试；两个相距3cm的同类对象也能在构造例子中都处理。持续失败时最多尝试两次，没有无限重试。这只支持一个可测试的修正方向，尚未做该准备候选的RGB成绩验证。',
 '当前真实回合的末次选择过滤：'+json.dumps(filter_counts,ensure_ascii=False)+'。过滤项数不是独立物体数；Reader编号并不保证持续身份。',
 '首次观测缺失类别：'+json.dumps(diag['missing_categories_first'],ensure_ascii=False)+'。候选冻结最初类别分配，之后新出现类别也可能被忽略。',
 '对象跟踪诊断：'+str(len(qualified))+'个满足距离/间隔门槛的关联中，'+str(diag['lift_under_1cm'])+'个在lift末端相对初始高度增加不足1cm。该值是分析用真实pose的诊断代理，不是接触力或抓取成功证明；真值从未输入候选。',
 '此外，候选缺少显式归位阶段，而原生完整成功还有归位与落稳条件；即使部分分类分提高，也不能直接写成完整成功。','',
 '四、过去这段时间是否完全没有改进',
 '不是完全没有：初始增强反馈候选在一个已暴露布局得到15分，原反馈候选为0；名义高度门控旁路也使一条候选从0到该布局15分。这是局部部分分，不能称稳定泛化。',
 '执行层面的进展独立成立：阶段34轨迹执行方式修正使完成approach18→35，活动预算中断3→0；阶段36消除了已核查的闭爪命令丢失；阶段38运输目标修正使完成approach35→64、运输拒绝5→0；阶段39固定6次让完成approach64→72，但原得分均未增加。',
 '完整发布技能参照在同5布局是0、15、15、15、40分，平均17，完整成功0/5。它使用更多感知、规划、到位检查和恢复能力，与生成候选的4个primitive接口不同；它也有到位门槛/重试耗尽问题。因此既提示生成候选能力受限，也提示应验收底层技能；不能当作公平的模型优劣对比。',
 '阶段31至40累计133个实际原生执行，主要重复使用5个开发布局，不是133个独立场景。完整成功累计为'+str(sum(int(x['successes']) for x in ledger))+'。这是近期分类任务System2诊断的范围，不代表整个项目此前所有任务都失败。',
 '本轮没有新增付费API调用或训练，未晋升候选，保留pi05。后台、接口、CPU构造实验、视频和原生结果分开计数。','',
 '五、下一步应按什么顺序实验',
 'A. 先检验完整搬运链的可执行性。处理变量是恢复时的机械臂/放置目标选择规则；先固定失败时的真实关节状态做离线规划，再验证最小RGB抓取—抬升—运输—释放。保持候选其他逻辑、评分和1100步不变。验收规划拒绝、动作实际完成、物体随手运动、放入原生篮筐的证据，以及原生部分分/完整成功，不能只报告返回路径。',
 'B. 单独验证有限重试。已准备prepared-candidates/bounded_retry/candidate.py，只将同类4cm位置排除的次数阈值1改为2，总6次不变。保持接口、感知、姿态和运输规则不变。在暴露布局做小规模RGB配对，记录重复处理、覆盖、动作预算、部分分。CPU8例通过不等于RGB通过。',
 'C. 把对象覆盖、增量类别分配、归位分别作为后续变量；不一次性加入所有修改。感知未返回的对象必须标为未知，不用仿真真值替代候选可见信息。独立布局只在策略冻结后使用。',
 'D. 接口和最小技能链验收后，再重新进行真正的System2反馈比较：同一初始技能、同一可用API、相同候选数/费用预算，记录候选收到的反馈和完整执行日志，再按冻结规则选择并独立验证。生成、验证、后续复用Token成本分开记录。','',
 '六、证据与限制',
 'FINAL_SUMMARY.json；episode-results.csv；comparison-with-reused-control.csv；fallback-events.csv；actual-driver-replay.json；recovery-chain-audit.json；choice-filter-audit.json；current-symbolic-capacity.json；bounded-retry-fixtures.json；transport-tracking-audit.json；scoring-condition-audit.json；transport-video-review/frame-index.json；HISTORICAL_CONTRACT_CORRECTION.txt；native-validation/。',
 '一次部署失败发生在日志目录创建之前，5次setup没有候选执行或有效回执，单列保存，不计作5个策略0分。诊断sidecar按有效cohort的真实simulator PID筛选，失败启动的零帧日志保留但不混入物理统计。',
 '复用的旧对照不是新样本；运行时段和RGB/物理执行存在波动，因此单次布局分差只是描述性结果。机制分支可以由准确调用记录核实，稳定任务收益仍需独立验证。']
(L/'INTERPRETATION.txt').write_text('\n'.join(text)+'\n')
with (L/'REPORT.txt').open('a') as f:f.write('\n完整判断与下一步变量设计：INTERPRETATION.txt。历史能力反馈更正：HISTORICAL_CONTRACT_CORRECTION.txt。\n')
review=dict(state='completed',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Recent classification System2 stages31..40',actual_native_executions=133,unique_development_layouts=5,full_successes=sum(int(x['successes']) for x in ledger),latest=s['interpretation'],mechanism=diag,report='INTERPRETATION.txt',historical_correction='HISTORICAL_CONTRACT_CORRECTION.txt',retained_policy='pi05',manual_repair_is_not_automatic_system2_improvement=True)
(L/'RESEARCH_PROGRESS_REVIEW.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n');(L/'RESEARCH_PROGRESS_REVIEW.txt').write_text('\n'.join(text)+'\n')
print(json.dumps(dict(scores=g['scores_by_layout_100'],interpretation=gain,mechanism=diag,native_total=133),ensure_ascii=False))
