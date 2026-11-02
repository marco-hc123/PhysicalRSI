"""Register and stage the authorized native diagnostics and System 1 reference run.

Run on the existing server only. Does not launch GPU work or call a model.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path('/mnt/data/physical-RSI')
FREEZE = ROOT/'result/23_protocol_freeze_20261029T132917Z'
OUT = Path(sys.argv[1])
OUT.mkdir(exist_ok=False)
SRC = OUT/'analysis-sources'
SRC.mkdir()
NOW = datetime.now(timezone.utc).isoformat()

def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

frozen = json.loads((FREEZE/'source-freeze.json').read_text())
for path, expected in frozen['recorded_protocol_and_framework_hashes'].items():
    assert sha(Path(path)) == expected, path
for row in frozen['deployment_files']:
    assert sha(Path(row['path'])) == row['sha256'], row['path']

jobs = [dict(name='diagnostic_classify', step=2, task='classify_objects',
             layouts=[2, 4], route='code', condition='diagnostic', ground_truth=True, retained=True),
        dict(name='diagnostic_classify_missing', step=2, task='classify_objects',
             layouts=[1], route='code', condition='diagnostic', ground_truth=True),
        dict(name='diagnostic_language', step=2, task='classify_objects_by_language',
             layouts=[0, 3], route='code', condition='diagnostic', ground_truth=True)]
for task in ['classify_objects', 'classify_objects_by_language']:
    for route in ['pi05', 'pi05-sparse-memory', 'code', 'agent']:
        jobs.append(dict(name='reference_'+task+'_'+route, step=3, task=task,
                         layouts=list(range(5, 10)), route=route,
                         condition='reference', ground_truth=False))
protocol = dict(schema='physicalrsi.steps23/v3', registered_utc=NOW,
    supersedes='/mnt/data/physical-RSI/result/24_steps23_20261030T012400Z_v2',
    amendment='Keep two verified v2 fixed-route diagnostic episodes; run only missing layout1, then remaining registered jobs. Unique native run IDs prevent importing earlier resume results. Initial v1 route fault costs remain separate.',
    freeze=str(FREEZE), freeze_protocol_sha256=sha(FREEZE/'protocol.json'),
    source_hashes=frozen['recorded_protocol_and_framework_hashes'], jobs=jobs,
    authorization='User explicitly requests completing steps 2 and 3 on the cloud, 2026-10-30.',
    step2=dict(episodes=5, design='Three category-sort controls and two language-sort diagnostics on previously seen development layouts.',
        route='Fixed official released code capability, isolating execution from Agent selection.',
        truth='Simulator-side pose and pure native containment/settlement/home predicates; output only, never policy inputs.',
        timing='Diagnostics include observation overhead and are not pooled with original speed measurements.',
        caveat='Fresh diagnostic executions, not a replay of saved physical states or a controlled repair.'),
    step3=dict(episodes=40, layouts_per_task=5, repetitions=1,
        routes=['pi05', 'pi05-sparse-memory', 'code', 'agent'],
        layout_manifest=str(FREEZE/'data-splits.json'),
        design='All four routes on the same ten preregistered System 1 reference scenes; no tuning or retry-until-success.',
        interpretation='Fixed-route zero planner usage is not zero VLA inference/development cost; sparse-vs-base differs in weights and architecture as well as memory.',
        memory='Verify immutable snapshot references, episode binding/reset and real sparse-history append/materialize/reset. No memory-off ablation or improvement claim.'),
    accounting=dict(step_limit=1100, control_dt_seconds=0.04, seed=0,
        model='qwen3.7-plus', temperature=0, enable_thinking=True,
        maximum_http_attempts_per_logical_call=3,
        failure_policy='Keep normal planner and native failures; halt on incomplete infrastructure evidence.',
        cold_definition='One fresh top-level process per task/route group, then five ordered resets; record total group time separately.',
        scope='Model requests only on Agent reference route, at most 10 logical calls and 30 HTTP attempts.',
        purposes=['infrastructure_diagnostics', 'frozen_skill_execution']),
    exclusions=['System 2', 'project A execution', 'all-task leaderboard', 'raw-output migration'],
    raw_retention='cloud_only')
write(OUT/'protocol.json', protocol)
write(OUT/'preparation-status.json', dict(complete=False, stage='registered'))
write(OUT/'analysis-status.json', dict(complete=True, scope='Prior completed failure audit S22 and protocol freeze S23 reused'))

policy = (ROOT/'result/20_cross_project_evidence_20261029T075456Z/analysis-sources/cloud_comparison_policy_v2.py').read_text()
assert 'row.update(values)' in policy, 'Require the corrected v2 event recorder'
policy = policy.replace("parser.add_argument('--port'", "parser.add_argument('--route', choices=['pi05','pi05-sparse-memory','code','agent'], required=True)\nparser.add_argument('--port'", 1)
policy = policy.replace("if status['api_attempts'] >= 12:", "if status['api_attempts'] >= int(os.environ['PHYSICALRSI_MAX_HTTP']):")
policy = policy.replace('def measured_urlopen(request, timeout=120, **kwargs):',
    "def measured_urlopen(request, timeout=120, **kwargs):\n    assert args.route == 'agent', 'Fixed route must never call a planner API'")
fixed = '''
if args.route != 'agent':
    class FixedRoutePlanner:
        def __init__(self, **kwargs): pass
        def plan(self, **kwargs):
            if args.route == 'code':
                operation = {'classify_objects': 'visual-attribute-placement',
                             'classify_objects_by_language': 'language-conditioned-placement'}[args.task]
                return dict(composition='memory-guided-program-library', operations=[operation],
                            rationale='Preregistered fixed released capability control; no API choice.')
            composition = {'pi05': 'memory-guided-manipulation',
                           'pi05-sparse-memory': 'memory-guided-visual-history'}[args.route]
            return dict(composition=composition, operations=[], rationale='Preregistered fixed checkpoint control; no API choice.')
    planner_module.AgentPlanner = FixedRoutePlanner
    skill_module.AgentPlanner = FixedRoutePlanner

assert skill_module.AgentPlanner is planner_module.AgentPlanner
'''
policy = policy.replace('original_plan = planner_module.AgentPlanner.plan', fixed+'\noriginal_plan = planner_module.AgentPlanner.plan')
policy = policy.replace("status['logical_calls'] += 1", "status['logical_calls'] += int(args.route == 'agent')")
policy = policy.replace("number, tick = status['logical_calls'], time.monotonic()", "number, tick = status['episode_index']+1, time.monotonic()")
policy = policy.replace("event('logical_plan_start', logical_call=number)", "event('logical_plan_start' if args.route == 'agent' else 'fixed_route_start', logical_call=number)")
policy = policy.replace("event('logical_plan_end',", "event('logical_plan_end' if args.route == 'agent' else 'fixed_route_end',")
memory_instrumentation = (Path(__file__).parent/'steps23_memory_instrumentation.py').read_text()
policy = policy.replace('from XPolicyLab.policy.physicalRSI.model import Model', memory_instrumentation+'\nfrom XPolicyLab.policy.physicalRSI.model import Model')
policy = policy.replace("event('first_observation', instruction=row['instruction'])", "event('first_observation', instruction=row['instruction'], immutable_memory_revision=runtime.memory.revision)")
policy = policy.replace("event('runtime_reset_start')", "event('runtime_reset_start', sessions=list(runtime.sessions), queue_sizes={str(k):len(v) for k,v in runtime.action_queues.items()}, immutable_memory_revision=runtime.memory.revision)")
policy = policy.replace("event('runtime_reset_end')", "event('runtime_reset_end', sessions=list(runtime.sessions), queue_sizes={str(k):len(v) for k,v in runtime.action_queues.items()}, immutable_memory_revision=runtime.memory.revision)")
policy = policy.replace('    instrument(runtime)',
    "    assert type(runtime.planner) is planner_module.AgentPlanner\n    event('planner_binding_verified', route=args.route, planner_class=type(runtime.planner).__name__)\n    instrument(runtime)")
(SRC/'cloud_comparison_policy.py').write_text(policy)

native = (ROOT/'result/20_cross_project_evidence_20261029T075456Z/analysis-sources/cloud_comparison_native.py').read_text()
gt = (Path(__file__).parent/'steps23_ground_truth.py').read_text()
native = native.replace('def instrument(env):', gt+'\n\ndef instrument(env):')
native = native.replace('    self.st_idx, self.ed_idx, self.idx = 0, len(self.seed_list), 0',
    "    assert self.seed_list == selected, 'Unexpected prior resume filtering; refuse partial scene coverage'\n    self.st_idx, self.ed_idx, self.idx = 0, len(self.seed_list), 0")
native = native.replace("event('reset_ready', control_dt=env.dt*env.obs_manager.collect_interval)", "event('reset_ready', control_dt=env.dt*env.obs_manager.collect_interval)\n            ground_truth(env, 'reset')")
native = native.replace("result = take(actions_list, env_idx_list)", "result = take(actions_list, env_idx_list)\n            if env.take_action_cnt[0] % 10 == 0 or any(env.end_flag): ground_truth(env, 'control')")
native = native.replace("result = run_eval()", "result = run_eval()\n            ground_truth(env, 'terminal')")
(SRC/'cloud_comparison_native.py').write_text(native)

runner = (ROOT/'result/20_cross_project_evidence_20261029T075456Z/analysis-sources/cloud_comparison_run.py').read_text()
runner = runner.replace("PHYSICALRSI_SKILL_CONFIG=str(OUT/'skills.json')", "PHYSICALRSI_LOG_GT='1' if job['ground_truth'] else '0', PHYSICALRSI_MAX_HTTP=str(3*len(job['layouts'])), PHYSICALRSI_SKILL_CONFIG=str(OUT/'skills.json')")
runner = runner.replace("'--output',str(OUT),'--task',job['task'],'--port','6012'", "'--output',str(OUT),'--task',job['task'],'--route',job['route'],'--port','6012'")
runner = runner.replace("label='cross-project-'+job['condition']", "label='steps23-'+job['condition']+'-'+job['route']")
runner = runner.replace('server=client=None', "server=client=None\nnative_run_id=SUITE.name+'--'+OUT.name")
runner = runner.replace('ROBODOJO_RUN_ID=OUT.name', 'ROBODOJO_RUN_ID=native_run_id')
runner = runner.replace('{OUT.name}', '{native_run_id}')
runner = runner.replace("    assert any(e['kind']=='control_ack' for e in events), 'No native control instrumentation observed'", "    assert all(e['kind'] == 'episode_error' for e in terminal) or any(e['kind']=='control_ack' for e in events), 'No native control instrumentation observed'")
runner = runner.replace("    if native:\n", "    if native:\n        assert len(results)==1\n")
runner = runner.replace("    save('complete',complete=True,", "    if job['ground_truth']:\n        truth=[json.loads(l) for l in (OUT/'ground-truth.jsonl').read_text().splitlines()]\n        assert not any('error' in r for r in truth), 'Ground truth observer failed'\n        assert len([r for r in truth if r['phase']=='terminal']) == len(job['layouts'])\n    save('complete',complete=True,")
route_checks = '''    policy_events=[json.loads(l) for l in (OUT/'policy-events.jsonl').read_text().splitlines()]
    assert any(e['kind']=='planner_binding_verified' and e['route']==job['route'] for e in policy_events)
    if job['route']!='agent':
        assert not list((OUT/'api').glob('*metadata.json')), 'Unexpected fixed-route HTTP cost'
        plans=[e['plan'] for e in policy_events if e['kind']=='fixed_route_end']
        assert len(plans)==len(job['layouts']), 'Fixed routes must execute each registered plan'
        composition={'pi05':'memory-guided-manipulation','pi05-sparse-memory':'memory-guided-visual-history','code':'memory-guided-program-library'}[job['route']]
        assert all(p['composition']==composition for p in plans)
'''
runner = runner.replace("    save('complete',complete=True,", route_checks+"    save('complete',complete=True,")
(SRC/'cloud_comparison_run.py').write_text(runner)
for name in ['steps23_finalize.py']:
    shutil.copy2(Path(__file__).parent/name, SRC/name)
shutil.copy2(Path(__file__).parent/'steps23_controller_v3.py', SRC/'steps23_controller.py')
shutil.copy2(Path(__file__), SRC/Path(__file__).name)
for name in ['steps23_ground_truth.py','steps23_memory_instrumentation.py','steps23_assets.py']:
    shutil.copy2(Path(__file__).parent/name, SRC/name)
for p in SRC.glob('*.py'):
    compile(p.read_text(), str(p), 'exec')
write(OUT/'registration.json', dict(registered_utc=NOW, source_files={p.name:sha(p) for p in SRC.glob('*.py')},
    new_api_calls=0, new_native_episodes=0, deployed_baseline_changed=False))
print(str(OUT))
