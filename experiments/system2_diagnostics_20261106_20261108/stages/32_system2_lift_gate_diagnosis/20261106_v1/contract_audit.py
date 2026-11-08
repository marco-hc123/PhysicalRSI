"""Evidence-based API capability audit and draft feedback; never changes runtime."""
import collections,datetime,hashlib,json
from pathlib import Path
R=Path('/mnt/data/joey_tr/physical-RSI')
L=R/'result/32_system2_lift_gate_diagnosis/20261106_v1';N=L/'native-validation';O=L/'contract-audit'
O.mkdir(exist_ok=True)
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,d):(O/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
d=read(N/'analysis/matrix-analysis.json');zs=collections.defaultdict(list);errors=[];scene_calls=0;projected_action_calls=0;projected_action_steps=0
for a in d['actors']:
    proc=read(N/a['process_record'])
    for call in proc['calls']:
        method=call['request']['method'];value=call.get('response',{}).get('value',{})
        if method=='scene':
            scene_calls+=1
            for name,obj in value['objects'].items():zs[name.rsplit('_',1)[0]].append(obj['pose'][2])
        if method in ['approach','gripper']:
            projected_action_calls+=1;projected_action_steps+=int('action_steps' in value)
        if 'primitive_error' in value:
            errors.append(dict(condition=a['condition'],layout=a['mapped_layout_id'],call_id=call['request']['id'],error=value['primitive_error'],projected_keys=list(value),record=a['process_record']))
internal=[]
for p in (N/'analysis/referenced-primitive-services').rglob('*.json'):
    x=read(p);res=x.get('result',{})
    if isinstance(res,dict) and res.get('primitive_error'):
        internal.append(dict(path=str(p.relative_to(N)),error=res['primitive_error'],action_steps=res.get('action_steps')))
request=R/'result/29_system2_feedback_api/20261104_v1/requests/augmented_3.json'
req=read(request);text='\n'.join(m['content'] for m in req['messages'])
runtime=read(N/'analysis/frozen-runtime.json')
caps=dict(schema='physicalrsi.feedback-capabilities-draft/v2',status='draft_not_applied_to_active_runtime',
    scene=dict(coordinates='World-frame metre estimates derived from calibrated head RGB rays intersected with category-specific nominal planes.',z_is_measured_dynamic_height=False,
        z_rule='0.765 + nominal category HEIGHT / 2, not the current vertical position of a lifted object.',persistent_instance_tracking=False,
        absence='No returned object is not proof of failed grasp: detector, crop, proposal filtering, CLIP semantics, or occlusion can remove a physically present object.',
        forbidden_inference='Do not use scene Z increase, unchanged instance suffix, or disappearance alone as a grasp-success test.'),
    approach=dict(current_failure_mode='This deployed compatibility adapter returns primitive_error=no_collision_free_path plus observed state when planning rejects BEFORE any trajectory execution. Other exceptions remain exceptions.',
        documented_legacy_mode=runtime['skill_api']['methods']['approach'],
        current_success='Observed joints after bounded trajectory execution; not a grasp, pose-accuracy, or task-success assertion.',
        projected_action_steps_available=False,
        recovery='A zero-execution planning rejection can be considered separately from uncertain partial physical execution. A recovery policy still requires frozen limits and native validation; no unlimited retry.'),
    gripper=dict(current_output='Observed joint state after six setpoint steps',grasp_success_observable=False),
    budget=dict(native_steps=1100,max_waypoints_per_approach=500,gripper_setpoint_steps=6,public_remaining_steps_available=False,
        proposed_interface_change_not_implemented='Consider exposing executed primitive steps and remaining task budget with explicit semantics; test zero-action rejection versus partial cancellation.'),
    provenance=dict(source_request=str(request),request_sha256=sha(request),native_protocol_sha256=sha(L/'protocol/native-protocol.json')))
save('feedback-contract-v2.json',caps)
summary=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),native_cases_reused=10,new_native_cases=0,new_api_calls=0,
    scene_calls=scene_calls,returned_object_samples=sum(map(len,zs.values())),nominal_height_by_category={k:dict(samples=len(v),min_z=min(v),max_z=max(v),unique_z=sorted(set(v))) for k,v in zs.items()},
    planner_rejection_calls=errors,internal_rejections=internal,projected_action_calls=projected_action_calls,projected_responses_exposing_action_steps=projected_action_steps,
    source_request_sha256=sha(request),old_approach_description=runtime['skill_api']['methods']['approach'],
    request_term_checks={k:k.lower() in text.lower() for k in ['height','nominal','fixed height','plane','no_collision_free_path','not persistent tracking identities']},
    inference_limits=['Term checks alone are not a semantic proof; conclusions also use exact API description, frozen Reader implementation and measured scene outputs.','No claim that this compatibility assembly is unmodified upstream PhysicalRSI.','No live prompt/runtime changes or new generated candidates.'])
save('summary.json',summary)
results=read(L/'planning-return/results.json');pred=[]
for layout in [1,3,4]:
    actor=next(a for a in d['actors'] if a['condition']=='bypass_lift_guard' and a['mapped_layout_id']==layout)
    lengths=[r['trajectory_shape'][0] for r in results if r['layout']==layout and r['goal_variant']=='previous_clearance']
    total=actor['trusted_primitive_action_steps']+min(lengths)
    pred.append(dict(layout=layout,historical_completed_primitive_steps=actor['trusted_primitive_action_steps'],return_trajectory_waypoints=lengths,min_required_steps=total,budget=1100,exceeds_budget=total>1100,
        prediction='Planning may accept the new retreat but unchanged native budget may terminate before it completes.',scope='Historical state-based prediction, not the new native result; within-host counts, not timestamps.'))
save('followup-budget-prediction.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),before_treatment_cohort_result=True,predictions=pred))
lines=['接口能力与候选假设审计','',
 '范围：只读取冻结的实际请求、候选、Reader、兼容执行层及本批10个原生回合。未改线上接口或System2提示词。',
 f'本批{scene_calls}次scene返回、{sum(map(len,zs.values()))}个对象记录中，同一类别的Z均保持类别平面高度。该统计与Reader固定高度投影代码一致；它不是抬升动态测量。',
 '候选要求抬升后Z增加2.5cm，与当前接口提供的信息不相容。历史生成请求的scene描述只说明RGB世界坐标估计，没有明确告知Z为类别固定高度。不能简单归结为“用户步骤出错”或“官方System2算法错误”；当前有证据的是生成候选对接口能力的假设与部署的感知能力不一致，且反馈契约说明不够明确。',
 '另发现描述一致性问题：旧提示词称无路径时抛RuntimeError，当前兼容层则把纯规划拒绝转成primitive_error字典。候选move()实际处理了该字典，因此该描述差异不是本批提前退出的直接原因；仍应修正后续说明。',
 f'公开动作响应{projected_action_calls}次，暴露action_steps的响应{projected_action_steps}次。内部完整日志有步数，但候选当前不能从公开响应直接得到这些计数。因此不应把后台可见剩余预算当作候选已经拥有的能力。',
 '规划器只使用冻结的机器人/桌面模型，没有完整动态物体碰撞模型。可规划不等于抓稳、接触安全、完成放置或任务成功。',
 '', '下一批建议提供的结构化能力说明已写入feedback-contract-v2.json：明确名义Z、非持久实例编号、漏检不等于抓取失败、规划拒绝零执行与部分执行异常的区别，以及当前预算可见性。该文件只是建议反馈材料，尚未做付费生成对照或接入正式System2。',
 '', '原生撤离对照的事前预算预测：']
for p in pred:lines.append(f"layout{p['layout']}：已执行{p['historical_completed_primitive_steps']}步，加离线撤离轨迹至少{min(p['return_trajectory_waypoints'])}步，总计至少{p['min_required_steps']}，超过1100。若原生中复现此顺序，可能由规划失败转为预算终止；不能据此预先写成实测结果。")
lines+=['','所有判断均针对本研究冻结的实现、适配与候选。未证明完整官方论文系统或所有任务均存在同一问题。']
(O/'REPORT.txt').write_text('\n'.join(lines)+'\n')
print(json.dumps(dict(scene_calls=scene_calls,object_samples=sum(map(len,zs.values())),projected_actions=projected_action_calls,action_step_fields=projected_action_steps,internal_rejections=len(internal),budget_predictions=pred)))
