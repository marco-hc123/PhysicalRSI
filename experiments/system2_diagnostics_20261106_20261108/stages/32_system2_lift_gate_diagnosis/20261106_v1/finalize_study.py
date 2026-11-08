"""Publish a comprehensive lab report after both native archives are verified."""
import collections,datetime,hashlib,json
from pathlib import Path
R=Path('/mnt/data/joey_tr/physical-RSI')
L=R/'result/32_system2_lift_gate_diagnosis/20261106_v1';F=L/'retreat-followup'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
archives=[];datasets=[]
for root,name in [(L,'lift_guard'),(F,'retreat_destination')]:
    N=root/'native-validation';v=read(N/'migration/ARCHIVE_VERIFIED.json');assert v['state']=='verified'
    d=read(N/'analysis/matrix-analysis.json');assert d['complete'] and d['qualified_cases']==10
    assert read(N/'analysis/independent-validation.json')['state']=='passed'
    datasets.append((name,N,d));archives.append(v)
old=datasets[0][2];new=datasets[1][2];N=datasets[1][1]
rows=[];details=[];replication=[]
for batch,root,d in datasets:
    for c in d['cohorts']:
        rows.append(dict(batch=batch,condition=c['condition'],cases=c['cases'],successes=c['successes'],mean_score_100=100*c['mean_normalized_score'],
            scores_by_layout_100=[100*next(e['normalized_score'] for e in d['episodes'] if e['condition']==c['condition'] and e['layout_id']==i) for i in range(5)],
            wall_seconds=c['cohort_wall_seconds'],accepted_approaches=c['accepted_approach_calls'],incomplete_approaches=c['incomplete_approach_calls'],
            step_limit_cancellations=c['native_step_limit_cancellations'],source=str(root/'analysis/matrix-analysis.json')))
for a in new['actors']:
    p=N/a['process_record'];calls=read(p)['calls']
    row=dict(condition=a['condition'],layout=a['mapped_layout_id'],mapping_qualified=a['mapping_qualified'],rpc_calls=a['rpc_calls'],
        rejected_approaches=a['rejected_approach_calls'],accepted_approaches=a['accepted_approach_calls'],incomplete_approaches=a['incomplete_approach_calls'],
        native_step_limit_cancelled=a['native_step_limit_cancelled'],completed_primitive_steps=a['trusted_primitive_action_steps'],first_error=a['first_error'],
        call10=calls[10] if len(calls)>10 else None,call11=calls[11] if len(calls)>11 else None,record=str(p),sha256=sha(p))
    if a['condition']=='return_to_clearance' and len(calls)>10:
        row['retreat_target_equals_prior_clearance']=calls[10]['request']['kwargs']==calls[6]['request']['kwargs']
    details.append(row)
for layout in range(5):
    def outcome(d,condition):return next(e for e in d['episodes'] if e['condition']==condition and e['layout_id']==layout)
    a=outcome(old,'bypass_lift_guard');b=outcome(new,'bypass_lift_guard');t=outcome(new,'return_to_clearance')
    replication.append(dict(layout=layout,earlier_bypass_score_100=100*a['normalized_score'],fresh_bypass_score_100=100*b['normalized_score'],return_score_100=100*t['normalized_score'],
        fresh_difference_100=100*(t['normalized_score']-b['normalized_score']),earlier_vs_repeat_difference_100=100*(b['normalized_score']-a['normalized_score']),
        fresh_bypass_success=b['success'],return_success=t['success']))
prediction=read(L/'contract-audit/followup-budget-prediction.json')
checks=[]
for p in prediction['predictions']:
    a=next(a for a in details if a['condition']=='return_to_clearance' and a['layout']==p['layout'])
    checks.append(dict(layout=p['layout'],predicted_min_steps=p['min_required_steps'],actual_step_limit_cancellation=a['native_step_limit_cancelled'],
        actual_incomplete_approaches=a['incomplete_approaches'],actual_retreat_call=a['call10'],next_call_exists=a['call11'] is not None,
        interpretation='Use native receipts and pending-call evidence together; task reaching1100 alone does not establish actor budget exhaustion.'))
accounting=dict(new_native_cases=20,new_native_cohorts=4,unique_exposed_layouts=5,new_raw_videos=60,
    historical_35_native_cases_reused_for_context=35,historical_cases_not_counted_as_new=True,
    cpu_recorded_prefix_replays=45,solver_probes=63,saved_trajectories_static_checks=24,perception_reader_calls=4,additional_full_frame_detector_probes=2,
    new_paid_api_calls=0,new_paid_api_cost_usd=0,new_generated_candidates=0,training_steps=0,policy_promotions=0,
    note='Do not add offline replays, model inference probes, historical reuse or video count to robot sample count.')
summary=dict(state='completed',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),accounting=accounting,cohorts=rows,
    followup_per_layout=replication,followup_actor_details=details,prediction_checks=checks,archives=archives,
    scope='Manual sequential mechanism diagnostics on a frozen deployment and exposed layouts; not full benchmark or autonomous System2 improvement.')
save(L/'FINAL_SUMMARY.json',summary);save(F/'comparison-analysis.json',dict(rows=rows[2:],replication=replication,actors=details,prediction_checks=checks))
lines=['PhysicalRSI System 2失败定位与逐项修正实验报告','',
 '研究目标与本阶段定位',
 '本阶段沿“日志定位→离线证伪/验收→单项原生对照→检查新停止点”的顺序推进。目标是区分候选假设、接口能力、规划可行性和执行预算，不是把所有失败笼统归为System2失效。',
 '本轮没有重新调用System2生成候选，没有训练或选择新策略。两个改动由人工诊断得到；pi05仍为此前保留的策略。本阶段结论不能写成“System2已自动取得改进”。',
 '', '一、冻结条件与证据链',
 '起点为此前增强反馈生成的augmented_3候选，SHA c083d296b7708688356311749727ce410c8a0d09d2380f1722a94cea2bccd4db。保留原来的classify_objects任务、ARX X5、五个已暴露诊断布局、原生评分及1100步预算。',
 '环境、资产、代码和技能的版本身份通过冻结runtime/harness/layout SHA验证。所有原生组都有独立回执、原始_result.json、动作/RPC记录和三相机视频；第二轮也重新执行对照组。详细身份在各protocol/native-protocol.json与native-validation/analysis/frozen-runtime.json。',
 '主要研究在实验室项目目录；RGB工作通过本机SSH中转后执行，再校验归档回该目录。原始证据保留真实运行元数据；没有改实验室项目目录以外的环境。主机时钟有偏差，使用同一主机的单调计时，不跨主机相减时间戳。',
 '', '二、先定位为何抬升后提前return：25次历史前缀回放',
 '每个版本使用同一真实历史观测与已完成动作响应，严格核对调用参数；遇到第一条未观测的新动作就截断，不编造动作后的结果。',
 '五个版本各5次：原始、只去Z、只去XY、同时去XY/Z、旁路整项return检查。能请求下一动作的输入数分别为0、0、0、1、5。',
 '因此“只去掉高度条件即可恢复执行”的预测被否定。布局2和4抬升后没有同类别目标；布局0/1/3最近同类目标XY差距约11.50/9.50/9.75cm，均超出6cm阈值。即使去掉XY和Z，exact-one数量检查也会拦截多数输入。',
 '当前Reader的Z来自类别固定平面，不能测动态抬升。这个真实接口限制是重要问题，但不是历史五个输入中唯一阻塞条件。完整回放在replays/、inputs/及OFFLINE_REPORT.txt。',
 '', '三、原生检查整体抬升guard是否阻止后续执行',
 '仅把抬升后的return条件旁路；其余动作、感知、规划、布局、评分与预算不变。原始5个全部0分；旁路后5个都请求了后续动作，layout4取得15/100，其余0分，完整成功仍0/5。',
 '原始与旁路并非逐像素相同观测，首个目标位置相差约0.035–0.097mm；已记录配对差异。单个布局的一次部分分数不能证明统计显著提升或泛化。另20次新观测CPU回放仅用于分支核查，不增加机器人样本。',
 '旁路使错误继续暴露：layout0/2在搬运至篮筐时规划失败；layout1/3/4到篮筐、张开夹爪后，在垂直撤离到Z1.07时规划失败。五次均有no_collision_free_path，并按候选异常处理结束；这不是HTTP故障或模型没有返回。',
 '15分属于原生评分的部分阶段，不能改写为完整成功。视频可见layout4原始策略停在手表仍靠近夹爪的位置，旁路策略在白篮筐上方张开夹爪，其他物品仍在桌面。',
 '', '四、感知链诊断：关闭robot-overlap过滤是否足够',
 '真实录像解码的初始与抬升后两帧分别做原始过滤/关闭该过滤，共4次Reader推理；另有2次整图DINO探针。成对输入、原始检测输出及mask前提案保持一致。',
 '初始图两条件均返回1个watch；抬升后两条件均返回0个watch。关闭这一项过滤没有恢复手表。阶段记录区分了检测、跨类别IoU去重、robot mask、CLIP类别融合及最终过滤；不能把漏检直接归因于某一层。',
 '这里是有损录像解码、近似帧/关节状态对齐的单布局诊断，不是原传感器逐像素复现，不是原生任务回合。perception-replay/保存全部阶段提案和结果。',
 '', '五、规划目标诊断：45次高度探针与18次撤离探针',
 '使用五个真实失败调用的起始关节状态、目标XY/姿态/手臂，仅改变目标Z，分别原值、降低4cm、降低8cm，每条件3种子，共45次。原目标全部失败；降4cm只修复layout0搬运目标；降8cm还使三个撤离目标可规划，layout2仍失败。',
 '这些结果表明目标高度影响一部分失败，但不能统一解释全部失败。没有直接把“向下移动8cm”部署为正式撤离，因为可规划不等于安全或有用的物理行为。',
 '再针对三个撤离状态，比较原垂直上抬与返回此前已到达的抬升位置，各3种子，共18次：原目标0/9可规划，返回原抬升位置9/9可规划。离线规划只使用冻结机器人/桌面模型，不含完整动态物体碰撞，因此必须继续原生验收。',
 '', '六、第二轮原生对照：只改变放置后的撤离目标',
 '两组都保留上一轮诊断用抬升guard旁路。对照仍在篮筐XY上垂直撤离至1.07m；处理组仅把这条动作改为回到刚才物体XY处的clearance_z。重新运行5+5个布局，未增加步数、修改分数或重新生成候选。','']
lines += ['批次 | 条件 | 成功 | 平均Score/100 | 布局0..4分数']
for r in rows:lines.append(f"{r['batch']} | {r['condition']} | {r['successes']}/{r['cases']} | {r['mean_score_100']:.2f} | {r['scores_by_layout_100']}")
lines += ['', '第二轮动作与停止原因：']
for a in sorted(details,key=lambda x:(x['condition'],x['layout'])):
    lines.append(f"{a['condition']}/layout{a['layout']}：RPC{a['rpc_calls']}，完成approach{a['accepted_approaches']}，规划拒绝{a['rejected_approaches']}，未完成approach{a['incomplete_approaches']}，执行中被原生预算取消={a['native_step_limit_cancelled']}，首错误={a['first_error']}。")
lines += ['', '事前预算预测与实测核对：']
for c in checks:lines.append(f"layout{c['layout']}：历史动作+离线撤离轨迹预测至少{c['predicted_min_steps']}步，实际执行中预算取消={c['actual_step_limit_cancellation']}，未完成approach={c['actual_incomplete_approaches']}，撤离之后新调用存在={c['next_call_exists']}。")
lines += [
 '注意：所有原生回合都到1100步，并不意味着候选都因预算终止。已return的候选会保持当前位置直至评估终止；只有候选仍在动作中且被取消，才归入执行预算问题。完整区分见comparison-analysis.json。',
 '', '七、原因归属：现有证据能说什么',
 '1. 候选层：用名义Z验证动态抬升；失败后catch-all return；固定撤离目标在本批状态下不可规划。这些是当前具体生成候选的假设/设计问题。',
 '2. 接口与适配层：当前感知本来就是桌面物体的RGB平面估计，不保证抓持物体的3D跟踪。旧提示词没有明确写出固定高度能力边界，且无路径“抛异常”的描述与兼容层实际错误字典不一致。候选处理了错误字典，所以后者不是本批直接根因。',
 '3. 预算层：动作轨迹逐点执行，单次移动可能数百步。公开响应没有action_steps字段（本批61个动作响应均未暴露），虽然后台日志可见。生成器不能被假定已经获得实时剩余预算。',
 '4. 归因边界：这是冻结部署、兼容适配和具体候选的实测；不是对全部官方PhysicalRSI、所有System2机制或完整RoboDojo榜单的否定。暂未证明独立布局上的提升，也未完成自动候选生成—验证—提升闭环的新成功案例。',
 '', '八、下一轮可执行路线',
 '先完成接口契约：给System2明确名义Z、实例编号非持久、漏检不等于抓取失败、纯规划拒绝零执行与部分执行异常的区别。草案在contract-audit/feedback-contract-v2.json，尚未应用到当前冻结运行。',
 '对预算问题先确定研究变量：可以在原预算下改动作序列/轨迹效率，也可以另做单独预算扩展诊断；扩展预算必须单独标记，不能与原基准得分混为一谈。不要同时换模型、改感知、改动作和放宽评分。',
 '随后做同一模型、相同生成设置下的原反馈/明确能力契约反馈对照，记录所有生成、拒绝和失败，不只挑好候选。候选经过离线与原生验证后，再冻结选择并在独立新布局验收。方案已保存为next-generation-protocol-draft.json，尚未进行付费调用。',
 '', '九、样本与费用账目',json.dumps(accounting,ensure_ascii=False,indent=2),
 '上述20个新原生回合属于4组、同5个暴露布局。此前35个原生回合只作历史来源，不再次累计。离线回放、求解、感知与视频均不算独立机器人样本。',
 '没有本轮语言模型调用，因此不能从本轮得出Token节省百分比；本轮贡献是明确后续改进需要的反馈信息、动作契约和失败层次。',
 '', '十、文件索引',
 'FINAL_SUMMARY.json：完整机器可读总表与账目；REPORT.txt：本报告。',
 'OFFLINE_REPORT.txt、replays/、inputs/：历史候选25次前缀回放。',
 'native-validation/：第一轮10例、30视频、全部原始回执和日志，migration/ARCHIVE_VERIFIED.json验证归档。',
 'post-native-analysis/：第一轮配对分析及20次新观测前缀回放。',
 'perception-replay/：逐阶段感知诊断、输入帧引用与单GPU释放记录。',
 'planning-recovery/、planning-return/：63次规划探针、轨迹、配置、日志及报告。',
 'retreat-followup/native-validation/：第二轮10例、30视频；comparison-analysis.json为配对及预测核对。',
 'contract-audit/：接口假设审计、事前预算预测、反馈说明和后续生成对照草案。',
 'video-review/：真实关键帧、文件SHA、录像来源、编码帧号和已阅说明。',
 'CONTINUATION.txt：接续说明；最终活动进程及资源状态在后续完成核查记录中。',
 '', '解释限制',
 '部分得分≠完整成功；发出动作≠完成动作；规划可行≠真实抓取；手工修正≠System2自动改进；同布局重跑≠独立泛化；原始名义Z≠动态高度。保留这些界限，才能把下一轮改进结果解释清楚。']
(L/'REPORT.txt').write_text('\n'.join(lines)+'\n')
print(json.dumps(dict(state='completed',cohorts=rows,accounting=accounting,prediction_checks=[{k:v for k,v in c.items() if k!='actual_retreat_call'} for c in checks]),ensure_ascii=False))
