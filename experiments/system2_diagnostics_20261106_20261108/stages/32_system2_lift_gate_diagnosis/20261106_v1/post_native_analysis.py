"""Lab-only paired analysis and fresh-observation counterfactual prefix replay."""
import collections
import datetime
import hashlib
import json
import math
from pathlib import Path
import sys
R=Path('/mnt/data/joey_tr/physical-RSI/result/32_system2_lift_gate_diagnosis/20261106_v1')
N=R/'native-validation'
sys.path.insert(0,str(R))
from offline_replay import replay,equal
def read(p):return json.loads(p.read_text())
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert read(N/'migration/ARCHIVE_VERIFIED.json')['state']=='verified'
d=read(N/'analysis/matrix-analysis.json');assert d['qualified_cases']==10 and d['complete']
out=R/'post-native-analysis';out.mkdir(exist_ok=True)
assert not (out/'summary.json').exists(),'Do not silently repeat a completed analysis'
sources={n:(R/'candidates'/n/'candidate.py').read_text() for n in ['original','bypass_lift_guard']}
expected=['scene','scene','gripper','approach','approach','gripper','approach','scene']
actors={};replays=[];skipped=[]
for a in d['actors']:
    if not a['mapping_qualified']:
        skipped.append(dict(condition=a['condition'],reason='unqualified_actor_layout_mapping',record=a['process_record']));continue
    key=(a['condition'],a['mapped_layout_id']);assert key not in actors
    p=N/a['process_record'];proc=read(p);calls=sorted(proc['calls'],key=lambda c:c['request']['id'])
    row=dict(condition=a['condition'],layout_id=a['mapped_layout_id'],record=a['process_record'],record_sha256=sha(p),
        methods=[c['request']['method'] for c in calls],call_count=len(calls),
        accepted_approaches=a['accepted_approach_calls'],rejected_approaches=a['rejected_approach_calls'],
        incomplete_approaches=a['incomplete_approach_calls'],native_step_limit_cancelled=a['native_step_limit_cancelled'],
        completed_primitive_action_steps=a['trusted_primitive_action_steps'],
        next_call_after_first_lift=calls[8]['request'] if len(calls)>8 else None,
        physical_grasp='unknown_without_video_or_independent_physical_measurement')
    actors[key]=(row,calls)
    eligible=len(calls)>=8 and [c['request']['method'] for c in calls[:8]]==expected and all(c['state']=='completed' and 'value' in c.get('response',{}) and not c['response']['value'].get('primitive_error') for c in calls[:8])
    row['prefix_replay_eligible']=eligible
    if not eligible:
        skipped.append(dict(condition=a['condition'],layout_id=a['mapped_layout_id'],reason='Did not complete identical eight-method pre-guard structure'));continue
    for variant,code in sources.items():
        result=replay(code,calls[:8],str(R/'candidates'/variant/'candidate.py'))
        result.update(observation_condition=a['condition'],layout_id=a['mapped_layout_id'],counterfactual_candidate=variant,source_record_sha256=sha(p))
        rel=f"replays/{a['condition']}_layout_{a['mapped_layout_id']}_as_{variant}.json"
        save(out/rel,result)
        replays.append(dict(observation_condition=a['condition'],layout_id=a['mapped_layout_id'],candidate=variant,state=result['state'],next_call=result['next_call'],path=rel))
pairs=[]
for layout in range(5):
    rows={n:next(e for e in d['episodes'] if e['condition']==n and e['layout_id']==layout) for n in sources}
    pair=dict(layout_id=layout,original_score_100=100*rows['original']['normalized_score'],bypass_score_100=100*rows['bypass_lift_guard']['normalized_score'],
              original_success=rows['original']['success'],bypass_success=rows['bypass_lift_guard']['success'],
              score_difference_100=100*(rows['bypass_lift_guard']['normalized_score']-rows['original']['normalized_score']))
    if all((n,layout) in actors for n in sources):
        ar,ac=actors[('original',layout)];br,bc=actors[('bypass_lift_guard',layout)]
        pair['diagnostics']={'original':ar,'bypass_lift_guard':br}
        first=lambda calls:next((x['request']['kwargs'] for x in calls if x['request']['method']=='approach'),None)
        pa,pb=first(ac),first(bc)
        pair['first_targets_equal']=equal(pa,pb)
        pair['first_target_position_distance_m']=math.dist(pa['position_m'],pb['position_m']) if pa and pb else None
        pair['first_target_arm_equal']=pa['arm']==pb['arm'] if pa and pb else None
        obs=lambda calls:next((x['response']['value'].get('objects') for x in calls if x['request']['method']=='scene' and 'response' in x),None)
        pair['initial_scene_objects_exactly_equal']=obs(ac)==obs(bc)
        pair['pre_guard_request_prefix_equal']=len(ac)>=8 and len(bc)>=8 and all(equal({k:x['request'][k] for k in ['method','args','kwargs']},{k:y['request'][k] for k in ['method','args','kwargs']}) for x,y in zip(ac[:8],bc[:8]))
    pairs.append(pair)
summary=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),native_cases=10,new_cpu_replays=len(replays),
    native_cases_reused_for_replay=len(replays)//2,new_api_calls=0,lab_gpu_used=False,
    cohorts=d['cohorts'],paired_outcomes=pairs,actor_diagnostics=[x[0] for x in actors.values()],counterfactual_replays=replays,skipped_replay_inputs=skipped,
    interpretation_limits=['Native outcomes are measured; replay next-call requests are not physical outcomes.',
       'Physical grasp remains unknown unless supported by separately reviewed video or an independent physical observer.',
       'One diagnostic guard bypass, no generated-policy promotion; same five historical layouts.',
       'Use paired initial scene/target comparisons to assess runtime variation; do not assume identical observations.'])
save(out/'summary.json',summary)
table=['condition | full success | mean Score /100 | completed approach | incomplete approach']
for c in d['cohorts']:table.append(f"{c['condition']} | {c['successes']}/{c['cases']} | {c['mean_normalized_score']*100:.2f} | {c['accepted_approach_calls']} | {c['incomplete_approach_calls']}")
lines=['System 2 lift-guard 原生对照与配对分析','',
       '本批为人工机制消融：原始 augmented_3 与仅将抬升 return guard 旁路的版本。候选其他代码、评分与1100步预算保持原样。',
       '该实验不等同于自动自改进成功，也没有替换 pi05。此前提出的只移除Z条件，在离线回放中0/5改变停止分支，故原生方案改为整项检查消融；方案在新原生执行前固定。','']+table
lines+=['','逐布局原生评分（0–100）：']
for p in pairs:lines.append(f"layout {p['layout_id']}: original={p['original_score_100']:g}; bypass={p['bypass_score_100']:g}; difference={p['score_difference_100']:g}; same pre-guard request prefix={p.get('pre_guard_request_prefix_equal','unknown')}")
lines+=['',f"使用本批新观测另做 {len(replays)} 次CPU候选前缀回放；只回放已完成的8次调用，到下一条未观测动作请求即截断。没有增加机器人样本数。",'真实抓取是否成立需结合视频或独立状态证据；仅有approach完成、夹爪闭合、正常return或后续调用均不是抓取成功证明。',
        'actor_diagnostics与paired_outcomes记录了下一调用、规划拒绝、步数终止、目标差异和初始观测差异。完整日志和30段原始视频在native-validation/native-campaign/runs。',
        '这5个布局是历史诊断布局，尚未验证独立泛化。动作预算未扩大，所有分数沿用原生评分。','',
        '进一步方向：依据本批实际新停止点确定单变量实验；若继续执行仍无抓取证据，应先检查接触/夹持/抬升契约，而非将旁路条件当成正式修复。']
(out/'REPORT.txt').write_text('\n'.join(lines)+'\n')
print(json.dumps(dict(state='complete',new_cpu_replays=len(replays),paired_scores=[{k:p[k] for k in ['layout_id','original_score_100','bypass_score_100']} for p in pairs],cohorts=d['cohorts']),ensure_ascii=False))
