"""Write the campaign report only after all frozen native phases validate."""
import collections
import datetime
import json
from pathlib import Path

O = Path(__file__).resolve().parent
read = lambda p: json.loads(p.read_text())
s = read(O / 'FINAL_SUMMARY.json')
assert s['state'] == 'completed'
phases = s['completed_native_phases']
matrices = {p: read(O / p / 'analysis/matrix-analysis.json') for p in phases}
replays = {p: read(O / p / 'analysis/source-stop-replay-v2.json') for p in phases}
diagnostics = {p: read(O / p / 'analysis/mechanism-diagnostics.json') for p in phases}
selection = s['search_selection']
lines = []
def add(*items): lines.extend(str(x) for x in items)
def scores(phase, condition):
    rows = sorted([r for r in matrices[phase]['episodes'] if r['condition'] == condition], key=lambda r:r['layout_id'])
    return [round(r['normalized_score'] * 100, 4) for r in rows]
def cohort_table(phase):
    add('策略 | 实际原生回合 | 完整成功 | 各布局 Score /100 | 平均 Score /100')
    for c in matrices[phase]['cohorts']:
        add(f"{c['condition']} | {c['cases']} | {c['successes']}/{c['cases']} | {scores(phase,c['condition'])} | {c['mean_normalized_score']*100:.2f}")
def mechanism_table(phase):
    add('以下为首次物体操作的事后物理诊断代理量，不能代替原生任务评分。')
    for c in matrices[phase]['cohorts']:
        rows=[x for x in diagnostics[phase]['cases'] if x['condition']==c['condition']]
        known=[x for x in rows if x.get('source_association',{}).get('qualified')]
        counts=collections.Counter(x.get('physical_diagnosis','unknown') for x in rows)
        add(f"{c['condition']}: n={len(rows)}, 物体关联可判定={len(known)}, lift_proxy={sum(bool(x.get('lift_proxy')) for x in rows)}, 首次释放={sum(bool(x.get('release_observed')) for x in rows)}, 首物体最终稳定送达代理={sum(bool(x.get('selected_object_delivered_proxy')) for x in rows)}, 诊断={dict(counts)}")
    r=replays[phase]
    add(f"精确记录回放可定位退出位置：{r['qualified_return_locations']}/{len(r['cases'])}。这只是 CPU 上按已有回复重放代码，不新增机器人回合。")
    for name in [x['condition'] for x in matrices[phase]['cohorts']]:
        q=[x for x in r['cases'] if x['condition']==name]
        grouped=collections.Counter((x.get('terminal'),x.get('policy_exit_line'),x.get('qualified_return_location',False)) for x in q)
        add(f"  {name}: (回放终态, 代码行号, 定位资格) -> {dict(grouped)}")

add('PhysicalRSI System 2：候选补样本、执行修正与独立布局验证',
    '生成时间 UTC: '+datetime.datetime.now(datetime.timezone.utc).isoformat(),
    '本报告只总结 20261107_v1 新批次；旧路线一只作为已核验研究起点。', '',
    '一、研究问题与最终状态',
    '问题 A：在同样反馈、模型、执行器与开发布局下，多给候选生成机会是否获得收益？',
    '问题 B：候选共同失败是否受到某个具体执行目标规则的限制？',
    '问题 C：加入已验证反馈后，下一轮搜索是否改进；开发期选出的策略能否迁移到未参与修改的新布局？',
    f"已完成 {s['actual_native_episodes']} 个实际原生评分回合，保留 {s['original_videos']} 个原始相机视频；另有 5 次零策略动作的布局初始化资格检查。",
    f"完成 {s['paid_api_requests']} 次付费候选生成，预估新增费用 ${s['estimated_new_api_usd']:.6f}；本批预算上限 $10，最终账单以提供方为准。",
    f"第一轮 1 候选预算选择={selection['round1_selection']['budget1']['selected']}；5 候选预算选择={selection['round1_selection']['budget5']['selected']}；第二轮选择={selection['round2_selection']['selected']}。",
    '本批 fixed_parent 是已有 code candidate，不是 pi05。未训练权重、未修改全局策略注册表。实验室未占用 GPU。', '',
    '二、先明确几个不等价的结果',
    '动作接口返回成功 ≠ 物体被抓稳 ≠ 物体送达并稳定留在目标篮筐 ≠ 原生分类整任务成功。',
    '原生得分按任务的阶段条件累计。15/100 是达到一个评分阶段，不是完成 15% 的物体，也不是完整成功。完整成功标记还包含任务完成/回位要求。',
    '候选程序正常 return 只说明程序结束；它可以因规划失败主动退出。仿真仍可保持至 1100 步，不代表候选一直在执行有效动作。',
    'first-object delivery / lift 均为事后诊断代理，依赖物体关联和几何规则；未知关联保持未知。它们不证明真实抓持接触力，也不提供给策略作为隐藏状态。', '',
    '三、冻结范围、资源与版本',
    '任务 classify_objects，ARX X5，RoboDojo 原生 RGB 仿真。开发期沿用已暴露的 5 个布局；所有候选在同一冻结执行条件下比较。',
    '候选可使用 scene / approach / gripper / reobserve 等既定公共接口；不能读取仿真真实物体位姿来控制。scene 的 nominal Z 不等于真实动态高度。',
    '每回合原生上限 1100 步；隔离程序机器人 RPC 上限 100 次，隔离超时 1500 秒，单 primitive 截止 180 秒。RPC 次数、原生动作步数和付费 API 次数分开计数。',
    '模型 gpt-6.1-sol / reasoning high，max_completion_tokens=16000；第一轮 5 次完全同请求，第二轮 3 次完全同更新请求。保留所有候选，不以重新生成替换表现差的候选。',
    '模拟器环境 Python 3.11.17、Isaac Sim 5.1.0.0、Torch 2.7.0+cu128、NumPy 1.26.0、Warp 1.11.0；policy 环境 Torch 2.7.1、NumPy 1.26.4、Warp 1.17.0。',
    '完整版本、硬件和源文件身份见 route1-freeze/environment-current.json、各 phase 的 runtime/binding/harness、source-closure/path-map.json。环境未升级，具体执行文件以 SHA256 为准。',
    '初次父策略准备曾因 assembler 导入路径出现一次部署失败（0 个原生回合），证据保存在 deployment-attempts/parent-prepare01；修正启动绑定后才开始评分。该准备失败不计为策略 0 分。',
    '初次生成提示词遗漏 100 RPC 限制，原请求没有事后改写。第一轮 25 个候选回合均未触及此限制；第二轮反馈明确补入。见 budget-contract-addendum.json。', '',
    '四、路线一作为研究起点（旧证据，不重复累计）',
    '旧路线一共有 10 个原生回合、30 个视频，已单独核验归档。当前单周期候选 5 回合中 2 次稳定送达；发布技能首篮筐周期 5 次送达，其中 3 次正常完成、2 次异常清理张爪后送达。两者都没有整任务完整成功。',
    '两组的目标物体、接口能力和执行流程并不完全一致，因此不能按 2/5 与 5/5 直接判断策略优劣。只说明系统存在局部搬运能力，但尚不稳定。',
    '本批继续使用完整六周期固定父代码；路线一单周期诊断与本批父策略不能混成同一组。旧数据仅引用，新增回合数为 0。',
    '证据：route1-source-lock.json、route1-result-reference.json、route1-freeze/，以及实验室 result/41_system2_skill_chain_floor/20261107_v1。', '',
    '五、第一轮：固定条件，增加候选生成机会')
cohort_table('parent');cohort_table('sampling')
add('第一轮每次输入均为 3,010 Token，共生成 5 份不同代码；5/5 通过语法和准入，全部进行了 5 布局原生评价。',
    '5 个候选的得分全部为 0，初始父策略平均为 3/100，因此 1 候选预算和 5 候选预算都保留 fixed_parent。这个小样本未观察到“多生成几次即可获益”，不等于更多样本永远无效。',
    '不能将此结果解释为对最早 Qwen 两轮候选数量的严格补测：现在的模型、推理设置与执行契约不同。',
    '精确代码/初始 memory 绑定的记录回放 25/25 通过：4 个候选先出现抬升代理、再因运输目标规划拒绝主动 return；sample_03 在接近阶段的有界尝试全部被拒绝，未实际进入抓取。',
    '本批失败回复已经到达候选代码，程序也执行了相应分支；当前证据不支持把这些失败归因于反馈丢失、程序崩溃或 100 RPC 用尽。',
    '5 份候选理由都倾向于去掉历史目标偏移并改用篮筐中心/内部点。但尚未做单独的反馈措辞对照，不能断言某一句反馈造成失败。')
mechanism_table('sampling')
add('', '六、路线二：固定同一候选，只改变运输目标 XY 规则',
    '根据第一轮共同的 no_collision_free_path，选择 sample_01 作为对照对象。在两组中都使用同一份带开关的代码，只切换 memory 中 experiment_target_rule。',
    'control=生成方案原目标；offset=父策略历史 XY 偏移。修改发生在选臂之后；不同时改高度、姿态、夹爪、步数、模型或执行器。原始生成代码另行保留。',
    '外侧篮筐使用 bx-0.0175、by-0.035；中间篮筐按已选机械臂使用 bx±0.065、by-0.055。这是一个整体 XY 规则因素，未分别识别 X 与 Y 的作用。',
    '两组源代码 SHA 相同；仅一个 memory 键不同。实测首次选臂 5/5 一致，初始目标的最大几何波动约 0.000143m。仍有物理随机性且按 control-first 顺序运行。')
cohort_table('repair');mechanism_table('repair')
add('开发布局上，首次释放从 0/5 到 3/5，首个物体最终稳定送达代理从 0/5 到 2/5，得分有 1 对提高 15 分、4 对持平，平均提高 3 分。',
    '该修正只恢复到初始父策略的平均 3/100，并未超过初始父策略；两组完整成功都是 0/5。',
    '所有回合最终仍在运输失败分支退出：有的卡在第一物体，有的第一物体完成后卡在后续物体。一次局部送达并不消除整任务后续障碍。',
    '这是人工设计的执行目标修正，不是 System 2 自动发现的收益；后续只把实测证据作为下一轮反馈。见 manual-target-control/design-final.json 与 repair/analysis/target-control-comparison.json。', '',
    '七、第二轮：加入完整执行证据后，再生成与验证',
    '执行器保持原版，父策略仍为 fixed_parent。一次性冻结新的反馈包，生成 3 个候选：包含父代码与 memory、精确停止位置、第一轮全部结果、代表调用序列、人工 XY 对照的源码/差分/结果，以及明确的 RPC 限额。',
    '3 份请求内容完全相同（63,083 bytes），没有加入独立验收布局或原始隐藏物体位姿；候选完成后不能手工改写再作为生成结果评分。',
    '3 份生成方案均提出先以空夹爪实际接近候选放置点，再执行抓取；同时采用类别优先、显式张爪、有限次数的源位置回退等逻辑。round2_02 额外强调目的篮筐侧机械臂选择。以上是生成代码的意图，实际执行程度须以调用记录为准。',
    '注意：这种放置点预检是实际 approach 动作，会消耗原生步数，不是免费规划查询；空夹爪可达也不保证闭合夹爪或持物路径可达。这些生成方案同时改变多个高层决策，不是单因素对照。',
    '这一轮同时增加了搜索机会、更新了反馈并加入人工修正证据，不能从前后差异中单独识别“候选数”“轮数”“反馈质量”的因果效应。也不能称为没有人工帮助的自主发现。')
cohort_table('round2');mechanism_table('round2')
add('按完整成功数优先、平均原生分数其次的规则选择；与父策略持平则保留父策略。第二轮实际选择：'+selection['round2_selection']['selected']+'。', '',
    '八、冻结选择后，独立新布局验收',
    '先写入 selection-final.json，再生成并资格检查 5 个新布局，核对已有文件/物理布局签名。没有在测试结果上挑选候选或继续调参。',
    '新布局从冻结的公共任务生成器分布采样，物体/类别组合可以变化；这不是只移动坐标的对照，也不是专门控制的新类别泛化实验。',
    f"共有 {s['heldout_logical_strategy_views']} 个逻辑策略视图，但相同 source+memory+executor 去重后仅执行 {s['heldout_unique_strategies']} 个唯一策略。复用的视图不增加原生回合数。",
    '因为开发期人工目标修正出现正向得分对，在看任何独立布局结果之前，额外冻结了其匹配 control 与 offset 两组。这样可以分别判断人工修正在新布局上的迁移。')
cohort_table('heldout');mechanism_table('heldout')
add('逻辑视图与实际执行证据映射：')
for x in s['heldout_strategies']:
    add(f"{x['label']} -> {x['evaluated_as']}；Score={x['heldout_scores_100']}；成功={x['heldout_successes']}/{x['heldout_cases']}。")
if s['heldout_manual_target_pairs']:
    ds=[x['score_delta_100'] for x in s['heldout_manual_target_pairs']]
    add(f"独立布局人工 XY 对照逐对差值={ds}；均值={sum(ds)/len(ds):.2f} 分；正向/持平/负向对数={sum(x>0 for x in ds)}/{sum(x==0 for x in ds)}/{sum(x<0 for x in ds)}。")
add('', '九、Token、计时与阶段账目',
    'Token 为本批生成请求的提供方 usage。cached input 与 cache-write 都是输入内部项目，reasoning 是输出子集，不能再次加到 total 中。原生执行没有付费高层 LLM 调用。')
for x in s['api_usage']:
    add(f"{x['batch']}: {x['requests']} requests, input={x['prompt_tokens']}, output={x['completion_tokens']}, total={x['total_tokens']}, cached_input_subset={x['cached_input_subset']}, cache_write_input_subset={x['cache_write_input_subset']}, reasoning_output_subset={x['reasoning_output_subset']}, estimated_USD={x['estimated_usd']:.6f}。")
add('逐请求耗时和原始 usage 在 ledger.json；运行阶段耗时在 all-cohorts.csv。每个 cohort wall 包含启动/执行/等待，不能当作纯机械臂运动时间；1100 原生步也不等于 1100 次有效运动。',
    '检查发现实验室时钟比本机约慢 99.224 秒、执行服务器约慢 1.208 秒（测量时点和 RTT 不确定性见 clock-comparison.json）。未修改系统时钟。不能相减不同机器的 UTC 字段计算延迟；本批 API/native 时长使用各进程单调时钟。',
    '阶段实际回合数：'+str({p:matrices[p]['qualified_cases'] for p in phases})+'。',
    '旧路线一引用、精确记录回放、API-only 生成、准入检查、5 次零策略动作布局初始化均没有重复累计为新评分回合。', '',
    '十、目前能支持与不能支持的结论',
    '1. 单纯增加第一轮候选数量，在当前这一池候选与 5 个开发布局上没有带来超过父策略的得分收益。',
    '2. 可以将一批失败定位到候选中的明确分支：规划拒绝被正确送达并导致主动退出。不是笼统的“System 2 没运行”。',
    '3. 在同一候选上改变一个目标 XY 规则，能够改变部分执行链与局部得分。因此至少某些损失与候选目标规则有关，不应一概归为底层完全没有搬运能力。',
    '4. 不能把人工 XY 修正、更多搜索机会及更新反馈混为同一个因果因素；正式的第二轮与独立验收数值以上表和原始记录为准。',
    '5. 不能据此证明整个上游 PhysicalRSI 有固定缺陷，也不能用本批替代官方 RoboDojo 全任务评分。受限公共接口、候选代码、布局分布、物理随机性和执行预算都影响结果。',
    '6. 本批不是两项目 Token 比值或速度倍数的实验；早期公开参照与本批 System 2 生成成本不能直接相除。',
    '7. 小样本、单一候选池、相关布局对照，仍不足以给出总体成功率或统计显著改善结论。独立布局不用于再选择。', '',
    '十一、下一轮建议：依据本批停止点预注册，不继续测试集调参',
    '若仍以运输规划拒绝为主：固定一个候选/执行器，比较原目标规则与“抓取前联合验证接近和运输”的单因素策略；保持模型、输入、类别、动作预算和评分不变。验收先看规划通过且真正执行的比例，再看物体稳定送达、原生 Score 与完整成功。',
    '若路径可执行但途中丢失：固定目标与候选，单独验证抓持保持或轨迹衔接；不能同时调 XY、高度、抓取姿态和等待。验收记录抬升/共动/丢失时刻，并以稳定入筐及原生分数确认效果。',
    '若第二轮仅在开发布局更好：冻结当前结果，把新问题反馈限制在下一轮开发集；另外预留新的测试布局。禁止用本批 heldout 挑选更好的候选后重新命名为独立收益。',
    '要分别估计“更多样本”与“更好反馈”：下一轮使用固定执行契约和相同总候选预算，成对比较反馈包，并做多个独立候选池；同样的开发选择规则后再测试。',
    '以上是后续建议，不是本批已经完成的额外实验。', '',
    '十二、证据索引与复核入口',
    'protocol.json / route1-source-lock.json / execution-final.json / selection-final.json：协议和版本冻结。',
    'requests/ / candidates/ / ledger.json：完整请求、响应、候选与成本；不含密钥。',
    'parent、sampling、repair、round2、heldout：每阶段 native-campaign、runtime、harness、sim-diagnostics、原生 receipt/result、三视角视频。',
    '各阶段 analysis/matrix-analysis.json、independent-validation.json：原始评分一致性、源文件身份和视频完整解码。',
    '各阶段 analysis/source-stop-replay-v2.json、mechanism-diagnostics.json：精确退出分支与事后物理诊断。',
    'all-episodes.csv、all-cohorts.csv、stage-accounting.csv、api-usage.csv、heldout-strategy-views.csv：可重算的表格数据。',
    'reference-path-map.json、source-closure/path-map.json、migration/source-manifest.json：依赖证据闭包与 SHA256 清单。大权重/安装环境不重复打包。',
    '迁移完成后实验室 archive-analysis/ 会从归档原始评分和 receipt 再次重算；迁移校验文件是实际归档完成的依据，报告生成本身不等于迁移已完成。')
report=O/'REPORT.txt';assert not report.exists();report.write_text('\n'.join(lines)+'\n')
reproduce='''PhysicalRSI search/execution-control campaign reproduction notes

This directory is an immutable evidence snapshot, not an instruction to rerun paid experiments.
Never overwrite native-campaign output or regenerate a poor candidate in place.

Read protocol.json, budget-contract-addendum.json, execution-final.json,
selection-final.json and heldout-matched-control-addendum.json first.
Resolve original absolute source/evidence paths using source-closure/path-map.json
and reference-path-map.json. Large installed dependencies are pinned references.
The archive does not include virtualenvs or all pretrained weights; preserve the
recorded environment/package/source identities when rebuilding on another host.

Chronology:
1. Freeze the previously verified route1 record; no new route1 episodes.
2. Evaluate a fresh five-layout full-code parent control.
3. Generate five identical-request GPT high candidates; preserve all outcomes.
4. Evaluate admitted candidates on the same five development layouts.
5. Exact CPU replay of recorded candidate-visible replies locates exits.
6. Freeze and evaluate matched targetXY control: same code, one memory flag.
7. Freeze baseline execution and updated feedback; generate three new candidates.
8. Evaluate all three, select using full successes then mean score; retain ties.
9. Freeze strategies before creating five previously unexposed qualified layouts.
10. Evaluate unique source+memory+executor strategies once each on those layouts.
11. Validate native receipt/result equality, sources, videos and recorded replays.
12. Summarize, seal per-file SHA256 manifest, relay through laptop, verify archive,
    then independently recalculate scores on lab CPU.

Read-only/CPU recomputation on the archived lab directory:
  python3 -B analyze_archived.py
This writes archive-analysis inside this project only. It uses no GPU or API.

Actual campaign launcher sources are run_phase.py, prepare_phase.py and templates/.
They are evidence for reconstruction, not portable one-command invocations: original
runtime binds paths and hashes. A new native replication requires a NEW result root,
matching pinned environments/assets, explicit budget accounting, a verified idle
allowed GPU, a new protocol freeze, and fresh credentials supplied outside logs.

Do not rerun the generation worker against this completed ledger; there were eight
authorized paid requests and no automatic retries. Credential input was memory-only.

Budget-1 and budget-5 strategy views may reuse the fixed parent's heldout evidence.
Source-reply replay and five layout resets are not new scored task episodes.
Manual repair is not a generated System2 candidate. Do not tune on heldout outcomes.
'''
(O/'REPRODUCE.txt').write_text(reproduce)
print(json.dumps(dict(state='report_written',report_bytes=report.stat().st_size)))
