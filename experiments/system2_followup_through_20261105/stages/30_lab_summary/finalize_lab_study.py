"""Consolidate completed lab diagnostics without new GPU/API experiments."""
import collections,csv,datetime,hashlib,json,os,re,statistics,subprocess
from pathlib import Path
R=Path('/mnt/data/joey_tr/physical-RSI');C=R/'result/27_system2_offline_diagnostics/20261104_cpu_v1';G=R/'result/28_h100_offline_acceptance';A=R/'result/29_system2_feedback_api/20261104_v1';E=A/'offline-eval-v1';F=E/'followup-v2';O=R/'result/30_system2_lab_diagnosis/20261104_v1'
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,v):
 p=O/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def table(name,rows):
 with (O/name).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
if (O/'completion.json').exists():raise RuntimeError('Completed report exists')
O.mkdir(parents=True,exist_ok=True);os.umask(0o077)
assert read(G/'20261104_v6_sparse/status.json')['state']=='complete'
assert read(E/'completion.json')['executions']==120
assert read(F/'completion.json')['cpu_probes_total']==30
assert read(G/'20261104_v5/pi05/completion.json')['state']=='passed'
assert read(G/'20261104_v5/planning/completion.json')['result']['calls']==24
assert read(A/'status.json')['attempts']==6
ledger=read(A/'billing-reviewed.json');usage=[]
for arm in ['baseline','augmented']:
 rows=[x for x in ledger['rows'] if x['id'].startswith(arm)]
 usage.append({'arm':arm,'generation_count':len(rows),'input_tokens':sum(x['input'] for x in rows),'cached_input_subset':sum(x['cached_subset'] for x in rows),'cache_write_subset':sum(x['cache_write_subset'] for x in rows),'output_including_reasoning':sum(x['output_including_reasoning'] for x in rows),'reasoning_subset':sum(x['reasoning_subset'] for x in rows),'mean_generation_seconds':statistics.mean(x['seconds'] for x in rows),'estimated_usd':sum(x['estimated_standard_usd'] for x in rows)})
table('api-usage.csv',usage);save('api-usage.json',usage)
metrics=read(E/'summary.json');extra=read(F/'geometry.json');dynamic=read(F/'dynamic.json')
for r in metrics:
 x=[v for v in extra if v['candidate']==r['candidate']];d=next(v for v in dynamic if v['candidate']==r['candidate'])
 r.update(supplemental_point_predicate_matches=sum(v['predicate_matches_surrogate'] is True for v in x),supplemental_denominator=4,changed_scene_reached=d['changed_scene_reached'],post_changed_scene_approaches=d['post_changed_scene_approaches'])
table('candidate-diagnostics.csv',metrics);save('candidate-diagnostics.json',metrics)
planrows=[]
for key,vals in read(G/'20261104_v5/planning/summary-counts.json').items():
 layout,variant=key.split('/');planrows.append({'layout':int(layout),'variant':variant,'planner_success':vals[0],'solver_calls':vals[1],'seeds':'0,1,2','robot_episodes':0})
table('planning-feasibility.csv',planrows)
policies=[]
for name,p in [('pi05',G/'20261104_v5/pi05/completion.json'),('sparse-memory',G/'20261104_v6_sparse/sparse/completion.json')]:
 d=read(p)['result'];assert len(d['calls'])==3 and all(x['all_finite'] for x in d['calls'])
 policies.append({'policy':name,'load_seconds':d['load_seconds'],'first_inference_seconds':d['calls'][0]['seconds'],'warm_inference_mean_seconds':statistics.mean(x['seconds'] for x in d['calls'][1:]),'inference_calls':3,'action_horizon':50,'per_step_dimensions':14,'reset_verified':d['reset_verified'],'input':'synthetic seed0','native_episodes':0})
table('policy-acceptance.csv',policies)
accounting=[{'item':'Historical CPU study','count':65,'unit':'heterogeneous CPU probe executions','includes_old_evidence':False,'new_robot_episodes':0,'note':'27 fixtures +14 single-variable +4 driver +10 initially misordered prefixes +10 corrected prefixes; keep purposes separate'}, {'item':'Historical native evidence reanalyzed','count':10,'unit':'previous candidate episodes','includes_old_evidence':True,'new_robot_episodes':0,'note':'78 RPC records; not new trials'}, {'item':'H100 reachability','count':24,'unit':'offline solver calls','includes_old_evidence':True,'new_robot_episodes':0,'note':'3 historical targets, variants, 3 solver seeds; no physics'}, {'item':'Policy acceptance','count':6,'unit':'synthetic input inference calls','includes_old_evidence':False,'new_robot_episodes':0,'note':'3 pi05 +3 sparse; not task scores'}, {'item':'Feedback generation','count':6,'unit':'paid API candidate generations','includes_old_evidence':True,'new_robot_episodes':0,'note':'3 baseline +3 augmented; already completed before pause'}, {'item':'Saved candidate main diagnostics','count':120,'unit':'CPU probes','includes_old_evidence':True,'new_robot_episodes':0,'note':'54 fixture +36 point geometry +30 recorded prefixes'}, {'item':'Saved candidate targeted followup','count':30,'unit':'CPU probes','includes_old_evidence':False,'new_robot_episodes':0,'note':'24 supplemental geometry +6 changed-scene follow-through'}]
table('phase-accounting.csv',accounting)
findings=[
 {'id':'F1','claim':'Existing candidates contain local geometric and control-flow weaknesses','evidence':str(C/'REPORT.txt'),'confidence':'CPU behavior reproduced; full native causal contribution not isolated','attribution':'Generated candidate code, not proof of a universal upstream core defect'},
 {'id':'F2','claim':'The recorded no-path error is converted to RuntimeError by the existing driver','evidence':str(C/'driver-memory-and-error-contract.json'),'confidence':'Exact driver text under virtual IO','attribution':'Error delivery works in this contract; catch-and-return can still lose policy-level explanation'},
 {'id':'F3','claim':'The mutated memory object is not separately published by the recorded driver','evidence':str(C/'driver-memory-and-error-contract.json'),'confidence':'Schema observation and copied explicit-consumer prototype only','attribution':'Not established cause of native zero scores; candidates do not read memory; distinct from VLA sparse history'},
 {'id':'F4','claim':'Historical no-path pattern reproduces on H100; smaller lift targets and arm+orientation variants change feasibility','evidence':str(G/'20261104_v5/planning/results.json'),'confidence':'24 solver calls, same pinned recorded inputs','attribution':'Supports target/constraint mismatch; no proof of unavoidable geometry or grasp success'},
 {'id':'F5','claim':'Both existing neural policies can load and emit finite actions on one H100','evidence':str(O/'policy-acceptance.csv'),'confidence':'Three synthetic-input calls per policy, reset verified','attribution':'Does not qualify RGB native simulation or benchmark performance'},
 {'id':'F6','claim':'Supplemental feedback changes generated containment and motion heuristics','evidence':str(O/'candidate-diagnostics.csv'),'confidence':'3 candidates per arm, 150 offline probes, exploratory only','attribution':'Information and longer context are confounded; no native score improvement established'},
 {'id':'F7','claim':'All six candidates stop without further approaches after the changed category is actually observed','evidence':str(F/'dynamic.json'),'confidence':'Six two-scene mock follow-through probes','attribution':'No uncaught error is not evidence of task completion or recovery'},
 {'id':'F8','claim':'No new native improvement or selected policy replacement is demonstrated','evidence':str(O/'phase-accounting.csv'),'confidence':'New robot episodes zero','attribution':'Do not conclude System2 is universally ineffective, or promote any candidate from these diagnostics'}]
save('findings.json',findings)
nextplan=[
 {'experiment':'Geometry contract before policy promotion','variable':'Explicit oriented, relative-Z containment contract versus each saved candidate predicate; vary yaw, height, object extents and measurement uncertainty','fixed':['same recorded units/frame and object schema','same saved candidate source','no new model generations in this check'],'acceptance':['separately report center-point, object-volume and true-interior definitions','zero invalid numeric/quat outputs','test boundary uncertainty without labeling a margin automatically wrong'],'native_required':'Ground-truth physical basket membership and grasp success require supported simulator; current point fixtures are insufficient'},
 {'experiment':'Action completion and failure feedback','variable':'Explicit termination reason and post-action observation checks versus current silent return; one contract change at a time','fixed':['same primitives and step limits','same candidate and task','same planner settings'],'acceptance':['distinguish plan failure, action acknowledgement, executed motion, verified lift and task terminal','scene changes reached in tests','bounded recovery or explicit abort with reason, never silent completion claim'],'native_required':'Verify actual motion and grasp on an RT-capable host; no privileged execution changes on this lab server'},
 {'experiment':'Feedback-content control','variable':'Original feedback, relevant rejected-code/failure feedback, and token-budget-matched control','fixed':['gpt-6.1-sol medium','same parent pi05','same output budget and generation count','same downstream evaluation and cache accounting'],'acceptance':['pre-register all candidates without hidden retries','compare contract pass and heldout task score separately','report latency by cache state','keep cumulative billing under remaining authorized limit'],'native_required':'Do not spend more merely to increase parse-valid samples before an actionable scoring path is available'},
 {'experiment':'Small independent layout acceptance','variable':'A narrowly repaired candidate versus retained pi05 and its unmodified candidate reference','fixed':['same task/robot/assets/version','same layout seed paired across policies','same RGB/deployment/step/scoring protocol','same initial reset contract'],'acceptance':['audit prior layout exposure before selecting unused layouts','freeze 5-10 new paired layouts before generation/selection','report success count, partial score, exceptions, token cost and full wall clock','retain parent unless the frozen selection criterion is met'],'native_required':'Supported RTX/RGB execution host and validated untrusted executor are prerequisites'}]
save('next-experiment-plan.json',nextplan)
report=f'''PhysicalRSI System 2 lab diagnostic study — 2026-11-04

Purpose and conclusion
Investigate where unsuccessful self-improvement breaks: feedback delivery, generated code, primitive contract, planning, or deployment. This study supplies offline causal clues and runtime acceptance, not new RoboDojo success scores. It does not rerun project A or measure a new cross-project token saving.
The strongest result is that the retained deployment can perform CUDA planning and pretrained action inference on one H100, while generated candidates still exhibit distinguishable geometry and continuation weaknesses. Relevant failure feedback changes their code, but it has not yet demonstrated improved native task score.

Execution boundaries
Host gpuserver3; all new persistent server files are under /mnt/data/joey_tr/physical-RSI/result/. One idle physical GPU 1 was selected by UUID GPU-a84ba1a7-488b-54cf-eb02-6ded6cf3f94f. No training, RGB native episode, driver/package/system modification, lab API reuse, GitHub upload or cloud execution was performed. GPU workers used project-local caches and Landlock disk-write confinement; their own process thread/device IO is allowed. Candidate diagnostics use an audited restricted-capability CPU harness, not a qualified substitute for the production privileged executor.

Evidence accounting
See phase-accounting.csv. The previous CPU work contains 65 different-purpose probe executions, including both the preserved incorrectly filename-ordered prefix version and its corrected chronology. The current candidate analysis contains 120 main probes plus 30 targeted followups. Do not pool these into a robot success rate. Historical 10 native candidate episodes/78 RPC receipts are reused evidence. The 24 planner calls and 6 neural inferences are new offline executions. Six API generations were completed before the user-requested pause and were not repeated after resume.

1. Historical fault localization
The original round2 generated code used an XY +/-0.2m basket condition. On six axis-aligned center-point fixtures it matched 3/6 expected decisions; replacing only the extent with half-dimensions matched 6/6. This is not proof that a box-center test matches the real basket's interior. The original candidate also raises KeyError on a watch-to-pen category transition. A separate manually repaired copy can reach the first approach. This is a diagnostic intervention, not autonomous System2 success. The old static fixture can consume the 100-RPC budget; a fixed synthetic scene does not prove an actual physical loop.
The exact recorded driver already converts no_collision_free_path into RuntimeError. Therefore a universal claim that the interface hides every planning failure is contradicted by this contract check. Publishing only the policy return value, rather than mutations to the memory object, was separately observed and a schema prototype passed an explicit counter round-trip. This is not established as the cause of zero native scores and is unrelated to whether sparse visual memory loads.
The chronology correction is authoritative in 27.../followup_v2; original filename-order results are retained for audit.

2. Planning and H100
The 24 historical probes reproduced the same qualitative feasibility pattern:
- layout1 original 20cm lift: 0/3 solver successes; 15cm, 10cm and 5cm targets each 3/3.
- layouts3 and4: left variant 0/3 each; right variant 3/3 each.
The arm comparison changes both the chosen arm and its supplied quaternion. The three seeds are solver-repeatability probes, not independent task samples. Failure is not a mathematical proof of unreachable geometry, and a collision-free plan is not a successful grasp. These exact targets are not the newly generated candidates' first targets; do not transfer feasibility claims to a different object/arm/state without testing.

3. Pretrained policy acceptance
pi05 and sparse-memory each loaded their existing Orbax checkpoints and emitted three finite 50-step, 14-dimensional dual-arm action chunks. Each step has 6 arm and1 gripper coordinates per side. Reset cleared the observation state. Sparse history had 0 valid historical frames initially, then1 valid frame after the prescribed repeated observations, and reset cleared history. This is limited causal-history plumbing acceptance; it does not assess useful memory, full 20-frame occupancy or task performance. Inputs were deterministic synthetic RGB/state, not robot rollouts.
Cold and warm timings are in policy-acceptance.csv. They are tiny synthetic inference measurements with compilation/cache differences; no claim of benchmark throughput or cross-project acceleration follows.

4. Feedback generation experiment
Model gpt-6.1-sol, reasoning medium, same max_completion_tokens=12000, JSON output, standard service, no tools, no automatic retries. Three baseline and three augmented requests were interleaved. The selected parent remained pi05. Baseline messages were preserved; the treatment appended rejected candidate source and attributed historical failures/ordered observations. No hand-written repaired answer was appended. Current_code was empty for the neural parent in the baseline, so this treatment explicitly exposes the rejected program history rather than pretending the parent has Python code.
All six responses parsed as the requested JSON and valid Python. Parsing alone is not algorithm quality. Input tokens per request: baseline3138 versus augmented13475. The treatment uses more context and does not establish token reduction. Prompt content and context length vary together. Cache state and generation randomness further limit timing interpretation. Exact usage and request hashes are preserved under29...; aggregate api-usage.csv keeps cached and cache-write tokens as input subsets, and reasoning as an output subset.
Reviewed usage-based estimate: USD {ledger['estimated_total_usd']:.7f}; user ceiling USD10. Conservative whole-batch reservation was USD{ledger['conservative_whole_batch_reserve_usd']:.6f}, not an actual charge. The initial online ledger understated cache-write premium; billing-reviewed.json and api-usage.csv are authoritative for this analysis. Account invoice remains authoritative for actual cost. No new API calls were needed after resume; no key was persisted.

5. Main candidate comparison: 120 CPU probes
54 fixture executions (6x9),36 center-point geometry executions (6x6),30 sequence-ordered historical prefixes (6x5). All candidate sources and scene inputs were hash checked unchanged. No invalid approach/gripper arguments, uncaught fixture exceptions or 100-RPC exhaustion were observed in these six candidates. This is limited to these tests.
All six reached a first approach in all five historical diagnostic layouts. These were stop-before-action prefixes, not native executions. All baseline first approach heights were1.14m; all augmented heights were1.01m. Baselines selected right in all five layouts; augmented candidates selected right for0/1/2 and left for3/4. These are changed heuristics, not proof of more feasible or successful actions.
Baseline candidates matched6/6 axis-aligned center-point expectations each. Augmented candidates matched5/6 each: they introduced8-12mm inset margins, so the near-edge point(.09,.07) in a(.2,.15) footprint was treated as outside. This is a disagreement with a center-footprint surrogate, not an established physical defect; object size and basket wall geometry matter.
For the object high above the basket, all baselines returned true from their XY-only containment predicate; all augmented candidates returned false. Predicate returns were separately instrumented because the absence of an approach could instead be caused by height safety bounds.
No-path and transport-error fixtures caused every candidate to return after one attempted approach. None of these returns means task completion. Static mock scene RPC totals were11 for each baseline and9,9,8 for augmented candidates, versus the old candidate's budget exhaustion; fewer calls may also reflect earlier stopping, and is not a success metric.

6. Targeted followup: 30 CPU probes
These were designed after initial inspection and are explicitly exploratory, not heldout confirmation. Four point-predicate scenes per candidate test90-degree basket yaw, common vertical translation and a below-basket point; six more runs allow the prior category-change fixture to proceed past mock actions.
Baseline candidates matched1/4,1/4,2/4 of these supplemental point expectations. Augmented candidates matched4/4,4/4,2/4. In particular augmented_3 used an absolute object-Z threshold below1.0m: it failed the raised-basket and below-basket tests despite handling the original above-basket case. The other two use relative vertical geometry. Full physical containment still needs explicit ground truth; these numbers are not task scores or a basis to promote a winner.
The first dynamic-category prefix test stopped augmented_2 at its first action before it saw the new category. That result cannot establish recovery. The follow-through correction ensures every candidate receives the changed scene: all six then return with zero further approach requests. The old KeyError is absent, but continuing to handle the new object is not demonstrated. This is a distinct and actionable limitation.

7. What can and cannot be attributed
Candidate-specific geometric tests and source/branch logic are directly inspectable. The reproduced solver constraints support target/arm-orientation mismatch as one local failure mechanism. The existing no-path error contract is functioning in the tested driver, so the evidence does not support labeling all failures an interface-delivery bug.
The changed feedback produced changed candidate behavior, but two groups of3 with different context lengths and no physical scoring do not prove the original PhysicalRSI algorithm is defective or that feedback augmentation improves benchmark success. Historical versions, adapters and generated candidates must remain distinguished. Retaining pi05 when candidates do not improve is compatible with a correctly functioning selector. No candidate was deployed or promoted in this study.

8. Harness corrections, preserved attempts
GPU attempts v1-v3 failed at CUDA initialization because of the new diagnostic controller/worker confinement setup; v4 passed CUDA after per-worker confinement. v4 then encountered two harness issues: the copied planner YAML had lost sibling URDF/mesh resolution, and the output checker treated a list of action dictionaries as a numeric array. v5 restores sibling asset links in the new directory and stacks numeric fields without changing model or planner logic. v5 planning and pi05 passed. A user pause stopped only the owned scheduler; the pi05 worker finished naturally. After resume v6 ran only the remaining sparse worker. These setup failures must not be entered as robot-policy failures. Existing source/environment files were preserved.

9. Next experiments
See next-experiment-plan.json for variables, fixed conditions and acceptance metrics. Prioritize the containment contract and explicit stop/recovery feedback; evaluate one change at a time. Additional generations alone are not a substitute for validated execution and scoring. The lab H100 can continue API, CPU contract and offline CUDA work, but the existing IsaacSim5.1 RGB route needs a supported rendering host. The original privileged isolation backend also remains unqualified for this ordinary lab account; no sudo or system permission changes were attempted. Audit layout exposure before defining5-10 new paired layouts; no unused layout set has been selected here.

Reproduction and audit
REPRODUCE.txt identifies immutable inputs and the separate scripts. evidence-index.json hashes the report inputs; artifact-manifest.json hashes new report artifacts. Logs, proposals, input messages, raw provider usage, trajectories and action arrays remain in their source result batches, not copied into a code repository. Statistical generalization and native outcome improvement remain unknown.
'''
(O/'REPORT.txt').write_text(report)
(O/'REPRODUCE.txt').write_text('Read continuation.json and actual processes before any run. Do not overwrite completed batches. CPU historical script: 27.../run_cpu_batch.py. Main new candidate evaluation: 29_system2_feedback_api/20261104_v1/offline-eval-v1/evaluate_candidates.py; target followup: offline-eval-v1/followup-v2/followup_candidates.py. Both admit pinned saved candidates and run without API/GPU. GPU worker source: 28_h100_offline_acceptance/20261104_v5/run_gpu_batch.py; sparse-only controller: 20261104_v6_sparse/resume_sparse.py. For independent repeat change output root to a NEW project-local directory and verify one idle GPU; never invoke an old completed main(). Preserve cached compilation and hardware differences in timing records. Do not regenerate the six API candidates unless a NEW explicitly designed generation study is required. Model messages/settings/raw usage are under29.../v1; billing-reviewed.json supersedes the initial ledger cost estimate. No synthetic probe may be counted as a new native robot episode.\n')
evidence=[C/'REPORT.txt',C/'completion.json',C/'followup_v2/completion.json',C/'driver-memory-and-error-contract.json',C/'followup_v2/feedback/prompt-comparison.json',G/'20261104_v4/basic/completion.json',G/'20261104_v5/planning/protocol.json',G/'20261104_v5/planning/results.json',G/'20261104_v5/pi05/completion.json',G/'20261104_v6_sparse/sparse/completion.json',A/'protocol.json',A/'ledger.json',A/'billing-reviewed.json',E/'candidate-audit.json',E/'completion.json',E/'summary.json',E/'recorded-prefix-matrix.json',E/'fixture-matrix.json',E/'geometry-matrix.json',F/'protocol.json',F/'completion.json',F/'geometry.json',F/'dynamic.json']
evidence += list((A/'candidates').glob('*/candidate.py'))+list((A/'responses').glob('*.json'))+list((A/'requests').glob('*.json'))
save('evidence-index.json',[{'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in evidence])
# Scan only new text evidence; never print potential credential values.
hits=[]
pattern=re.compile(rb'sk-(?:proj-|ws-)[A-Za-z0-9_.-]{16,}|-----BEGIN (?:OPENSSH |RSA )?PRIVATE KEY-----')
for root in [A,O,G/'20261104_v6_sparse']:
 for p in root.rglob('*'):
  if p.is_symlink() or not p.is_file() or 'cache' in p.relative_to(root).parts or p.suffix not in ['.py','.json','.log','.txt','.csv']:continue
  if pattern.search(p.read_bytes()):hits.append(str(p))
save('credential-scan.json',{'scope':'New API/evaluation/report/sparse textual artifacts; caches and binaries excluded','credential_pattern_hit_files':hits});assert not hits
owned=[]
for d in Path('/proc').iterdir():
 if not d.name.isdigit() or int(d.name)==os.getpid():continue
 try:
  cmd=(d/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
  if str(R) in cmd and any(x in cmd for x in ['resume_sparse.py','evaluate_candidates.py','followup_candidates.py','run_gpu_batch.py','run_api_batch.py']) and not 'python3 -B -c' in cmd:owned.append(int(d.name))
 except OSError:pass
gpu=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader'],text=True).strip()
save('final-process-audit.json',{'at':now(),'active_owned_experiment_pids':owned,'gpu_process_snapshot':gpu,'gpus':subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader'],text=True).strip()});assert not owned
save('completion.json',{'state':'completed_lab_offline_scope','finished_utc':now(),'new_candidate_cpu_probes':150,'planning_calls':24,'policy_inferences':6,'paid_generations':6,'new_api_calls_after_resume':0,'native_episodes':0,'policy_promotion':False,'estimated_api_usd':ledger['estimated_total_usd'],'credentials_persisted':False,'remaining':['Native task score and independent layout acceptance','Production untrusted executor validation','Content-versus-length feedback control if justified']})
cont={'state':'completed_lab_offline_scope','updated_utc':now(),'host':'gpuserver3','active_owned_processes':[],'report':str(O/'REPORT.txt'),'results':{'cpu':str(C),'gpu_planning_pi05':str(G/'20261104_v5'),'sparse':str(G/'20261104_v6_sparse'),'api_and_candidates':str(A),'candidate_eval':str(E),'followup':str(F),'consolidated':str(O)},'api_estimated_usd':ledger['estimated_total_usd'],'api_budget_usd':10,'api_key':'not persisted; do not recover old keys','gpu_permission':'one idle H100 only; recheck current availability','next_action':'Review diagnostics and arrange supported native RGB execution plus validated isolation; no repeated paid generations or old successful checks without a new experiment design','new_native_episodes':0}
save('continuation.json',cont)
for p in [C/'continuation.json',G/'20261104_v5/continuation.json',A/'continuation.json']:p.write_text(json.dumps(cont,indent=2)+'\n')
manifest=[{'path':str(p.relative_to(O)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in O.rglob('*') if p.is_file() and not p.is_symlink() and p.name!='artifact-manifest.json']
save('artifact-manifest.json',manifest)
print(json.dumps({'report':str(O/'REPORT.txt'),'completion':read(O/'completion.json'),'candidate_summary':metrics,'gpu_snapshot':read(O/'final-process-audit.json'),'evidence_files':len(evidence),'report_artifacts':len(manifest)},ensure_ascii=False))
