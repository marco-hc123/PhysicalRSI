"""Freeze saved-candidate evaluation before starting any robot episode."""
from pathlib import Path
import datetime
import hashlib
import json

R=Path('/mnt/data/physical-RSI')
O=R/'result/31_rgb_supplement_20261105/protocol'
O.mkdir(exist_ok=True)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

names=['baseline_1','augmented_1','augmented_2','baseline_2','baseline_3','augmented_3']
base=R/'reference/result/29_system2_feedback_api/20261104_v1/candidates'
candidates=[{'name':name,'source':str(base/name/'candidate.py'),
             'source_sha256':sha(base/name/'candidate.py'),
             'proposal_sha256':sha(base/name/'proposal.json')} for name in names]
original=R/'result/31_system2_final_validation_20261030T121000Z/workspace/rounds/round-000000'
cases=json.loads((original/'validation-cases.json').read_text())
rows=[]
for case in cases:
    path=original/'validation-layouts'/case['file']
    value=json.loads(path.read_text())
    # The recorded layout identity hashes canonical JSON, not pretty-printed bytes.
    canonical=hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    assert canonical==case['layout_sha256'], case['file']
    rows.append({'file':case['file'],'layout_sha256':canonical,'raw_file_sha256':sha(path),
                 'task':case['task'],'framework_split':case['split'],
                 'research_role':'previously exposed diagnostic/development reuse; not heldout'})
assert len(rows)==5 and all(row['task']=='classify_objects' for row in rows)
runtime=R/'result/31_system2_final_validation_20261030T121000Z/runtime.json'
protocol={
    'schema':'physicalrsi.rgb-supplement.protocol/v1',
    'frozen_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'state':'frozen before new native execution; resource and executor qualification pending',
    'question':'Do saved feedback-augmented candidates change native execution or task outcome, and where does each first fail?',
    'prerequisites':[
        'Frozen model and asset hashes verified',
        'Recorded privileged isolated executor qualified',
        'Original RGB, robot reset, task and scoring pipeline qualified'],
    'runtime':{'path':str(runtime),'sha256':sha(runtime),'preserve_recorded_values':True,
               'python':'3.11.17','isaac_sim':'5.1.0','simulator_packages':267,
               'policy_packages':232,'verified_runtime_code_files':741,
               'known_frozen_metadata_conflict':'rerun-sdk NumPy>=2 declaration against policy NumPy1.26.4; preserve versions and qualify actual runtime imports'},
    'matrix':{'task':'classify_objects','parent':'retained pi05, unchanged pretrained checkpoint',
              'saved_candidates':candidates,'layouts':rows,'native_logical_cases':35,
              'execution_order':['pi05']+names,
              'execution':'One native cohort at a time; same five cases in frozen order',
              'batch_semantics':'Preserve original five-environment native cohort semantics',
              'selection':'Diagnostic batch only; parent remains selected'},
    'qualification_accounting':'First pi05 cohort also qualifies deployment. Include its five cases only when frozen conditions and result validity checks pass. Preserve incomplete/setup attempts separately and report any reruns.',
    'outcomes':[
        'Task-native success and raw score, using original evaluator semantics',
        'First failure stage: perception, containment, target/arm choice, planning, action execution, termination, scoring',
        'Attempted RPC, acknowledgement, measured motion, verified lift and task completion distinguished',
        'API requests and tokens, expected zero for saved-candidate evaluation',
        'Startup, reset-to-result, observable component times and full wall clock',
        'CPU/GPU/RAM samples, original logs and videos'],
    'failure_policy':'Do not silently count infrastructure/import/crash/setup failures as valid zero-scoring policy episodes. Preserve every attempt and determine validity with the frozen evaluator.',
    'causal_limits':[
        'Three saved generations per condition and five reused layouts: descriptive diagnostic comparison',
        'Feedback content and context length both differ; not a token-budget-matched intervention',
        'Do not transfer old planner target feasibility to different new targets',
        'API return values and fewer calls do not imply task success',
        'CPU/RAM differs from original host; timing is condition-specific'],
    'later_gated_steps':[
        'Use first-failure evidence to register one-variable repair and paired controls before execution',
        'Audit all historical layout exposure before freezing5-10 new paired layouts',
        'Independent acceptance compares repaired candidate, its unchanged source and retained pi05',
        'Additional model generation requires fresh credentials and remaining authorized budget check'],
    'delivery_root':'/mnt/data/joey_tr/physical-RSI/result/31_system2_rgb_validation/20261105_v1',
    'summary_host_wording':'server','preserve_original_machine_metadata':True,
    'new_api_calls_so_far':0,'new_robot_episodes_so_far':0}
path=O/'diagnostic-matrix-v1.json'
with path.open('x') as stream:
    stream.write(json.dumps(protocol,indent=2))
(O/'diagnostic-matrix-v1.sha256').write_text(sha(path)+'  diagnostic-matrix-v1.json\n')
(O/'layout-digest-audit.json').write_text(json.dumps({
    'recorded_identity':'SHA256 of canonical JSON with sorted keys and compact separators',
    'raw_file_digest_is_distinct':True,'all_five_canonical_digests_match':True,
    'layouts':rows},indent=2))
print(json.dumps({'path':str(path),'sha256':sha(path),'planned_cases':35,
                  'layouts':5,'native_execution_started':False}))
