"""Summarize verified execution-contract results; retain physical outcome limits."""
import collections, csv, datetime, hashlib, json, statistics
from pathlib import Path
L = Path('/mnt/data/joey_tr/physical-RSI/result/34_system2_trajectory_contract/20261106_v1')
N = L / 'native-validation'
P = Path('/mnt/data/joey_tr/physical-RSI/result/33_system2_capability_feedback/20261106_v1')
def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x): (L/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
assert not (L/'FINAL_SUMMARY.json').exists()
archive=read(N/'migration/ARCHIVE_VERIFIED.json')
assert archive['state']=='verified' and archive['native_cases']==10 and archive['videos']==30
assert read(N/'analysis/independent-validation.json')['state']=='passed'
d=read(N/'analysis/matrix-analysis.json');assert d['qualified_cases']==10 and d['complete']
source=P/'candidates/capability_feedback_2/candidate.py';proposal=read(source.parent/'proposal.json')
cases=[];traces=[];bindings=[]
for a in sorted(d['actors'],key=lambda a:(a['condition'],a['mapped_layout_id'])):
    assert a['mapping_qualified']
    packet=(N/a['process_record']).parents[2]/'root/input.json';x=read(packet)
    assert x['source']==proposal['source'] and x['memory']==proposal['memory']
    bindings.append(dict(condition=a['condition'],layout=a['mapped_layout_id'],input_file=str(packet.relative_to(N)),input_sha256=sha(packet),source_sha256=sha(source),code_exact=True,memory_exact=True))
    ep=next(e for e in d['episodes'] if e['condition']==a['condition'] and e['layout_id']==a['mapped_layout_id'])
    stop=('native_step_limit_cancelled_active_execution' if a['native_step_limit_cancelled'] else
          'returned_after_planning_rejection' if a['first_error'] and a['return_record_exists'] else
          'returned_without_recorded_planning_rejection' if a['return_record_exists'] else 'other_actor_stop')
    candidates=sorted((N/'backend-traces'/a['condition']/a['actor_episode_id']).glob('*/trajectory-*.json'))
    assert len(candidates)<=a['approach_calls'],(a['condition'],a['mapped_layout_id'],len(candidates),a['approach_calls'])
    local=[]
    for p in candidates:
        t=read(p)
        row=dict(condition=a['condition'],layout=a['mapped_layout_id'],plan_index=t['index'],state=t['state'],
                 mode=t['mode'],dense_waypoints=t.get('dense_waypoints'),selected_waypoints=t.get('executed_waypoints'),
                 execution_complete_without_error='primitive_return' in t and not t['primitive_return'].get('primitive_error'),
                 completed_action_steps=t.get('primitive_return',{}).get('action_steps'),
                 projected_error=t.get('primitive_return',{}).get('primitive_error'),
                 execution_exception=t.get('execution_exception'),
                 final_observed_joint_error_rad=t.get('final_observed_joint_error_rad'),
                 selection_diagnostic=t.get('selection_diagnostic'),trace=str(p.relative_to(N)),trace_sha256=sha(p))
        local.append(row);traces.append(row)
    cases.append(dict(condition=a['condition'],layout=a['mapped_layout_id'],score_100=ep['normalized_score']*100,success=ep['success'],
                      approach_calls=a['approach_calls'],traced_plans=len(candidates),untraced_approaches=a['approach_calls']-len(candidates),
                      stop_class=stop,accepted_approaches=a['accepted_approach_calls'],rejected_approaches=a['rejected_approach_calls'],
                      incomplete_approaches=a['incomplete_approach_calls'],completed_primitive_steps=a['trusted_primitive_action_steps'],
                      completed_approach_steps=a['trusted_steps_by_operation'].get('approach',0),
                      proposed_dense_waypoints=sum(t['dense_waypoints'] or 0 for t in local),
                      proposed_selected_waypoints=sum(t['selected_waypoints'] or 0 for t in local),
                      receipt=ep['receipt'],actor_record=a['process_record']))
assert len(cases)==len(bindings)==10
groups=[]
for mode in ['dense','released_waypoint_thinning']:
    rows=[x for x in cases if x['condition']==mode];c=next(c for c in d['cohorts'] if c['condition']==mode)
    groups.append(dict(condition=mode,cases=len(rows),successes=sum(x['success'] for x in rows),
                       scores_by_layout_100=[x['score_100'] for x in sorted(rows,key=lambda r:r['layout'])],
                       mean_score_100=statistics.mean(x['score_100'] for x in rows),
                       stop_classes=dict(collections.Counter(x['stop_class'] for x in rows)),
                       completed_primitive_steps=sum(x['completed_primitive_steps'] for x in rows),
                       completed_approaches=sum(x['accepted_approaches'] for x in rows),
                       full_cohort_wall_s=c['cohort_wall_seconds']))
paired=[]
for layout in range(5):
    c=next(x for x in cases if x['condition']=='dense' and x['layout']==layout)
    t=next(x for x in cases if x['condition']=='released_waypoint_thinning' and x['layout']==layout)
    paired.append(dict(layout=layout,dense_score_100=c['score_100'],thin_score_100=t['score_100'],score_difference_100=t['score_100']-c['score_100'],dense_stop=c['stop_class'],thin_stop=t['stop_class'],dense_completed_primitive_steps=c['completed_primitive_steps'],thin_completed_primitive_steps=t['completed_primitive_steps']))
offline=read(L/'offline-contract/summary.json')
account=dict(new_native_cases=10,unique_previously_exposed_layouts=5,new_raw_videos=30,new_generated_candidates=0,reused_saved_candidate=1,
             new_paid_api_calls=0,new_paid_api_usd=0,lab_gpu_used=False,new_solver_calls_offline=0,
             historical_saved_trajectories_rechecked=24,cpu_selection_checks=48,cpu_invalid_fixture_checks=5,policy_promotions=0)
summary=dict(state='completed',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),question='Does released waypoint selection reduce execution-budget blockage under identical candidate code and native task limits?',
             accounting=account,groups=groups,cases=cases,paired_layouts=paired,source_memory_binding_checks=bindings,
             trace_count=len(traces),offline_summary={k:v for k,v in offline.items() if k not in ['rows','invalid_fixtures']},
             source_sha256=sha(source),retained_policy='pi05',archive=archive,
             limitations=['Manual compatibility-adapter diagnostic, not automatic System2 policy improvement.',
                          'Only waypoint selection changes; the released skill also has cone IK and endpoint gates not adopted here.',
                          'Static chord bounds and native sampled endpoints do not certify full scene collision safety.',
                          'Proposed waypoint counts include paths that might not finish. Completed steps exclude partial cancelled actions.',
                          'Five reused layouts and one chosen candidate do not establish independent generalization.',
                          'Task termination can include hold actions after candidate return; full wall time differs from active primitive time.',
                          'This fresh10case comparison does not recount historical stage33 or stage32 episodes.'])
save('FINAL_SUMMARY.json',summary);save('trajectory-events.json',traces)
for name,rows in [('paired-layout-results.csv',paired),('episode-results.csv',cases),('trajectory-events.csv',traces)]:
    with (L/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader()
        for r in rows:w.writerow({k:json.dumps(v) if isinstance(v,(dict,list)) else v for k,v in r.items()})
lines=['PhysicalRSI：轨迹执行契约诊断','',
'研究问题：上一轮部分候选耗尽原生1100步预算。发布技能会筛选waypoint，当前兼容接口执行全部原始规划采样。本轮固定capability_feedback_2的源码和记忆，只改变waypoint选择，检验执行瓶颈。',
'两组各5个相同已暴露布局；dense为本轮新跑的对照，released_waypoint_thinning使用发布函数，参数max_joint_step=.12、chord_tolerance=.01。没有修改目标位姿、感知、规划器参数、抓手步数、原生评分或1100步上限。没有新增API或训练。',
'这属于人工设计的接口诊断，不是System2自行改出了这个接口。还没有采用发布技能的全部控制逻辑，尤其未添加cone IK和末端收敛等待。','',
'CPU检查：复用24条历史规划轨迹，48次dense/thin选择检查，另5个无效输入拒绝检查。静态合格不代表物理成功。','',
'原生结果：']
for g in groups:lines.append(f"{g['condition']}：得分{g['scores_by_layout_100']}，完整成功{g['successes']}/5，平均分{g['mean_score_100']:.2f}/100；停止原因{g['stop_classes']}；完成移动{g['completed_approaches']}次。")
lines+=['','逐布局比较：']+[json.dumps(x,ensure_ascii=False) for x in paired]
lines+=['','解释边界：']+summary['limitations']+['','完整账目：',json.dumps(account,ensure_ascii=False,indent=2),
'','证据：protocol.json；offline-contract/summary.json；native-validation/analysis/；native-validation/backend-traces/；FINAL_SUMMARY.json；trajectory-events.csv；native-validation/migration/ARCHIVE_VERIFIED.json。',
'正式结论与下一步需结合逐动作诊断和代表性视频核查后补充，不根据节省waypoint数量自动宣称成功。']
(L/'REPORT.txt').write_text('\n'.join(lines)+'\n')
print(json.dumps(dict(state='completed',accounting=account,groups=groups),ensure_ascii=False))
