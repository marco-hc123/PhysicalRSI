"""Analyze the verified transport-target comparison; CPU only, no policy changes."""
from pathlib import Path
import csv, datetime, hashlib, json, os

L = Path(__file__).resolve().parent
N = L / 'native-validation'
def read(p): return json.loads(p.read_text())
def lines(p): return [json.loads(s) for s in p.read_text().splitlines() if s.strip()]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p, x): p.write_text(json.dumps(x, ensure_ascii=False, indent=2) + '\n')
def table(name, rows):
    if not rows: return
    with (L/name).open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader()
        for r in rows:
            w.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict,list)) else v for k,v in r.items()})

verified = read(N/'migration/ARCHIVE_VERIFIED.json')
assert verified['state'] == 'verified' and verified['native_cases'] == 10 and verified['videos'] == 30
matrix = read(N/'analysis/matrix-analysis.json')
side = read(N/'analysis/postgrasp-analysis.json')
assert side['state'] == 'passed'
protocol = read(L/'protocol.json')
names = [x['name'] for x in protocol['conditions']]
assert names == ['original_transport','offset_transport']
proposal = read(L.parent.parent/'33_system2_capability_feedback/20261106_v1/candidates/capability_feedback_2/proposal.json')
rows, events, bindings = [], [], []
for actor in matrix['actors']:
    assert actor['mapping_qualified']
    name, idx = actor['condition'], actor['mapped_layout_id']
    src = L/'candidates'/name/'candidate.py'
    assert sha(src) == next(x['candidate_sha256'] for x in protocol['conditions'] if x['name'] == name)
    process_path = N/actor['process_record']
    packet = read(process_path.parents[2]/'root/input.json')
    assert packet['source'] == src.read_text() and packet['memory'] == proposal['memory']
    bindings.append(dict(condition=name, layout_id=idx, source_sha256=sha(src), source_exact=True, memory_exact=True, input_file=str((process_path.parents[2]/'root/input.json').relative_to(L))))
    calls = sorted(read(process_path)['calls'], key=lambda x:x['request']['id'])
    closed = {}; cycle = 0; cycle_opened = False; after_close = 0
    local_events = []
    for call in calls:
        req = call['request']; method = req['method']; kw = req['kwargs']
        if method == 'gripper':
            if kw['command'] == 0:
                cycle += 1; after_close = 0; closed[kw['arm']] = True; cycle_opened = False
            else:
                if closed.get(kw['arm']): cycle_opened = True
                closed[kw['arm']] = False
        if method != 'approach': continue
        active = closed.get(kw['arm'], False)
        if active: after_close += 1
        phase = ('lift_after_close' if after_close == 1 else 'transport_after_lift' if after_close == 2 else 'later_closed_motion') if active else 'pregrasp_or_next_cycle'
        value = call.get('response',{}).get('value',{})
        rejected = bool(value.get('primitive_error'))
        accepted = call['state']=='completed' and 'response' in call and not rejected
        event = dict(condition=name,layout_id=idx,actor=actor['actor_episode_id'],cycle=cycle,call_id=req['id'],phase=phase,arm=kw['arm'],target=kw['position_m'],accepted=accepted,rejected=rejected,incomplete=not accepted and not rejected,error=value.get('primitive_error'),state=call['state'])
        local_events.append(event); events.append(event)
    applied = lines(N/'backend-traces'/name/actor['actor_episode_id']/'0/applied-actions.jsonl')
    checks = mismatches = closed_checks = closed_mismatches = 0
    for action in applied:
        for arm,command in action['last_explicit_commands'].items():
            bad = any(abs(v-command)>1e-6 for v in action['applied_action'][arm+'_ee_joint_state'])
            checks += 1; mismatches += bad
            if command == 0: closed_checks += 1; closed_mismatches += bad
    assert mismatches == 0, 'Both conditions must preserve explicit commands'
    transports = [x for x in local_events if x['phase']=='transport_after_lift']
    outcome = next(x for x in matrix['episodes'] if x['condition']==name and x['layout_id']==idx)
    rows.append(dict(condition=name,layout_id=idx,score_100=outcome['normalized_score']*100,success=outcome['success'],native_actions=outcome['native_action_count'],completed_approaches=actor['accepted_approach_calls'],rejected_approaches=actor['rejected_approach_calls'],incomplete_approaches=actor['incomplete_approach_calls'],active_budget_cancel=actor['native_step_limit_cancelled'],transport_attempts=len(transports),transport_completed=sum(x['accepted'] for x in transports),transport_rejected=sum(x['rejected'] for x in transports),close_commands=cycle,command_checks=checks,command_mismatches=mismatches,closed_checks=closed_checks,closed_mismatches=closed_mismatches,completed_primitive_action_steps=actor['trusted_primitive_action_steps'],last_failure=next((x for x in reversed(local_events) if x['rejected'] or x['incomplete']),None),actor_final_state=actor['actor_final_state'],actor=actor['actor_episode_id']))
rows.sort(key=lambda x:(x['condition'],x['layout_id']))
groups=[]
for name in names:
    r=[x for x in rows if x['condition']==name]; assert len(r)==5
    cohort=next(x for x in matrix['cohorts'] if x['condition']==name)
    g=dict(condition=name,cases=5,scores_by_layout_100=[x['score_100'] for x in r],mean_score_100=sum(x['score_100'] for x in r)/5,successes=sum(x['success'] for x in r),cohort_wall_seconds=cohort['cohort_wall_seconds'])
    for field in ['completed_approaches','rejected_approaches','incomplete_approaches','active_budget_cancel','transport_attempts','transport_completed','transport_rejected','close_commands','closed_checks','closed_mismatches','completed_primitive_action_steps']:
        g[field]=sum(x[field] for x in r)
    groups.append(g)
pairs=[]
for idx in range(5):
    a,b=[next(x for x in rows if x['condition']==name and x['layout_id']==idx) for name in names]
    pairs.append(dict(layout_id=idx,original_score=a['score_100'],offset_score=b['score_100'],score_delta=b['score_100']-a['score_100'],original_transport_completed=a['transport_completed'],offset_transport_completed=b['transport_completed'],original_active_cancel=a['active_budget_cancel'],offset_active_cancel=b['active_budget_cancel']))
previous=read(L.parent.parent/'36_system2_gripper_command_contract/20261107_v1/FINAL_SUMMARY.json')
prev_group=next(x for x in previous['groups'] if x['condition']=='latched_command')
summary=dict(state='completed',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),accounting=dict(new_native_cases=10,new_raw_videos=30,new_api_calls=0,new_generated_candidates=0,new_offline_solver_calls=0,lab_gpu_used=False,policy_promotions=0),groups=groups,cases=rows,pairs=pairs,source_memory_bindings=bindings,archive=verified,retained_policy='pi05',previous_same_source_descriptive=dict(stage36_scores=prev_group['scores_by_layout_100'],fresh_control_scores=groups[0]['scores_by_layout_100']),interpretation=dict(any_positive_score_delta=any(x['score_delta']>0 for x in pairs),mean_score_delta=groups[1]['mean_score_100']-groups[0]['mean_score_100'],success_delta=groups[1]['successes']-groups[0]['successes'],transport_completed_delta=groups[1]['transport_completed']-groups[0]['transport_completed']),limits=protocol['limits']+['Transport completion is a returned motion primitive, not confirmed object delivery.','Fixed control-then-treatment order and reused layouts do not support a generalization or speedup claim.','Native action counts include idle hold; completed primitive action steps exclude unfinished calls.'])
dump(L/'FINAL_SUMMARY.json',summary)
table('episode-results.csv',rows);table('paired-layouts.csv',pairs);table('group-summary.csv',groups);table('approach-phases.csv',events)
os.environ['MPLCONFIGDIR']=str(L/'analysis-cache/matplotlib')
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
F=L/'figures';F.mkdir(exist_ok=True)
fig,axes=plt.subplots(1,2,figsize=(11,4))
for offset,name,g in zip([-.18,.18],names,groups):
    axes[0].bar([i+offset for i in range(5)],g['scores_by_layout_100'],width=.35,label=name)
    r=[x for x in rows if x['condition']==name]
    axes[1].bar([i+offset for i in range(5)],[x['transport_completed'] for x in r],width=.35,label=name)
axes[0].set(ylabel='Native score / 100',ylim=(0,100),title='Task outcome')
axes[1].set(ylabel='Completed transport primitives',title='Execution progress (not task success)')
for ax in axes:ax.set(xlabel='Previously exposed layout',xticks=range(5));ax.legend(fontsize=7)
fig.tight_layout()
for ext in ['png','svg']:fig.savefig(F/('transport_target_comparison.'+ext),dpi=160)
plt.close(fig)
text=['运输目标点对照：最终分析','', '问题：此前候选多次在闭爪、抬升之后的运输规划被拒绝。18次离线检查提示目标偏移可恢复轨迹，故本轮用10个新原生回合检验其是否转化为真实任务表现。','变量：仅修改运输目标。两组都固定同一候选其余代码与记忆、RGB感知、姿态、抓手目标保持、轨迹精简、1100步和原生评分；6次循环上限与缺少显式归位仍不改。','']+[json.dumps(g,ensure_ascii=False) for g in groups]+['','逐布局配对：'+json.dumps(pairs,ensure_ascii=False),'','得分判断：'+json.dumps(summary['interpretation'],ensure_ascii=False),'','本轮是人工单变量机制诊断，不是重新生成候选，也不是System2自动获得改进。轨迹返回、动作完成与物体成功分类分别核查。完整成功以原始结果文件为准，不按控制器是否报错判断。','全5个布局已在此前暴露，只能用于开发诊断。完整独立布局验证仍应在确定修正与选择规则后进行。','本轮无API调用、无模型训练、无实验室GPU使用、无策略晋升。','证据：native-validation/（原生回执、30视频、RPC、执行动作与分析侧真值日志）；protocol.json；episode-results.csv；approach-phases.csv；paired-layouts.csv；figures/。']
(L/'REPORT.txt').write_text('\n'.join(text)+'\n')
print(json.dumps(dict(state='completed',groups=groups,interpretation=summary['interpretation']),ensure_ascii=False))
