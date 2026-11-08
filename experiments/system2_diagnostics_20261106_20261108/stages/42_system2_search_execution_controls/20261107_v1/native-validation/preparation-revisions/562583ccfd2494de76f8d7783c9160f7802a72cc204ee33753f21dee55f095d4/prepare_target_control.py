"""Prepare, but do not run, a manual single-factor target-rule control."""
import ast,copy,datetime,difflib,hashlib,json,subprocess,sys
from pathlib import Path
O=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
source=(O/'candidates/sample_01/candidate.py').read_text()
proposal=read(O/'candidates/sample_01/proposal.json');assert proposal['source']==source
marker='            grip(arm, 1)\n            if not move(arm, [x, y, contact]):'
assert source.count(marker)==1
addition='''            # Manual experiment factor only; arm has already been selected.
            if memory.get('experiment_target_rule') == 'incumbent_offset':
                bx, by = basket['p'][:2]
                tx, ty = bx - 0.0175, by - 0.035
                if abs(bx) < 0.1:
                    tx = bx + (-0.065 if arm == 'left' else 0.065)
                    ty = by - 0.055

'''
controlled=source.replace(marker,addition+marker)
assert controlled.replace(addition,'')==source
sys.path.insert(0,str(O));from prepare_phase import audit
assert audit(controlled)['admitted']
D=O/'manual-target-control';D.mkdir(exist_ok=False)
(D/'candidate.py').write_text(controlled)
(D/'source.diff').write_text(''.join(difflib.unified_diff(source.splitlines(keepends=True),controlled.splitlines(keepends=True),fromfile='generated_sample_01',tofile='manual_target_control')))
entries=[]
for name,rule in [('target_control','generated'),('target_offset','incumbent_offset')]:
 p=copy.deepcopy(proposal);p.update(source=controlled,rationale='Manual experimental control, not another System2-generated candidate. Exactly one categorical factor: destination XY rule after arm selection. No change to contact, lift/transport/release heights, orientation, gripper timing, native horizon, API, runtime or scoring.')
 p['memory']['experiment_target_rule']=rule
 (D/(name+'.json')).write_text(json.dumps(p,indent=2)+'\n')
 entries.append(dict(name=name,source='manual-target-control/candidate.py',proposal='manual-target-control/'+name+'.json',research_origin='manual_single_factor_control',target_rule=rule))
# Exact recorded-reply replay for control arm; never invoke a real robot.
checks=[]
for f in sorted((O/'sampling/native-campaign/runs/sample_01/attempt-001/model/expert').glob('*/0/policy/processes/isolated/process.json')):
 payload=dict(source=controlled,memory=read(D/'target_control.json')['memory'],calls=read(f)['calls'])
 p=subprocess.run([sys.executable,'-B',str(O/'replay_stops.py'),'--worker'],input=json.dumps(payload),capture_output=True,text=True,timeout=8)
 assert p.returncode==0,p.stderr
 result=json.loads(p.stdout);assert result['all_recorded_calls_matched'] and result['terminal']=='returned',result
 checks.append(dict(process=str(f.relative_to(O)),process_sha256=hashlib.sha256(f.read_bytes()).hexdigest(),**result))
assert len(checks)==5
(D/'control-equivalence-replay.json').write_text(json.dumps(dict(state='passed',cases=checks,native_episodes=0,api_calls=0,gpu_used=False,scope='Inactive added branch and exact original source preserved; five recorded RPC sequences replay identically. This is not a new physical execution.'),indent=2)+'\n')
plan=dict(entries=entries,selection='Manual target-rule diagnostic only; no promotion into the generated-candidate pool',research_role='One fixed sample_01-derived source; only memory target-rule flag differs. Five exposed layouts per group. Manual repair evidence is separate from System2 search efficacy.')
(D/'repair-plan-draft.json').write_text(json.dumps(plan,indent=2)+'\n')
note=dict(state='prepared_not_running',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_sha256=hashlib.sha256(controlled.encode()).hexdigest(),original_source_sha256=hashlib.sha256(source.encode()).hexdigest(),factor='destination XY rule: generated basket-interior target vs historical incumbent relative offsets',primary_mechanistic_outcomes=['first manipulation reaches release','basket-directed no-path rejections','first-cycle stable object delivery proxy'],primary_task_outcomes=['native full-success count','mean native score'],fixed=['chosen arm before first target intervention','all heights and quaternions','all gripper calls/settling rules','source except one guarded target-rule block','100RPC/1100native budgets','frozen baseline executor/API/perception/score/layouts'],limitations=['Offset rule is a categorical bundle of X/Y offsets, not an isolated effect of either coordinate.','Closed-loop later actions can differ as consequences of the target intervention.','Control-first cohort order and nondeterministic execution remain limitations.','This manual target experiment is not a System2-generated improvement and never replaces the original generated sample.','No globally changed executor; no initial-pool runtime rebinding required.','Round2 may receive this development evidence but must generate its own untouched proposal.'],unused_alternative='closed_gripper_spacing remained a prepared hypothesis; no native spacing treatment is authorized by this plan')
(D/'design-draft.json').write_text(json.dumps(note,indent=2)+'\n')
print(json.dumps(dict(state='prepared',control_replays=len(checks),factor=note['factor'])))
