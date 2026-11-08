"""Five new loop-correction cases compared with five explicitly reused controls."""
from pathlib import Path
import json,csv,hashlib,datetime,os
L=Path(__file__).resolve().parent;N=L/'native-validation';P=L.parent.parent/'38_system2_transport_destination/20261107_v1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def table(name,rows):
    if not rows:return
    with (L/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows({k:json.dumps(v) if isinstance(v,(dict,list)) else v for k,v in r.items()} for r in rows)
v=read(N/'migration/ARCHIVE_VERIFIED.json');assert v['state']=='verified' and v['native_cases']==5 and v['videos']==15
m=read(N/'analysis/matrix-analysis.json');prior=read(P/'FINAL_SUMMARY.json');oldm=read(P/'native-validation/analysis/matrix-analysis.json');protocol=read(L/'protocol.json')
assert sha(P/'native-validation/migration/source-manifest.json')==protocol['control_evidence']['archive_manifest_sha256']
proposal=read(L.parent.parent/'33_system2_capability_feedback/20261106_v1/candidates/capability_feedback_2/proposal.json')
source=L/'candidates/fixed_six_turns/candidate.py';assert sha(source)==protocol['conditions'][0]['candidate_sha256']
rows=[];bindings=[]
for a in m['actors']:
    assert a['mapping_qualified'];i=a['mapped_layout_id'];p=N/a['process_record'];packet=read(p.parents[2]/'root/input.json')
    assert packet['source']==source.read_text() and packet['memory']==proposal['memory']
    episode=next(x for x in m['episodes'] if x['layout_id']==i)
    oldep=next(x for x in oldm['episodes'] if x['condition']=='offset_transport' and x['layout_id']==i)
    assert episode['layout_sha256']==oldep['layout_sha256']
    calls=sorted(read(p)['calls'],key=lambda x:x['request']['id']);closed={};after=0;transport=[]
    for c in calls:
        q=c['request'];kw=q['kwargs']
        if q['method']=='gripper':closed[kw['arm']]=kw['command']==0;after=0
        elif q['method']=='approach' and closed.get(kw['arm'],False):
            after+=1
            if after==2:transport.append(c)
    accepted=lambda c:c['state']=='completed' and 'response'in c and not c['response']['value'].get('primitive_error')
    rejected=lambda c:bool(c.get('response',{}).get('value',{}).get('primitive_error'))
    checks=bad=0
    for line in (N/'backend-traces/fixed_six_turns'/a['actor_episode_id']/'0/applied-actions.jsonl').open():
        x=json.loads(line)
        for arm,command in x['last_explicit_commands'].items():checks+=1;bad+=any(abs(y-command)>1e-6 for y in x['applied_action'][arm+'_ee_joint_state'])
    assert bad==0
    row=dict(condition='fixed_six_turns',layout_id=i,score_100=100*episode['normalized_score'],success=episode['success'],close_commands=sum(c['request']['method']=='gripper' and c['request']['kwargs']['command']==0 for c in calls),completed_approaches=a['accepted_approach_calls'],rejected_approaches=a['rejected_approach_calls'],active_budget_cancel=a['native_step_limit_cancelled'],transport_attempts=len(transport),transport_completed=sum(accepted(c) for c in transport),transport_rejected=sum(rejected(c) for c in transport),command_checks=checks,command_mismatches=bad,native_actions=episode['native_action_count'],completed_primitive_action_steps=a['trusted_primitive_action_steps'],actor=a['actor_episode_id'])
    rows.append(row);bindings.append(dict(layout_id=i,source_exact=True,memory_exact=True,source_sha256=sha(source),input_sha256=sha(p.parents[2]/'root/input.json'),layout_sha256=episode['layout_sha256']))
rows.sort(key=lambda x:x['layout_id']);assert len(rows)==5
old=[x for x in prior['cases'] if x['condition']=='offset_transport'];assert len(old)==5
pairs=[]
for b in rows:
    a=next(x for x in old if x['layout_id']==b['layout_id'])
    pairs.append(dict(layout_id=b['layout_id'],reused_control_score=a['score_100'],new_fixed6_score=b['score_100'],score_delta=b['score_100']-a['score_100'],reused_control_close_commands=a['close_commands'],new_fixed6_close_commands=b['close_commands'],reused_control_transport_completed=a['transport_completed'],new_fixed6_transport_completed=b['transport_completed']))
g=dict(condition='fixed_six_turns',cases=5,scores_by_layout_100=[x['score_100'] for x in rows],mean_score_100=sum(x['score_100'] for x in rows)/5,successes=sum(x['success'] for x in rows),cohort_wall_seconds=m['cohorts'][0]['cohort_wall_seconds'])
for key in ['close_commands','completed_approaches','rejected_approaches','active_budget_cancel','transport_attempts','transport_completed','transport_rejected','completed_primitive_action_steps']:g[key]=sum(x[key] for x in rows)
control=next(x for x in prior['groups'] if x['condition']=='offset_transport')
s=dict(state='completed',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),accounting=dict(new_native_cases=5,new_raw_videos=15,reused_control_native_cases=5,new_api_calls=0,new_generated_candidates=0,recorded_prefix_cpu_fixtures=10,lab_gpu_used=False,policy_promotions=0),new_group=g,reused_control=control,cases=rows,pairs=pairs,source_memory_bindings=bindings,archive=v,retained_policy='pi05',interpretation=dict(any_positive_score_delta=any(x['score_delta']>0 for x in pairs),mean_score_delta=g['mean_score_100']-control['mean_score_100'],success_delta=g['successes']-control['successes'],close_command_delta=g['close_commands']-control['close_commands'],transport_completed_delta=g['transport_completed']-control['transport_completed']),limits=protocol['limits'])
(L/'FINAL_SUMMARY.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n');table('episode-results.csv',rows);table('comparison-with-reused-control.csv',pairs)
ledger=list(csv.DictReader((P/'recent-experiment-ledger.csv').open()));assert sum(int(x['cases']) for x in ledger)==123
ledger.append(dict(stage=39,condition='fixed_six_turns',cases=5,successes=g['successes'],mean_score_100=g['mean_score_100'],source='39_system2_observation_loop/20261107_v1/FINAL_SUMMARY.json',role='Only5new cases;stage38offset controls reused,not counted again',scores_100=json.dumps(g['scores_by_layout_100'])))
table('recent-experiment-ledger.csv',ledger)
os.environ['MPLCONFIGDIR']=str(L/'analysis-cache/matplotlib')
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
F=L/'figures';F.mkdir(exist_ok=True);fig,axes=plt.subplots(1,2,figsize=(11,4))
for offset,label,scores,closes in [(-.18,'Stage38 control (reused)',control['scores_by_layout_100'],[next(x['close_commands'] for x in old if x['layout_id']==i) for i in range(5)]),(.18,'Fixed6 (new5cases)',g['scores_by_layout_100'],[x['close_commands'] for x in rows])]:
    axes[0].bar([i+offset for i in range(5)],scores,width=.35,label=label);axes[1].bar([i+offset for i in range(5)],closes,width=.35,label=label)
axes[0].set(ylabel='Native score /100',ylim=(0,100),title='Outcome');axes[1].set(ylabel='Close commands',title='Attempt coverage (not unique objects)')
for ax in axes:ax.set(xlabel='Previously exposed layout',xticks=range(5));ax.legend(fontsize=7)
fig.tight_layout()
for ext in ['png','svg']:fig.savefig(F/('loop_comparison.'+ext),dpi=160)
plt.close(fig)
text=['固定循环上限试验：5个新回合','', '仅将range(min(6,len(items)))改为range(6)。保存的初始类别分配、抓手/轨迹/运输目标、1100步和评分保持不变。对照是上一阶段5个偏移目标回合，明确复用，不再计为新样本。','新组：'+json.dumps(g,ensure_ascii=False),'已有对照：'+json.dumps(control,ensure_ascii=False),'配对表：'+json.dumps(pairs,ensure_ascii=False),'','判断：'+json.dumps(s['interpretation'],ensure_ascii=False),'','循环次数只改变可尝试上限，不能补全感知类别、保证抓住物体或保证放置入筐。接着用原接口响应重放终止分支，并核对对象跟踪和评分条件。','本轮直接回放保存代码的一个人工修改，新增API调用0，不是自动System2改写或策略晋升。','限制：不同运行时段、重复使用开发布局和已有对照，仅作诊断；不能证明独立泛化。','证据：native-validation/（5回合、15视频）、comparison-with-reused-control.csv、protocol.json。历史累计原生回合128，未把复用的5回合加第二次。']
(L/'REPORT.txt').write_text('\n'.join(text)+'\n');print(json.dumps(dict(new_group=g,interpretation=s['interpretation'])))
