"""Consolidate reviewed native, replay, visibility and physical-state evidence."""
from pathlib import Path
import json,datetime
L=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
s=read(L/'FINAL_SUMMARY.json');replay=read(L/'terminal-replay.json');coverage=read(L/'observation-coverage-audit.json');tracking=read(L/'transport-tracking-audit.json')
assert not (L/'EVIDENCE_INDEX.json').exists()
rr=[r for r in replay['rows'] if r['condition']=='offset_transport'];assert len(rr)==5
assert all(r['terminal_reason']=='initial_observation_loop_bound_exhausted' for r in rr)
cr=[r for r in coverage['rows'] if r['condition']=='offset_transport']
tr=[r for r in tracking['rows'] if r['condition']=='offset_transport'];q=[r for r in tr if r['association_qualified']]
summary=dict(offset_stop_reasons=[r['terminal_reason'] for r in rr],initial_detected_items=[r['first_scene_items'] for r in cr],actual_layout_items=[r['expected_object_count'] for r in cr],layouts_missing_initial_categories=[r['layout_id'] for r in cr if r['missing_categories_first']],new_categories_ignored=[dict(layout=r['layout_id'],categories=r['new_categories_seen_later_but_unassigned']) for r in cr if r['new_categories_seen_later_but_unassigned']],offset_close_cycles=len(tr),qualified_object_associations=len(q),low_lift_under_1cm=sum(r['lift_root_rise_m']<.01 for r in q),large_relative_translation_over_5cm=sum(r['relative_translation_change_m'] is not None and r['relative_translation_change_m']>.05 for r in q),lift_over_2cm_then_relative_change_over_5cm=sum(r['lift_root_rise_m']>.02 and r['relative_translation_change_m'] is not None and r['relative_translation_change_m']>.05 for r in q),tracking_thresholds_are_diagnostic_not_success_criteria=True)
s['mechanism_review']=summary;s['accounting']['recorded_response_replay_cases']=10;s['accounting']['historical_records_for_scoring_audit_preflight']=10
s['next_stage']=dict(root='/mnt/data/joey_tr/physical-RSI/result/39_system2_observation_loop/20261107_v1',variable='Only initial-count loop limit -> fixed6',new_native_cases_planned=5,prior_control_cases_reused=5,api_calls=0)
(L/'FINAL_SUMMARY.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
text='''运输目标修正：机制复核与结论

10个新原生回合已完成，30段视频完整解码通过，8409份文件已逐项校验并归档。原目标和偏移目标各5回合，分数均为0、0、0、0、15/100，完整成功均0/5。没有策略晋升。

执行层面确有改善：完成approach从35到64，规划拒绝从5到0；运输动作由5/10完成变成16/16完成。两个分母不同，后者执行了更多循环，不能当成16个独立场景。两组1100步和评分均未改。

新的停止位置已经核实：用完整记录的接口响应回放原候选，10个回合的请求方法、参数、顺序和数量均逐项一致。原组5回合均在运输规划拒绝后返回；偏移组5回合均耗尽初始观测决定的循环次数，没有未完成的活动调用，也没有异常被吞掉的证据。实际次数只有4、4、2、3、3；真实布局有8、5、3、7、6个对象。这不是到1100步才停，而是候选更早返回后原生保持到终止。

为什么仍不涨分，至少有两层证据：
1. 候选把第一帧当成完整任务清单。布局0、1、2首次分别没有watch、toy_car、camera类别；布局0后来看到watch，但初始assignments不再更新，仍然忽略。布局3、4虽然首次看到了三类，但各只识别到3个物体，循环也被固定为3次。它们并不是都触发了“最多6次”的上限，而是先触发了更小的首次数量上限。
2. 完成运动不等于搬运正确。16次闭爪/搬运中15次对象关联满足预定距离/间隔门槛；其中4次抬升不足1cm，6次对象与末端的相对平移变化超过5cm（这6次包含未成功抬升的情况）。两次对象先抬升超过2cm、随后相对平移变化超过5cm。这些是分析线索，不是接触力证明，不能全部直接命名为滑落。另查看布局2的首次松爪帧和终帧，物体停在篮筐前方，符合保存的对象状态与几何检查；不能把控制器完成运输当成成功放入。

因此，当前瓶颈已从“无法执行下一段轨迹”推进到“起始感知不完整、程序覆盖有限、抓取/放置并不可靠”。这支持检查起始候选及其可用能力，而非继续只增加System2提示词。仍不能据此判断PhysicalRSI通用框架或LLM普遍无效；完整已有控制器的能力接口和这些候选并不等价。

已经继续的新实验：只把range(min(6,len(items)))改为range(6)，开展5个新回合，复用本阶段偏移组5个结果作已有对照。初始类别分配、运输点、抓手、规划、评分、步数和缺少归位全部不改。CPU检查已证实新程序逐项复现旧动作前缀，只在旧结束点多请求一个scene。这个实验只验证循环覆盖假设，不会同时解决新增类别、失抓或放置偏差；不得预先宣称提高得分。

计时与Token：两个完整5回合cohort墙钟分别946.31秒、985.36秒，后者做了更多动作，没有跨项目加速结论。本轮直接执行保存的候选代码，新增API调用0；历史候选生成成本仍属于System2账目，不能把本轮0调用写成生成免费。

证据：FINAL_SUMMARY.json、terminal-replay.json/csv、observation-coverage-audit.json/csv、transport-tracking-audit.json/csv、scoring-condition-audit.json/csv、transport-video-review/frame-index.json、native-validation/。评分几何核查使用冻结源码与元数据，但采样时序可能不同，原生回执仍是成绩唯一依据。
'''
(L/'INTERPRETATION.txt').write_text(text)
with (L/'REPORT.txt').open('a') as f:f.write('\n最终机制复核见INTERPRETATION.txt及4项audit/replay文件。固定6次循环验证已进入下一阶段；本阶段成绩没有提升。\n')
with (L/'RESEARCH_PROGRESS_REVIEW.txt').open('a') as f:f.write('\n七、本轮追加的确定性诊断\n'+text)
review=read(L/'RESEARCH_PROGRESS_REVIEW.json');review['latest_mechanism_review']=summary;review['next_stage']=s['next_stage'];(L/'RESEARCH_PROGRESS_REVIEW.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
qa=dict(reviewed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),task='classify_objects',layout_id=2,condition='offset_transport',reviewed_frames=['transport-video-review/offset_layout2_first_release.png','transport-video-review/offset_layout2_final.png'],finding='At release and final frame, objects remain on table/in front of basket. Do not interpret completed transport as successful placement.',limits='One illustrative case; object identity/coordinates rely on qualified sidecar association. Images do not independently prove grasp-force failure.')
(L/'VISUAL_REVIEW.json').write_text(json.dumps(qa,indent=2)+'\n')
print(json.dumps(summary))
