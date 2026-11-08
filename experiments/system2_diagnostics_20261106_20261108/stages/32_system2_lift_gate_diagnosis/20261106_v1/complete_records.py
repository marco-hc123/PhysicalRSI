"""Complete derived documentation; never alters native archives or runtime code."""
import datetime
import hashlib
import json
from pathlib import Path

L = Path('/mnt/data/joey_tr/physical-RSI/result/32_system2_lift_gate_diagnosis/20261106_v1')
I = Path('/mnt/data/joey_tr/physical-RSI/result/16_system2_integration/25_system2_integration_20261030T050100Z/integration-sources')
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p, data): p.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')

summary = read(L/'FINAL_SUMMARY.json')
resources = read(L/'completion-resource-check.json')
assert summary['accounting']['new_native_cases'] == 20
assert all(not resources[k]['owned_experiment_processes'] for k in ['lab','execution_server'])

frame_index = read(L/'video-review/retreat-frame-index.json')
reviewed = [x for x in frame_index if x['layout'] == 4]
assert len(reviewed) == 2
for x in reviewed: assert sha(Path(x['image'])) == x['image_sha256']
save(L/'video-review/retreat-qualitative-review.json', dict(
    state='visually_reviewed', recorded_utc=now,
    task='classify_objects', layout=4, source_index='retreat-frame-index.json',
    reviewed_frames=reviewed,
    observations=[
        'The control final frame shows the left gripper over the white basket; other objects remain on the table.',
        'The return_to_clearance final frame shows a different left arm/gripper configuration, still near/over the white basket in the head view; remaining table objects are visible.',
        'Both recorded native scores are15/100 and full success isfalse. Images do not override these outcomes.',
    ],
    interpretation='Visible arm configuration differs consistently with a changed action, but these final frames alone cannot prove completion of retreat, precise displacement, stable grasp or correct placement. The actual pending-call and step-limit cancellation records establish that the new retreat was incomplete.',
    limitations=['Two final head-camera frames, not a metric pose/contact reconstruction.',
                 'Encoded frame1100 at25fps means44s in the video, not measured wall-clock time or a calibrated physical duration.']))

sources=[]
for relative, terms in [
    ('native-simulator/env_cfg/arx_x5.yml', ['sim_config']),
    ('native-simulator/env_cfg/sim/sim_config.yml', ['decimation','dt:','render_interval']),
    ('native-simulator/env/environment/base_env.py', ['self.sim_cfg.decimation','self.sim_cfg.sim.dt','self.sim_cfg.sim.render_interval']),
    ('native-simulator/env/environment/isaac/direct_rl_env.py', ['def sim_step','range(self.cfg.decimation)','self.sim.step']),
    ('step4_native_primitives_v3.py', ['dt=.004']),
]:
    p=I/relative
    lines=p.read_text().splitlines()
    excerpts=[dict(line=i+1,text=t) for i,t in enumerate(lines) if any(w in t for w in terms)]
    assert excerpts
    sources.append(dict(path=str(p),sha256=sha(p),excerpts=excerpts))
save(L/'contract-audit/timestep-sanity.json',dict(
    state='static_configuration_check_completed',recorded_utc=now,sources=sources,
    simulator_dt_seconds=.004, simulator_decimation=1, native_planner_dt_seconds=.004,
    conclusion='No timestep mismatch is apparent in these frozen configuration and adapter sources. This does not establish full dynamic correctness or explain all large trajectory lengths.',
    limits=['Read-only source check, zero new simulation or solver calls.',
            'No claim that encoded video time equals physical or wall-clock time.',
            'Episode warmup/reset/substeps and actual runtime overrides were not independently reconstructed here; do not derive total physical duration from this check.']))

history=L/'status-history';history.mkdir(exist_ok=True)
for path, name in [(L/'status.json','main-before-completion.json'),
                   (L/'retreat-followup/status.json','followup-before-completion.json')]:
    dest=history/name
    assert not dest.exists()
    dest.write_bytes(path.read_bytes())

save(L/'status.json',dict(
    state='completed',stage='completed_and_verified_on_lab',updated_utc=now,
    active_pid=None,active_experiment_processes=[],pending=[],
    accounting=summary['accounting'],main_report=str(L/'REPORT.txt'),
    main_summary=str(L/'FINAL_SUMMARY.json'),native_archives=[x['destination'] for x in summary['archives']],
    lab_gpu_active=False,execution_gpu_active=False,
    resource_receipt='completion-resource-check.json',
    next_action='Preserve completed studies. Next research: explicit capability feedback and budget-aware action tests under a separately frozen protocol; existing proposal remains unexecuted.',
    retained_policy='pi05',new_policy_promotions=0))
save(L/'retreat-followup/status.json',dict(
    state='completed',updated_utc=now,native_cases=10,raw_videos=30,
    native_archive='native-validation',archive_verified=True,
    control_scores_100=[0,0,0,0,15],treatment_scores_100=[0,0,0,0,15],
    full_successes_control=0,full_successes_treatment=0,
    treatment_budget_cancelled_layouts=[1,3,4],active_pid=None,pending=[],api_calls=0,
    analysis='comparison-analysis.json',note='The changed retreat was not completed; no score improvement or autonomous System2 promotion.'))

(L/'README.txt').write_text('''本阶段已完成：请从 REPORT.txt 与 FINAL_SUMMARY.json 阅读最终结论。

20 个新增原生回合 = 两轮各 2 条件 × 5 个已有布局；完整成功均为 0。
60 段原始视频、回执、日志和候选已校验归档。
summary.json 与 OFFLINE_REPORT.txt 是较早的25次CPU回放报告，不能作为最终总账。
retreat-followup/comparison-analysis.json 是第二轮逐布局与停止原因对比。
completion-resource-check.json 是完成时的进程/GPU核查；EVIDENCE_INDEX.json 为最终证据索引。
状态更新前的记录保留在 status-history/；CONTINUATION.txt 可用于继续研究，勿重复运行本轮矩阵。
所有改动是手工机制诊断，不是新的System2自动生成/策略提升。未来实验草案尚未执行。
''')
report=L/'REPORT.txt'
with report.open('a') as f:
    f.write('''
完成后核查补记
两批全部原生证据已逐文件SHA256校验回传；共15591个归档文件、60段视频。完成核查时，两台执行相关服务器均无本项目活动计算进程，GPU查询无计算进程。本轮未付费调用API；实例未被自动关闭。
已目视核对第二轮layout4的两张末帧：两组夹爪均仍位于白篮筐附近/上方，手臂构型不同，其余物品仍在桌面。末帧不证明撤离完成，动作日志中的未完成调用和预算取消才是停止原因依据。来源与限制见video-review/retreat-qualitative-review.json。
冻结仿真配置dt=0.004、decimation=1；本部署规划适配层dt也为0.004。静态配置层面未见两者时间步长不匹配，不能据此宣称动态行为全部正确或把视频时长当成物理时长；源文件哈希与摘录见contract-audit/timestep-sanity.json。
''')
print(json.dumps(dict(state='completion_records_written',main_report=str(report),native_cases=20,videos=60)))
