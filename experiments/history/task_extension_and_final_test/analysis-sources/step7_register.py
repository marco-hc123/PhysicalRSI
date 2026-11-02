"""Register limited completion; immutable source reuse and cloud-only evidence."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil,subprocess,sys
R=Path('/mnt/data/physical-RSI'); OLD=R/'result/24_steps23_20261030T013742Z_v3'
O=R/'result'/('34_limited_completion_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip()
O.mkdir(); S=O/'analysis-sources';S.mkdir()
for name in ['cloud_comparison_run.py','cloud_comparison_policy.py','cloud_comparison_native.py']:
 shutil.copy2(OLD/'analysis-sources'/name,S/name)
for p in Path(__file__).parent.glob('step7_*.py'):shutil.copy2(p,S/p.name)
# Explicit credential owner: controllers run as root, API credential stays with ecs-user.
for name in ['cloud_comparison_run.py','cloud_comparison_policy.py']:
 p=S/name;s=p.read_text();s=s.replace("Path.home()/'.config/physicalrsi/agent.json'","Path('/home/ecs-user/.config/physicalrsi/agent.json')");p.write_text(s)
# Existing verified measurement wrappers; task limit remains the native task's own value.
p=S/'cloud_comparison_run.py';s=p.read_text();s=s.replace("label='steps23-'", "label='limited-completion-'");p.write_text(s)
tasks=['stack_bowls','cover_blocks','insert_tubes']
jobs=[]
for stage,layouts in [('smoke',[0]),('formal',list(range(1,6)))]:
 for task in tasks:jobs.append(dict(name=stage+'_'+task,stage=stage,task=task,layouts=layouts,route='agent',condition=stage,ground_truth=False))
old=json.loads((OLD/'protocol.json').read_text())
freeze=R/'result/23_protocol_freeze_20261029T132917Z'
protocol=dict(schema='physicalrsi.limited-completion/v1',registered_utc=datetime.now(timezone.utc).isoformat(),
 authorization='User authorizes all limited new-task checks, smoke, formal evaluation, independent final test, comparison/export/reproduction closure.',
 jobs=jobs,source_hashes=old['source_hashes'],freeze=str(freeze),
 tasks=tasks,native_step_limits=dict(stack_bowls=800,cover_blocks=800,insert_tubes=500),
 agent_max_calls_per_episode=1,http_attempts_per_logical_call=3,
 official_defaults_preserved=True,episode_scope='Limited representative evaluation, not full leaderboard counts.',
 cohorts=dict(smoke=[0],formal=[1,2,3,4,5],source='Pinned official RoboDojo evaluation layouts; unused by this study; no claim of absence from model training.'),
 original_final_test=json.loads((freeze/'data-splits.json').read_text())['final_test'],
 failure_policy='Preserve task failures; stop and diagnose infrastructure errors. Version code/interface repairs separately and retain original outputs. No final-test tuning.',
 raw_retention='cloud_only',exclusions=['full leaderboard','new System2 iterations','project A reproduction','automatic ECS stop'])
write(O/'protocol.json',protocol)
write(O/'analysis-status.json',dict(complete=True,prior_evidence='Reuse audited O20/O21/O24/O31/O32; no rerun'))
write(O/'procedure-registration.json',{p.name:sha(p) for p in S.glob('*.py')})
planpath=R/'result/CURRENT_REPRODUCTION_PLAN.json';plan=json.loads(planpath.read_text());write(O/'previous-master-plan.json',plan)
plan.update(updated_utc=datetime.now(timezone.utc).isoformat(),current_step=7,next_step=7,active_directory=str(O),active_protocol=str(O/'protocol.json'),active_controller_pid=None,active_tmux_session=None,current_controller_running=False,next_action='Hydrate and validate resources, then three development smoke episodes')
plan['authorized_steps']=sorted(set(plan.get('authorized_steps',[])+[7,8]));plan['pending_completion_plan']['state']='authorized_execution'
write(planpath,plan);write(R/'result/CURRENT_STEP7.json',dict(directory=str(O),stage='registered',complete=False))
print(str(O))
