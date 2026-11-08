"""Analyze five actual native cases; reuse prior controls without recounting."""
import csv,datetime,hashlib,json,os
from pathlib import Path
L=Path(__file__).resolve().parent;N=L/'native-validation';P=L.parent.parent/'39_system2_observation_loop/20261107_v1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def table(name,rows):
    if not rows:return
    with (L/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows({k:json.dumps(v) if isinstance(v,(dict,list)) else v for k,v in r.items()} for r in rows)
archive=read(N/'migration/ARCHIVE_VERIFIED.json');assert archive['state']=='verified' and archive['native_cases']==5 and archive['videos']==15
m=read(N/'analysis/matrix-analysis.json');p=read(P/'FINAL_SUMMARY.json');protocol=read(L/'protocol.json')
assert sha(P/'native-validation/migration/source-manifest.json')==protocol['control_evidence']['archive_manifest_sha256']
expected_driver=read(L/'cpu-contract-results.json')['patched_driver_sha256'];source=L/'candidates/structured_rejection/candidate.py'
assert sha(source)==protocol['conditions'][0]['candidate_sha256']==p['source_memory_bindings'][0]['source_sha256']
memory=read(L.parent.parent/'33_system2_capability_feedback/20261106_v1/candidates/capability_feedback_2/proposal.json')['memory']
rows=[];fallback=[];bindings=[]
for a in m['actors']:
    assert a['mapping_qualified'];i=a['mapped_layout_id'];path=N/a['process_record'];root=path.parents[2]/'root';packet=read(root/'input.json')
    assert packet['source']==source.read_text() and packet['memory']==memory and sha(root/'policy.py')==expected_driver
    e=next(x for x in m['episodes'] if x['layout_id']==i);prior=next(x for x in p['source_memory_bindings'] if x['layout_id']==i);assert e['layout_sha256']==prior['layout_sha256']
    calls=sorted(read(path)['calls'],key=lambda x:x['request']['id']);closed={};after=0;transport=[]
    for j,c in enumerate(calls):
        q=c['request'];kw=q['kwargs'];v=c.get('response',{}).get('value',{})
        if q['method']=='gripper':closed[kw['arm']]=kw['command']==0;after=0
        elif q['method']=='approach' and closed.get(kw['arm'],False):
            after+=1
            if after==2:transport.append(c)
        if q['method']=='approach' and isinstance(v,dict) and v.get('primitive_error')=='no_collision_free_path':
            nxt=calls[j+1] if j+1<len(calls) else None;nq=nxt['request'] if nxt else {};nk=nq.get('kwargs',{})
            changed=nq.get('method')=='approach' and nk.get('arm')!=kw['arm'] and nk.get('position_m')==kw['position_m']
            fallback.append(dict(layout_id=i,rejected_call_id=q['id'],arm=kw['arm'],position=kw['position_m'],alternate_arm_requested=changed,next_request=nq,next_response=nxt.get('response') if nxt else None,alternate_trajectory_completed=bool(changed and nxt.get('state')=='completed' and not nxt.get('response',{}).get('value',{}).get('primitive_error'))))
    accepted=lambda c:c.get('state')=='completed' and 'response' in c and not c['response']['value'].get('primitive_error')
    checks=bad=0
    for line in (N/'backend-traces/structured_rejection'/a['actor_episode_id']/'0/applied-actions.jsonl').open():
        action=json.loads(line)
        for arm,command in action['last_explicit_commands'].items():checks+=1;bad+=any(abs(y-command)>1e-6 for y in action['applied_action'][arm+'_ee_joint_state'])
    assert bad==0
    binding=read(N/'backend-traces/structured_rejection'/a['actor_episode_id']/'0/driver-contract.jsonl');assert binding['patched_sha256']==expected_driver
    rows.append(dict(condition='structured_rejection',layout_id=i,score_100=100*e['normalized_score'],success=e['success'],close_commands=sum(c['request']['method']=='gripper' and c['request']['kwargs']['command']==0 for c in calls),completed_approaches=a['accepted_approach_calls'],rejected_approaches=a['rejected_approach_calls'],active_budget_cancel=a['native_step_limit_cancelled'],transport_attempts=len(transport),transport_completed=sum(accepted(c) for c in transport),completed_primitive_action_steps=a['trusted_primitive_action_steps'],command_checks=checks,command_mismatches=bad,actor=a['actor_episode_id']))
    bindings.append(dict(layout_id=i,source_sha256=sha(source),driver_sha256=expected_driver,memory_exact=True,layout_sha256=e['layout_sha256']))
rows.sort(key=lambda x:x['layout_id']);assert len(rows)==5
g=dict(condition='structured_rejection',cases=5,scores_by_layout_100=[x['score_100'] for x in rows],mean_score_100=sum(x['score_100'] for x in rows)/5,successes=sum(x['success'] for x in rows),cohort_wall_seconds=m['cohorts'][0]['cohort_wall_seconds'])
for k in ['close_commands','completed_approaches','rejected_approaches','active_budget_cancel','transport_attempts','transport_completed','completed_primitive_action_steps']:g[k]=sum(x[k] for x in rows)
control=p['new_group'];pairs=[]
for b in rows:
    a=next(x for x in p['cases'] if x['layout_id']==b['layout_id']);pairs.append(dict(layout_id=b['layout_id'],control_score=a['score_100'],new_score=b['score_100'],score_delta=b['score_100']-a['score_100'],control_close_commands=a['close_commands'],new_close_commands=b['close_commands']))
summary=dict(state='completed',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),accounting=dict(new_native_cases=5,new_raw_videos=15,reused_control_native_cases=5,invalid_deployment_attempts=1,invalid_setup_starts=5,new_api_calls=0,new_generated_candidates=0,cpu_contract_unique_fixtures=6,cpu_assembly_unique_fixtures=1,lab_gpu_used=False,policy_promotions=0),new_group=g,reused_control=control,cases=rows,pairs=pairs,source_memory_bindings=bindings,fallback_events=fallback,archive=archive,retained_policy='pi05',interpretation=dict(mean_score_delta=g['mean_score_100']-control['mean_score_100'],success_delta=g['successes']-control['successes'],any_positive_score_delta=any(x['score_delta']>0 for x in pairs),alternate_arm_requests=sum(x['alternate_arm_requested'] for x in fallback),completed_alternate_approaches=sum(x['alternate_trajectory_completed'] for x in fallback)),limits=protocol['limits'])
(L/'FINAL_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');table('episode-results.csv',rows);table('comparison-with-reused-control.csv',pairs);table('fallback-events.csv',fallback)
ledger=list(csv.DictReader((P/'recent-experiment-ledger.csv').open()));assert sum(int(x['cases']) for x in ledger)==128
ledger.append(dict(stage=40,condition='structured_rejection',cases=5,successes=g['successes'],mean_score_100=g['mean_score_100'],source='40_system2_rejection_contract/20261107_v1/FINAL_SUMMARY.json',role='5newcases;5stage39controls reused;setupfailure excluded',scores_100=json.dumps(g['scores_by_layout_100'])));table('recent-experiment-ledger.csv',ledger)
os.environ['MPLCONFIGDIR']=str(L/'analysis-cache/matplotlib')
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
fig,axes=plt.subplots(1,2,figsize=(10,4))
for offset,name,scores,close in [(-.18,'Exception wrapper (reused)',control['scores_by_layout_100'],[r['close_commands'] for r in p['cases']]),(.18,'Structured rejection',g['scores_by_layout_100'],[r['close_commands'] for r in rows])]:
    axes[0].bar([i+offset for i in range(5)],scores,.35,label=name);axes[1].bar([i+offset for i in range(5)],close,.35,label=name)
axes[0].set(ylabel='Native score /100',ylim=(0,100));axes[1].set(ylabel='Close commands (not unique objects)')
for ax in axes:ax.set(xlabel='Previously exposed layout',xticks=range(5));ax.legend(fontsize=7)
fig.tight_layout();(L/'figures').mkdir(exist_ok=True)
for ext in ['png','svg']:fig.savefig(L/('figures/rejection_contract.'+ext),dpi=160)
plt.close(fig)
(L/'REPORT.txt').write_text('结构化规划拒绝：5个新增原生回合\n\n仅更改子进程包装层的零动作规划拒绝返回约定；候选源码和memory与阶段39完全相同。布局、评分、1100步保持不变。阶段39的5个对照明确复用，不重复累计。\n新组：'+json.dumps(g,ensure_ascii=False)+'\n已有对照：'+json.dumps(control,ensure_ascii=False)+'\n差异：'+json.dumps(summary['interpretation'],ensure_ascii=False)+'\n\n此前一次部署在日志目录创建前失败，5次初始化没有候选执行、没有有效回合，不能计作5个策略0分。已保留原始错误与仅创建日志目录的修复。\n本轮API调用0，未重新生成候选或训练，也没有策略晋升。人工修复接口后发生的变化不能直接归功于System2自动改进。详细机制分析见INTERPRETATION.txt。\n')
print(json.dumps(dict(new_group=g,interpretation=summary['interpretation'],fallback_events=fallback)))
