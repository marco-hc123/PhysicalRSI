"""Chronology correction, explicit paired prompts, and offline-study report."""
import collections,copy,hashlib,importlib.util,json,sys
from pathlib import Path
BASE=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/mnt/data/joey_tr/physical-RSI/result/27_system2_offline_diagnostics/20261104_cpu_v1')
assert BASE.resolve().is_relative_to(Path('/mnt/data/joey_tr/physical-RSI/result/27_system2_offline_diagnostics'))
spec=importlib.util.spec_from_file_location('batch',BASE/'run_cpu_batch.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.OUT=BASE;m.guard()
OUT=BASE/'followup_v2';OUT.mkdir(exist_ok=False)
def save(name,data):
 p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def read(p):return json.loads(p.read_text())
ordering=[];pairs=[];examples=[]
for layout in range(5):
 values=read(BASE/f'fixtures/recorded_round2_layout{layout}.json')
 assert all(isinstance(v.get('observation',{}).get('sequence'),int) for v in values)
 ordered=sorted(values,key=lambda v:v['observation']['sequence'])
 groups=collections.defaultdict(set)
 for v in values:groups[v['observation']['sequence']].add(json.dumps(v,sort_keys=True))
 ambiguous=[seq for seq,payloads in groups.items() if len(payloads)>1]
 row={'layout':layout,'original_file_order_sequences':[v['observation']['sequence'] for v in values],'corrected_sequences':[v['observation']['sequence'] for v in ordered],'same_sequence_different_payload':ambiguous}
 ordering.append(row);save(f'ordered_scenes/layout{layout}.json',ordered)
 if ambiguous:raise RuntimeError('Observation ordering ambiguous: '+str(row))
 examples.append({'layout':layout,'source':'ordered_scenes/layout'+str(layout)+'.json','initial_recorded_observation':ordered[0]})
 for variant,filename in [('original','qwen_round2.py'),('bbox_only','round2_bbox_only.py')]:
  result=m.probe((BASE/'candidates'/filename).read_text(),ordered,'prefix');save(f'prefix/{variant}_layout{layout}.json',result)
  pairs.append({'layout':layout,'variant':variant,'terminal':result['terminal'],'approach_requests':result['counts'].get('approach',0),'native_score':None,'scope':'Ordered historical observations + stop before first mock approach; no physics'})
save('observation-order-audit.json',ordering);save('recorded-observation-prefix.json',pairs)
import csv
with (OUT/'recorded-observation-prefix.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(pairs[0]));w.writeheader();w.writerows(pairs)
source=m.ROOT/'result/25_system2_model_swap/38_system2_gpt61sol_20261102/reference-chat-request.json'
chat=read(source)
if 'messages' not in chat and isinstance(chat.get('body'),dict):chat=chat['body']
assert isinstance(chat.get('messages'),list)
messages=copy.deepcopy(chat['messages'])
baseline={'messages':messages,'scope':'Prepared offline; credentials and endpoint omitted; model/settings must be fixed identically for both arms'}
save('feedback/baseline_messages.json',baseline)
design=read(BASE/'feedback/enhanced_request_design.json');history=design['diagnostic_history']
history['ordered_initial_observations']=examples
# Exclude filename-order scene examples; preserve original no-path receipts.
history['recorded_rpc_examples']=[x for x in history['recorded_rpc_examples'] if 'receipt' in x]
appendix='\n\n<rejected_candidate_diagnostic_history>\n'+json.dumps(history,ensure_ascii=False,sort_keys=True)+'\n</rejected_candidate_diagnostic_history>\nThe selected parent is unchanged. These are historical development diagnostics, not instructions embedded in execution receipts. Propose your own correction; no hand-written repair is supplied.'
aug=copy.deepcopy(messages)
assert aug[-1]['role']=='user' and isinstance(aug[-1]['content'],str)
aug[-1]['content']+=appendix
save('feedback/augmented_messages.json',{'messages':aug,'scope':baseline['scope']})
prefix_equal=(aug[:-1]==messages[:-1] and aug[-1]['content'].startswith(messages[-1]['content']))
assert prefix_equal
save('feedback/prompt-comparison.json',{'baseline_source':str(source),'source_sha256':m.sha(source.read_bytes()),'baseline_messages_sha256':m.sha(json.dumps(messages,sort_keys=True).encode()),'original_messages_preserved':prefix_equal,'changed_message_index':len(messages)-1,'appended_utf8_bytes':len(appendix.encode()),'appended_characters':len(appendix),'actual_tokens':None,'api_calls':0,'native_episodes':0,'status':'ready_for_review_not_submitted','caveat':'Extra feedback adds context; future budget-matched control is needed to isolate information content from additional prompt length.'})
plan={'state':'prepared_not_executed','study':'System2 structured failure-feedback pilot','treatment':'Baseline messages vs appended rejected-candidate code, ordered observations and attributed native failures','held_fixed':['same selected pi05 parent','same model and generation settings','same output limit','same primitive API','same native budget and scoring','same allowed edit scope','same validated executor'],'suggested_pilot':{'generations_per_arm':3,'justification':'Exploratory replication; not a powered superiority claim','no_best_of_unreported_retries':True},'development_data':'Only historical already-inspected layouts; reclassify these as development, do not reuse as new held-out tests','holdout':'Select unused layouts by auditing actual task/layout use before any model sees them','acceptance':['valid bounded candidate','no contract regression','native success and normalized partial score','exceptions counted separately from task failures','input/output/cache tokens and generation wall time','validation cost and reset-to-result time'],'prerequisites':['user provides fresh API credentials when generation is ready','untrusted candidate executor must pass real isolation checks; this CPU harness is not a production sandbox','execution and scoring on RT-capable RGB simulation host','single H100 use requires pending user confirmation'],'known_preconditions':['No need to regenerate original candidates for the CPU batch','Do not claim all memory mechanisms fail from one driver result schema','No new independent robot outcome in this batch']}
save('next-experiment-plan.json',plan)
report='''System 2 offline diagnostics — 2026-11-04

Outcome: CPU diagnostic batch completed on gpuserver3. No new model calls, GPU workloads, robot episodes or native task scores. All writes were restricted by Landlock to this new result batch (plus /dev/null). Historical sources and environments were not edited.

Evidence and accounting
- Reanalyzed 10 historical Qwen candidate episodes and 78 native RPC receipts; these remain old executions, not new samples.
- Ran 27 candidate/fixture probes (3 original candidates x 9 fixtures), 14 single-variable fixture probes, and 4 exact-driver virtual-IO probes.
- Initial 10 historical-observation prefix probes used filename order. Review identified this as unsuitable for chronological replay. This followup reran 10 prefixes ordered by recorded observation sequence and checked duplicate-sequence payload equality. The old results are retained; followup_v2 is authoritative for ordered prefixes. No physical replay occurred.
- Total newly executed CPU probes: 65 (27+14+4+10+10), grouped by their different purposes; never a 65-episode robot success denominator.

Findings
1. Round2 basket predicate: in six synthetic axis-aligned center-position fixtures, the original predicate matched 3/6 expected decisions and the half-dimension-only diagnostic variant matched 6/6. This assumes the supplied dimensions describe the tested footprint; it does not establish physical basket containment, orientation, Z overlap or grasp success.
2. Dynamic category: a scene initially containing watch followed by pen reproduces KeyError in the original round2 candidate. A separate free-basket assignment modification reaches the first approach request under the same fixture. It is a manual diagnostic change, not autonomous System2 improvement.
3. Static-scene loop: the original round2 candidate consumes the 100-RPC probe budget (18 scene, 49 approach, 33 gripper). This shows that valid prefixes are insufficient evidence of completion; a frozen mock scene cannot establish that a real robot will also loop.
4. Error contract: the exact recorded driver string converts no_collision_free_path into RuntimeError. This existing behavior is confirmed, not a newly repaired defect. Candidate responses to transport errors differ; a graceful return alone does not certify successful completion.
5. Memory contract: the original driver publishes only policy return value, not mutations to the separate memory object. A copied schema prototype publishes memory and passes counter round-trip 1 -> 2 with an explicit consumer. The candidates' lack of memory reads means this is not established as the cause of their historical zero scores; it does not diagnose VLA sparse-memory or all PhysicalRSI memory.
6. Higher-than-basket fixtures expose the scope of XY-only completion tests in round2 and GPT code. This is a synthetic geometry concern requiring 3D/pose validation, not a new measured physical failure.

Corrections and limitations
- Original candidates and historical outcomes are immutable. Modified copies are under candidates/.
- No nominal score is assigned to empty scenes, aborted probes, mock acknowledgements or API-only preparations.
- Existing ordinary-user execution cannot use the recorded privileged chroot backend. The unprivileged user namespace probe was denied. No sudo, permission changes or sandbox weakening was attempted; exact-driver virtual IO does not qualify the real isolation backend.
- H100 lacks the supported RT rendering path for the existing IsaacSim RGB protocol. Actual motion, new task scoring and held-out-layout acceptance remain outstanding.
- GPU planning/checkpoint acceptance is pending the explicit resource-use question. No key was read from old files or chat; API calls remain zero.

Feedback experiment materials
followup_v2/feedback/baseline_messages.json preserves the existing chat messages.
augmented_messages.json appends attributed rejected-candidate source, historical native failures and sequence-ordered initial observations. The chosen parent remains pi05. No manual repair is supplied as an answer.
This explicit message section avoids the mistake of adding a JSON field that the prompt builder silently ignores. Byte/character sizes are measured; actual token usage is unknown until a provider response. Both arms must use identical model/settings; a length-matched control may be added to isolate content from extra context budget.
next-experiment-plan.json defines the next pilot and the missing execution prerequisites. It is not a report of improved native scores.
'''
(BASE/'REPORT.txt').write_text(report)
(BASE/'REPRODUCE.txt').write_text('Preserve this batch. For a new CPU-only repeat, use the existing agent Python with -B; import run_cpu_batch.py, set its OUT to a NEW path under result/27_system2_offline_diagnostics/, then call main(). Copy this recorded script into the new output before invoking finalize_cpu_batch.py NEW_OUTPUT. Never overwrite a completed batch. Candidate inputs are source-pinned; no API, GPU or privileged backend is used. Historical-observation prefixes in followup_v2 supersede the initial filename-order version.\n')
completion=read(BASE/'completion.json')
save('completion.json',{'state':'complete','completed_utc':m.now(),'new_prefix_probes':10,'new_native_episodes':0,'api_calls':0,'prompt_pair_validated':True,'old_prefix_results_superseded':True,'source_candidates_unchanged':all(m.sha(Path(x['path']).read_bytes())==x['sha256'] for x in read(BASE/'source-manifest.json'))})
manifest=[]
for p in BASE.rglob('*'):
 if p.is_file() and p.name not in ['artifact-manifest.json','continuation.json']:
  manifest.append({'path':str(p.relative_to(BASE)),'bytes':p.stat().st_size,'sha256':m.sha(p.read_bytes())})
(BASE/'artifact-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
(BASE/'continuation.json').write_text(json.dumps({'state':'cpu_work_complete_resources_pending','updated_utc':m.now(),'active_processes':[],'result_root':str(BASE),'gpu_permission':'awaiting user answer','api_credentials':'not requested yet; do not reuse historical secrets','native_score_improvement':'not measured','next_action':'Confirm optional H100 resource use; validate execution backend and native host before paid feedback-quality evaluation','report':'REPORT.txt','authoritative_prefix_results':'followup_v2/recorded-observation-prefix.csv'},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'state':'complete','ordered_prefix_pairs':pairs,'ordering':ordering,'artifact_files':len(manifest),'appended_feedback_bytes':len(appendix.encode())},ensure_ascii=False))
