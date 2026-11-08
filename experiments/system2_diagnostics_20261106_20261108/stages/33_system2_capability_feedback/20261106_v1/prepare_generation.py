"""Freeze a paired feedback comparison before any model generation."""
import copy,datetime,hashlib,json
from pathlib import Path
R=Path('/mnt/data/joey_tr/physical-RSI')
O=R/'result/33_system2_capability_feedback/20261106_v1'
OLD=R/'result/29_system2_feedback_api/20261104_v1'
D=R/'result/32_system2_lift_gate_diagnosis/20261106_v1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
assert not (O/'protocol.json').exists(),'Do not overwrite frozen experiment'
O.mkdir(parents=True,exist_ok=True)
req=read(OLD/'requests/augmented_3.json')
base=copy.deepcopy(req['messages'])
candidate=OLD/'candidates/augmented_3/candidate.py'
common=dict(kind='additional_shared_development_evidence',candidate_name='augmented_3',
 source=candidate.read_text(),source_sha256=sha(candidate),
 observations=dict(task='classify_objects',exposed_layouts=5,score_100=[0,0,0,0,0],
 completed_calls_before_return=8,stop='Returns after its post-lift scene guard; no subsequent transport call.',
 note='These are previously exposed development cases, not heldout. Native evaluation independently scores task completion.'),
 instructions='Propose your own policy and reusable memory. The selected parent remains pi05. No manually repaired code is supplied. Generated memory will be passed unchanged to policy(robot,memory).')
base.append(dict(role='user',content='<shared_recent_development_evidence>\n'+json.dumps(common,ensure_ascii=False)+'\n</shared_recent_development_evidence>'))
caps=read(D/'contract-audit/feedback-contract-v2.json')
caps={k:v for k,v in caps.items() if k not in ['provenance','status','schema']}
addition='Verified deployed capability clarification. For conflicting earlier API descriptions, this clarification is authoritative. This is interface and observed failure information, not hidden simulator state or a repaired policy.\n'+json.dumps(caps,ensure_ascii=False,sort_keys=True)
messages={'legacy_feedback':base,'capability_feedback':base+[dict(role='user',content=addition)]}
order=['legacy_feedback','capability_feedback','capability_feedback','legacy_feedback','legacy_feedback','capability_feedback']
counts={k:0 for k in messages};rows=[]
for arm in order:
 counts[arm]+=1;name=arm+'_'+str(counts[arm])
 request=dict(model='gpt-6.1-sol',messages=messages[arm],reasoning_effort='medium',max_completion_tokens=12000,response_format={'type':'json_object'},service_tier='default',store=False)
 raw=json.dumps(request,ensure_ascii=False).encode();bound=len(raw)+4096
 assert bound<100000
 reserve=(bound*6+12000*20)/1e6
 save(O/'requests'/(name+'.json'),request)
 rows.append(dict(id=name,arm=arm,replicate=counts[arm],request_file='requests/'+name+'.json',request_sha256=sha(O/'requests'/(name+'.json')),input_token_upper_bound=bound,reserved_usd=reserve))
prior=read(OLD/'billing-reviewed.json')
prior_reserve=prior['conservative_whole_batch_reserve_usd']
reserve=sum(x['reserved_usd'] for x in rows)
assert prior_reserve+reserve<10
protocol=dict(schema='physicalrsi.capability-feedback/v1',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
 question='Does explicit verified API capability feedback change generated assumptions and native outcomes?',
 model='gpt-6.1-sol',reasoning_effort='medium',endpoint='https://api.openai.com/v1/chat/completions',calls_planned=6,
 order=order,requests=rows,replicates_per_arm=3,
 treatment='Append only the verified capability clarification; both arms share identical historical augmented feedback and the same recent failed candidate source and observed stop evidence.',
 refinement_of_draft='Current failed candidate and raw stop evidence are supplied equally to both arms to isolate the capability clarification; frozen before generation, no outcome-dependent adjustment.',
 fixed=['Same base messages, source history, model, reasoning, output limit, response schema and no tools','Same five exposed diagnostic layouts, runtime, scoring and1100 native steps','Exact generated source AND memory passed to the runtime; no manual fixes'],
 planned_native_cases=30,planned_native_cases_per_candidate=5,
 selection='Exploratory matched candidate comparison; no automatic promotion, no heldout claim, pi05 retained.',
 admissions='Syntax and capability-isolation admission before native execution. Record all generated candidates and rejections; no selective regeneration. Rejected candidates have no native score, not zero.',
 metrics=['All candidates, invalid/rejected cases, success and native score','Unsupported nominal-Z/absence/instance-ID assumptions','Stop stage, failed and incomplete calls, step-limit cancellations','Generation usage/cache subsets and cost separate from native timing'],
 limitations=['Three generated candidates per arm; stochastic generations are not matched random seeds','Five exposed layouts per candidate, not15 independent layouts per arm','Content and prompt length differ; no attribution solely to length','Manual diagnostic outcomes are historical evidence, not new autonomous successes','No full RoboDojo benchmark or causal generalization from this small study'],
 budget_usd=10,previous_reserved_usd=prior_reserve,previous_reviewed_estimate_usd=prior['estimated_total_usd'],whole_batch_reserved_upper_usd=reserve,combined_reserved_upper_usd=prior_reserve+reserve,
 reserve_rates_per_million=dict(input=6,output=20),standard_rates_per_million=dict(input=2,cached_input=.1,cache_write=2.5,output=10),
 pricing_source='https://developers.openai.com/api/docs/models/gpt-6.1-sol',no_automatic_retries=True,
 sources=[dict(path=str(p),sha256=sha(p)) for p in [OLD/'requests/augmented_3.json',candidate,D/'contract-audit/feedback-contract-v2.json',D/'FINAL_SUMMARY.json',OLD/'billing-reviewed.json']])
save(O/'protocol.json',protocol)
save(O/'status.json',dict(state='protocol_frozen',pid=None,planned_calls=6,planned_native_cases=30,api_calls=0,new_native_cases=0))
print(json.dumps(dict(state='protocol_frozen',root=str(O),calls=6,new_reserve=reserve,combined_reserve=prior_reserve+reserve)))
