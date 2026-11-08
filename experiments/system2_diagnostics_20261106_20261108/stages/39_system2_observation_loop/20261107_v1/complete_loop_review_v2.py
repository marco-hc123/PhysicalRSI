"""Finalize the loop pilot and the recent research assessment after verification."""
from pathlib import Path
from collections import Counter
import json,datetime,csv
L=Path(__file__).resolve().parent;P=L.parent.parent/'38_system2_transport_destination/20261107_v1'
def read(p):return json.loads(p.read_text())
assert not (L/'EVIDENCE_INDEX.json').exists()
s=read(L/'FINAL_SUMMARY.json');assert s['state']=='completed'
r=read(L/'driver-contract-replay-v2.json');c=read(L/'observation-coverage-audit.json');t=read(L/'transport-tracking-audit.json');g=read(L/'scoring-condition-audit.json');fixture=read(L/'position-exclusion-audit.json')
assert r['state']=='passed' and r['native_replays']==5
terminal=dict(Counter(x['reason'] for x in r['rows'] if x['mode']=='recorded_native_wrapper'))
probe=read(L/'offline-rejection-probes/execution/summary.json');assert probe['solver_calls']==12
assert read(L/'offline-rejection-probes/execution/ARCHIVE_VERIFIED.json')['state']=='verified'
assert read(L/'prior-stage38-driver-audit.json')['native_replays']==10
qualified=[x for x in t['rows'] if x['association_qualified']]
diag=dict(terminal_reasons=terminal,actual_close_commands_by_layout=[x['actual_close_commands'] for x in c['rows']],initial_visible_items=[x['first_scene_items'] for x in c['rows']],layout_object_counts=[x['expected_object_count'] for x in c['rows']],newly_seen_unassigned_categories=[dict(layout=x['layout_id'],categories=x['new_categories_seen_later_but_unassigned']) for x in c['rows'] if x['new_categories_seen_later_but_unassigned']],qualified_object_associations=len(qualified),close_cycles=len(t['rows']),low_lift_under_1cm=sum(x['lift_root_rise_m'] is not None and x['lift_root_rise_m']<.01 for x in qualified),scoring_condition_audit='scoring-condition-audit.json',symbolic_position_exclusion='position-exclusion-audit.json')
diag.update(wrapper_exception_layouts=[1,4],planner_probe=probe['groups'],upstream_attribution='driver-contract-provenance/attribution.json',superseded_analysis='terminal-replay.json v1 terminal explanations for layouts1,4 superseded by actual-driver replay v2')
s['mechanism_review']=diag;s['accounting'].update(recorded_response_replay_cases=5,exploratory_symbolic_cases=2,cpu_contract_unique_fixtures=10,additional_offline_solver_calls=12,prior_stage_actual_wrapper_replays=10,counterfactual_saved_prefix_replays=15,cpu_contract_validated_on=['local','lab','execution_server'])
(L/'FINAL_SUMMARY.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
gain=s['interpretation']['any_positive_score_delta']
outcome=('出现局部部分分增加，必须进一步独立复核；这是人工代码修正，并非System2自动改进。' if gain else '没有任何布局出现得分增加。固定6次循环并没有解决剩余的任务覆盖和操作可靠性问题。')
text=['固定最多6次循环：最终复核','',
 '本轮只有5个新原生回合、15段原视频；对照是上一阶段5个offset_transport回合，明确复用。没有新增API调用、没有训练、没有策略晋升。',
 '已有对照分数：'+str(s['reused_control']['scores_by_layout_100'])+'；新组分数：'+str(s['new_group']['scores_by_layout_100'])+'；完整成功：'+str(s['new_group']['successes'])+'/5。',
 '得分判断：'+outcome,
 '真实执行次数：'+str(diag['actual_close_commands_by_layout'])+'；退出分支统计：'+json.dumps(terminal,ensure_ascii=False),
 '新增观测中仍未纳入分配的类别：'+json.dumps(diag['newly_seen_unassigned_categories'],ensure_ascii=False),
 '',
 '这一步的意义：上一轮的立即停止点确实是首次观测决定的循环次数，但去掉一个停止点不保证后续有可执行目标。应同时看下一次scene返回了什么、哪些目标被inside/attempted/assignment/basket匹配规则排除；不能把每个提前退出都称为模型报错，也不能只加大动作预算。',
 '额外的两个CPU构造检查把感知和抓取/放置假设为理想，只改变两个同类物体的间距：3cm时仅处理一个，8cm时处理两个。这确认了category+4cm位置排除规则能误排相邻对象；不代表真实布局中的发生比例，也不计为仿真成绩。当前Reader编号也未被证明稳定，不能直接换成编号就声称解决了跟踪。',
 '',
 '当前研究判断：有局部得分变化和执行层面的进展，但近期这批生成候选没有验证出稳定的完整任务成功。问题已具体定位到这套复现执行接口和候选程序的多个环节；尚不能归结为PhysicalRSI通用框架本身无效或LLM能力不足。完整已有技能在同5布局也只是0、15、15、15、40分，且具有更丰富的接口，不能当作等价的模型能力对照。',
 '',
 '关键修正：layout1和4的第35个原生调用返回了action_steps=0的no_collision_free_path。子进程包装层将该字典变成RuntimeError，候选外层except捕获后退出，所以原代码的换臂后备分支没有运行。冻结官方90b322a文件直接返回reply[value]；异常转换来自本实验适配层。不能将此归为官方框架原生错误，也不能证明所有低分都由这一点造成。',
 '已通过实际保存的子进程包装代码重放5回合，精确复现3个无可选目标退出和2个包装异常退出。仅替换异常转换后，两个记录前缀都会发起另一只手的请求；在没有真实响应处立即停止，不虚构执行结果。此前terminal-replay.json未经过真实包装层，且使用可被候选吞掉的AssertionError作记录边界，因而layout1和4的终止解释不可靠；原文件保留，v2明确替代。分数、视频和原始执行记录未改。',
 '回溯阶段38的10回合：原目标组的5次停止也是包装异常，而非候选move返回False后的显式退出。两者均在相同运输调用停止，所以原分数/计数不变；offset组5次首次观测计数限制结论仍成立。更正记录为prior-stage38-driver-audit.json，旧已封存报告保留。',
 '12次离线规划复核：两状态×原机械臂/候选换臂×3种seed。原机械臂0/6返回路径，换臂6/6返回路径；使用对应手的保存关节和候选原姿态。失败点是下一对象的预抓取接近，而非篮筐运输。规划仅含冻结静态几何，不证明实际抓住/放入或全场景无碰撞。',
 '',
 '已继续下一轮：仅修正结构化规划拒绝的返回约定，候选本身、场景、1100步和评分不变，新增5回合，与本轮5回合明确复用对照。结果单列40_system2_rejection_contract，不提前写入本轮结果。',
 '',
 '随后变量设计：',
 'A. 增量类别分配：以本轮固定6次版本为对照，仅改变scene中新出现类别的登记与空篮筐分配。保持感知模型、动作接口、抓取姿态、运输目标、尝试规则、1100步不变。验收记录新增类别是否被赋予有效唯一篮筐、是否实际得到尝试、任务分数/成功数。先验证缺失/重复篮筐等CPU边界，再少量RGB试验；已有布局结果不足以证明泛化。',
 'B. 对象跟踪与重试：先在保存的RGB/scene序列中验证同类相邻对象和移动后对象的匹配，明确未知身份；再单独改变尝试排除/重试规则，固定类别分配及动作接口。验收误排率、重复抓同一对象次数、各对象被实际处理数、完整成功与总动作成本，不能只统计close命令数。',
 'C. 最小抓取/放置执行契约：保持任务和感知限制，分别记录规划返回、动作执行、末端到位、物体是否随手移动、松爪后是否入筐。先验证最小操作单元，再比较恢复策略。分析用的真实物体pose不能回灌给候选；不可观测的成功应报告未知。也要检查候选返回后的idle hold是否保持最后目标，及归位契约。',
 'D. 重新比较System2机制：上述能力经过验收后，固定同一初始技能、相同可用接口、候选数和成本预算，再比较原反馈/结构化可执行反馈。由冻结选择规则决定是否保留候选，随后使用未用于调参的布局。报告生成成本、验证成本和后续复用成本，不把手工修正收益归给模型。',
 '',
 '证据：FINAL_SUMMARY.json；driver-contract-replay-v2.json；prior-stage38-driver-audit.json；observation-coverage-audit.json；transport-tracking-audit.json；scoring-condition-audit.json；position-exclusion-audit.json；transport-video-review/frame-index.json；native-validation/；comparison-with-reused-control.csv。']
(L/'INTERPRETATION.txt').write_text('\n'.join(text)+'\n')
with (L/'REPORT.txt').open('a') as f:f.write('\n完整的退出分支、能力判断和下一轮变量设计见INTERPRETATION.txt。\n')
ledger=list(csv.DictReader((L/'recent-experiment-ledger.csv').open()));count=sum(int(x['cases']) for x in ledger);assert count==128
review=dict(state='completed',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='RecentSystem2followup stages31..39,not whole project historical benchmark',actual_native_executions=count,unique_development_layouts=5,full_successes=sum(int(x['successes']) for x in ledger),latest_stage=s['interpretation'],mechanism_review=diag,new_api_calls_in_manual_stages34_to39=0,policy_promotions=0,retained_policy='pi05',previous_full_review=str(P/'RESEARCH_PROGRESS_REVIEW.txt'),current_report='INTERPRETATION.txt',limits=['128executions are not128independent layouts.','Priorcontrol5cases reused,notaddedagain.','Manual repairs and released controller reference are not proof of automaticSystem2 improvement.'])
(L/'RESEARCH_PROGRESS_REVIEW.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
previous=(P/'RESEARCH_PROGRESS_REVIEW.txt').read_text()
(L/'RESEARCH_PROGRESS_REVIEW.txt').write_text('最新阶段结论（阶段39）\n'+ '\n'.join(text)+'\n\n累计账目：阶段31至39共128个实际原生执行回合，主要复用5个开发布局；完整成功合计'+str(review['full_successes'])+'。不是128个独立场景。\n\n以下保留截至阶段38的逐问题回顾，其123回合账目是当时截止数，不再累加一次。\n\n'+previous)
print(json.dumps(dict(interpretation=s['interpretation'],mechanism=diag,total_native_cases=count,full_successes=review['full_successes']),ensure_ascii=False))
