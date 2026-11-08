import datetime,json
from pathlib import Path
L=Path('/mnt/data/joey_tr/physical-RSI/result/32_system2_lift_gate_diagnosis/20261106_v1')
def read(p):return json.loads(p.read_text())
for sub,title in [('planning-recovery','失败目标高度对照'),('planning-return','放置后撤离目标对照')]:
    O=L/sub;s=read(O/'summary.json');p=read(O/'protocol.json');r=read(O/'runtime.json')
    assert read(O/'status.json')['state']=='completed'
    lines=[title,'',
        '输入来自本批原生失败调用的实际起始关节状态和目标位姿；没有用成功状态替换失败状态。',
        '每次只在已冻结的规划器、几何和碰撞场景下改变协议指定的目标变量。使用三个随机种子检查重复性；种子不算三个独立布局。没有训练、付费API、RGB渲染或新增机器人回合。',
        f"共{s['solver_calls']}次求解。环境记录见runtime.json，配置仅做路径迁移，原始YAML及规划代码SHA保存。",'']
    for g in s['groups']:
        condition=str(g.get('goal_variant',g.get('delta_z_m')))
        lines.append(f"layout {g['layout']} / {g['phase']} / {condition}: 返回有限轨迹{g['returned_trajectory']}/{g['calls']}，状态{g['statuses']}")
    if sub=='planning-recovery':lines += ['',
        '原目标15次均未返回轨迹。下降4cm只让layout0搬运目标可行；下降8cm让layout0及三个撤离目标可行，layout2仍不可行。说明高度对部分失败有影响，但不是全部失败的共同解释。未把下降8cm直接部署为正式撤离：向下移动虽然可规划，却不等于完成安全撤离。']
    else:lines += ['',
        '三个放置后撤离状态，原垂直上抬目标0/9可行，返回此前已到达的抬升位置9/9可行。因此后续原生实验只更改这一撤离目标，保留原评分和1100步预算，并重新执行同批布局的对照组。该干预依然位于人工旁路抬升检查的诊断策略上，不是有效抓取验证器。']
    lines += ['',
        '局限：规划器使用冻结的机器人/桌面碰撞模型，非完整动态物体碰撞。Fail不是不可达的数学证明；Success只表示给定模型下返回轨迹。实际执行、步数、物体接触及得分必须另看原生仿真。求解顺序和常驻规划器可能影响随机性，不能把重复种子看成独立成功率估计。',
        '配置与环境：实验室只使用一张启动前确认空闲的GPU，写入限制在本实验目录。完成后gpu-after.json记录无计算进程。无需修改系统环境。',
        '完整证据：protocol.json、runtime.json、results.json、summary.json、probes/、trajectories/、worker.log、write-isolation.json和GPU采样。']
    (O/'REPORT.txt').write_text('\n'.join(lines)+'\n')
# A protocol draft, not a claim that a new generation experiment ran.
draft=dict(schema='physicalrsi.next-feedback-experiment-draft/v1',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),state='prepared_not_executed',
    question='Does explicitly exposing verified capabilities and failure-stage information reduce unsupported candidate assumptions and improve native execution?',
    treatment='Historical augmented feedback versus the same feedback plus verified feedback-contract-v2 and current failure-stage table',
    fixed=['Same base prompt, candidate history, model gpt-6.1-sol, reasoning setting, token limit and paired generation settings','Same five diagnostic layouts for development; same runtime, original scoring and1100-step budget for the first controlled comparison'],
    generation_plan='Three candidates per condition, log every request/response, API usage, errors and candidate hash; do not regenerate only failures.',
    offline_gates=['Contract: do not infer lift from nominal Z or object absence alone','Runtime: reject invalid imports/unbounded actions using existing admissions','Error handling: distinguish zero-execution planner rejection from partial-action errors','Account for unavailable remaining-step observations; do not pretend backend-only data is public'],
    native_metrics=['Actual evaluation score and full success','First violated contract or stop stage','Number of actions completed before stop','Planner reject/exception/step-budget breakdown','Generation Tokens separate from execution/API-only costs'],
    independent_validation='Only after a fixed repair passes development, freeze selection and evaluate new layouts without further tuning. Report all layouts and failures.',
    budget='No paid calls made now. Any later generation batch must enforce the user-authorized total cap before launching.',
    limitations=['Contract/lint pass is not robot success.','Do not attribute improvement solely to added text length; a size-matched irrelevant-feedback control can be a separate later ablation.','Manual mechanism fixes and auto-generated candidates must remain separate cohorts.'])
(L/'contract-audit/next-generation-protocol-draft.json').write_text(json.dumps(draft,ensure_ascii=False,indent=2)+'\n')
review=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),reviewed_images=['new_original_layout4_head_frame1100.png','new_bypass_lift_guard_layout4_head_frame1100.png'],
    observations=['Original final head frame shows watch near closed left gripper and visible unsorted items on table.','Bypass final head frame shows opened gripper above left white basket; a dark watch-like object is visible within it, with other items still on table.'],
    interpretation='Visual evidence is consistent with the measured partial score15/100 in bypass layout4, not full sorting success. The official score is taken from native results, not inferred from the image.',
    limits=['Encoded final frame; not metric pose/contact measurement.','No claim that every visible object was tracked or correctly classified.'])
(L/'video-review/new-qualitative-review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
print('Planning reports, draft future generation protocol, and native-frame review saved.')
