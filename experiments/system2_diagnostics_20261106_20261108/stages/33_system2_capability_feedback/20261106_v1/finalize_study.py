"""Aggregate completed, independently verified native and generation evidence."""
import collections,datetime,hashlib,json,statistics
from pathlib import Path
L=Path('/mnt/data/joey_tr/physical-RSI/result/33_system2_capability_feedback/20261106_v1');N=L/'native-validation'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):(L/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
assert not (L/'FINAL_SUMMARY.json').exists()
archive=read(N/'migration/ARCHIVE_VERIFIED.json');validation=read(N/'analysis/independent-validation.json')
assert archive['state']=='verified' and archive['native_cases']==30 and archive['videos']==90
assert validation['state']=='passed' and validation['valid_native_cases']==30
d=read(N/'analysis/matrix-analysis.json');assert d['complete'] and d['qualified_cases']==30
generation=read(L/'generation-analysis/summary.json');features=read(L/'generation-analysis/source-features.json');protocol=read(L/'protocol.json')
ledger=read(L/'ledger.json');cases=d['episodes'];actors=d['actors'];cohorts=d['cohorts'];assert len(cohorts)==6
code_memory_checks=[]
for r in ledger:
 name=r['id'];candidate=L/'candidates'/name/'candidate.py';proposal=read(candidate.parent/'proposal.json')
 harness=N/'native-campaign/harnesses'/name
 assert sha(candidate)==r['source_sha256']==sha(harness/'code/classify_objects.py')
 assert read(harness/'memory_rules.json')['classify_objects']==proposal['memory']
 code_memory_checks.append(dict(candidate=name,source_sha256=sha(candidate),source_exact=True,memory_exact=True))
actual_input_checks=[]
for actor in actors:
 name=actor['condition'];packet_path=(N/actor['process_record']).parents[2]/'root/input.json'
 packet=read(packet_path);proposal=read(L/'candidates'/name/'proposal.json')
 assert packet['source']==proposal['source'] and packet['memory']==proposal['memory']
 actual_input_checks.append(dict(candidate=name,actor=actor['actor_episode_id'],input_file=str(packet_path.relative_to(N)),input_sha256=sha(packet_path),source_exact=True,memory_exact=True))
assert len(actual_input_checks)==30
case_rows=[]
for ep in sorted(cases,key=lambda x:(x['condition'],x['layout_id'])):
 name=ep['condition'];matches=[a for a in actors if a['condition']==name and a['mapping_qualified'] and a['mapped_layout_id']==ep['layout_id']]
 assert len(matches)<=1
 a=matches[0] if matches else None
 stop=('unqualified_actor_mapping' if a is None else
       'native_step_limit_cancelled_active_execution' if a['native_step_limit_cancelled'] else
       'returned_after_planning_rejection' if a['first_error'] and a['return_record_exists'] else
       'returned_without_recorded_planning_rejection' if a['return_record_exists'] else
       'actor_error_or_other_stop')
 case_rows.append(dict(candidate=name,arm=name.rsplit('_',1)[0],layout=ep['layout_id'],score_100=ep['normalized_score']*100,success=ep['success'],native_steps=ep['native_action_count'],stop_class=stop,
  actor_mapping_qualified=bool(a),rpc_calls=a['rpc_calls'] if a else None,accepted_approaches=a['accepted_approach_calls'] if a else None,
  rejected_approaches=a['rejected_approach_calls'] if a else None,incomplete_approaches=a['incomplete_approach_calls'] if a else None,
  post_error_calls=a['calls_after_first_error'] if a else None,first_error=a['first_error'] if a else None,
  completed_primitive_steps=a['trusted_primitive_action_steps'] if a else None,receipt=ep['receipt'],actor_record=a['process_record'] if a else None))
candidate_rows=[]
for entry in ledger:
 name=entry['id'];rs=[r for r in case_rows if r['candidate']==name];c=next(x for x in cohorts if x['condition']==name)
 assert len(rs)==5
 candidate_rows.append(dict(candidate=name,arm=entry['arm'],replicate=entry['replicate'],cases=5,
  scores_by_layout_100=[r['score_100'] for r in sorted(rs,key=lambda x:x['layout'])],successes=sum(r['success'] for r in rs),mean_score_100=statistics.mean(r['score_100'] for r in rs),
  stop_classes=dict(collections.Counter(r['stop_class'] for r in rs)),native_cohort_full_wall_s=c['cohort_wall_seconds'],
  generation_total_tokens=entry['usage']['total_tokens'],generation_estimated_usd=entry['estimated_standard_usd']))
arm_rows=[]
for arm in ['legacy_feedback','capability_feedback']:
 rs=[r for r in case_rows if r['arm']==arm];cs=[r for r in candidate_rows if r['arm']==arm]
 arm_rows.append(dict(arm=arm,generated_candidates=3,native_cases=15,unique_exposed_layouts=5,successes=sum(r['success'] for r in rs),mean_score_100=statistics.mean(r['score_100'] for r in rs),
  candidate_means_100=[r['mean_score_100'] for r in cs],stop_classes=dict(collections.Counter(r['stop_class'] for r in rs)),
  cases_with_post_error_calls=sum(bool(r['post_error_calls']) for r in rs),total_native_full_wall_s=sum(r['native_cohort_full_wall_s'] for r in cs)))
accounting=dict(new_generation_api_calls=6,new_generated_candidates=6,cpu_general_fixture_checks=120,cpu_error_contract_checks=24,new_native_cases=30,unique_exposed_native_layouts=5,new_raw_videos=90,offline_gpu_calls=0,training_steps=0,policy_promotions=0,new_paid_api_estimate_usd=generation['estimated_total_usd'],cumulative_reviewed_api_estimate_usd=generation['cumulative_reviewed_api_estimate_usd'],conservative_combined_reserve_usd=protocol['combined_reserved_upper_usd'],user_cap_usd=10)
summary=dict(state='completed',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),question=protocol['question'],accounting=accounting,arms=arm_rows,candidates=candidate_rows,cases=case_rows,source_memory_binding_checks=code_memory_checks,actual_isolated_actor_input_checks=actual_input_checks,
 source_behavior=dict(dynamic_lift_guard_candidates_control=0,dynamic_lift_guard_candidates_treatment=0,bounded_no_path_fallback_candidates_control=0,bounded_no_path_fallback_candidates_treatment=3),
 contract_check=read(L/'error-contract-check/summary.json'),generation=generation,archive=archive,
 retained_policy='pi05',selection='No fresh parent selection or independent heldout acceptance performed; this is a generated-candidate mechanism comparison.',
 limitations=protocol['limitations']+['CPU fixtures are not physical episodes.','Native stop classifications derive from actual actor records, not episode length alone.','No inference of full task success from partial score or extra actions.','Native execution of saved code uses0 paid language-model calls; generation costs are separate.'])
save('FINAL_SUMMARY.json',summary)
lines=['PhysicalRSI：明确接口能力反馈的候选生成与原生验证报告','',
 '一、研究问题','此前发现候选对名义高度、漏检、规划错误和预算可见性的假设与当前部署不一致。本轮检查：明确这些能力边界后，模型是否改变候选行为，原生任务表现是否改善。',
 '这次是新模型生成候选的对照，未手工修改生成代码。它仍是受控的System2候选生成—验证阶段实验，没有把任何候选提升为正式策略。',
 '', '二、实验设计与公平性','对照使用历史增强反馈，并加入相同的最新失败源码和停止事实；处理组在完全相同的信息之后，仅附加已核实的接口能力说明。两组各生成3个候选，模型gpt-6.1-sol、medium、最大输出12000、JSON格式和调用模式相同。生成顺序为对照、处理、处理、对照、对照、处理；不是配对固定随机种子。',
 '相较前一份草案，本轮把最新失败源码与停止事实同时提供给两组，以避免把这部分信息与接口说明混为一个处理变量。修改在生成前冻结，见protocol.json。',
 '每个候选都用原来的5个已暴露布局、同一冻结运行器、原生评分和1100步预算测试；完整生成代码与proposal记忆均原样绑定。30个回合不是30个独立布局，也不是完整RoboDojo榜单。',
 '', '三、模型生成与接口检查','6次生成均得到有效JSON和Python源码，6个候选通过代码准入。120项通用CPU检查另加24项当前错误返回契约检查，均不包含真实物理任务得分。',
 '两个组均去掉此前的抬升高度门槛，因此不能把去掉门槛单独归功于处理组。处理组3个候选都显式识别零执行的no_collision_free_path，并允许一次接触前换臂；对照3个候选均结束。遇到未知错误或执行状态不确定的异常，两组均停止。',
 '旧通用named_no_path测试抛异常，和当前兼容层返回错误字典不完全相同，因此额外加入24项明确区分两者的检查，旧测试保留。CPU验证证明分支行为，不能证明恢复动作安全或任务成功。',
 '所有生成记忆均已绑定，但6个候选本身不读取memory参数，见source-features.json。',
 '', '四、原生任务结果','候选 | 布局0..4得分/100 | 完整成功 | 平均分/100']
for c in candidate_rows:lines.append(f"{c['candidate']} | {c['scores_by_layout_100']} | {c['successes']}/5 | {c['mean_score_100']:.2f}")
lines+=['','分组描述（每组3候选×同5布局）：']
for a in arm_rows:lines.append(f"{a['arm']}：完整成功{a['successes']}/15，平均分{a['mean_score_100']:.2f}；候选平均分分别{a['candidate_means_100']}；停止原因{a['stop_classes']}。")
delta=arm_rows[1]['mean_score_100']-arm_rows[0]['mean_score_100']
lines+=['',f'处理组减对照组的描述性平均分差为{delta:.2f}/100。样本少、布局重复暴露、生成随机性和多项代码行为差异限制解释，不报告统计显著提升或独立泛化。',
 '', '五、动作与失败阶段逐例核查']
for r in case_rows:lines.append(f"{r['candidate']}/layout{r['layout']}：score={r['score_100']:g}，success={r['success']}，停止={r['stop_class']}，完成approach={r['accepted_approaches']}，规划拒绝={r['rejected_approaches']}，未完成approach={r['incomplete_approaches']}，首次错误后调用={r['post_error_calls']}。")
lines+=['','所有回合到1100步不意味着候选都耗尽预算：候选提前return后，原生评估仍可能保持姿态至上限。只有活动调用、取消记录与自然步数终止一起满足时，才归入执行预算终止。额外动作或错误后重试也不等于完成搬运。',
 '', '六、Token、费用与速度口径',
 f"对照每次输入15316Token，处理15755Token，增加439（{generation['additional_input_percent']:.2f}%）。平均总Token分别17509与18144。此处是生成成本，不是两个项目的执行Token节省比例。",
 f"本轮API估算{generation['estimated_total_usd']:.7f}美元，连同此前已核查费用约{generation['cumulative_reviewed_api_estimate_usd']:.7f}美元；两批保守预留合计{protocol['combined_reserved_upper_usd']:.6f}美元，低于10美元上限，发票为准。",
 '缓存读和缓存写是输入的互斥子集，reasoning是输出子集，没有重复累加。处理组费用较低可能源于缓存命中和调用顺序，不能解释成输入更少。原生执行保存代码时无语言模型API调用，不能与生成费用混算。',
 '每个候选的native_cohort_full_wall_s含策略启动、执行、清理与证据验证。API时间另记，未从视频编码时间推导物理时间；没有跨项目加速倍数。',
 '', '七、结论边界与下一步','当前结果可用于判断反馈是否改变行为及在这5个布局上的表现，不能证明完整系统所有任务的效果。pi05仍为此前保留策略，尚未进行本轮候选的正式父策略替换或独立布局验收。',
 '下一轮应先依据逐例停止原因选择一个处理变量：若失败仍在搬运规划，则固定候选与感知，比较有界目标调整/恢复；若明确耗尽步数，则固定评分和候选，先做单独预算诊断，或在原预算下比较动作效率。不要把放宽预算的分数作为原基准提升。',
 '只有开发结果稳定改善后，再冻结选择并使用未参与反馈和调参的新布局验证。新反馈内容、动作修改与步数放宽应分别建组，保留所有失败候选。',
 '', '八、完整账目与资料入口',json.dumps(accounting,ensure_ascii=False,indent=2),
 'protocol.json、requests/、responses/、ledger.json：生成方案、每次请求响应和费用；不含API密钥。',
 'candidates/：原始生成代码、记忆和理由；offline-validation/与error-contract-check/：CPU准入和接口实验。',
 'generation-analysis/：逐请求Token和代码特征行号。',
 'native-validation/：30个原生回合、90段原始视频、全部回执与动作记录。',
 'native-validation/analysis/：可编辑CSV/JSON总表、原始视频索引、完整解码验证、布局与运行版本。',
 'native-validation/migration/ARCHIVE_VERIFIED.json：逐文件回传校验；FINAL_SUMMARY.json：最终机器可读统计。',
 '历史20个诊断回合、此前35个补测回合以及更早研究均只作引用，不在本轮30个回合内重复累计。']
(L/'REPORT.txt').write_text('\n'.join(lines)+'\n')
print(json.dumps(dict(state='completed',accounting=accounting,arms=arm_rows,candidates=candidate_rows),ensure_ascii=False))
