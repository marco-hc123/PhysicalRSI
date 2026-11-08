"""Recompute multi-task results from validated per-episode summaries; no tuning."""
import csv,datetime,json,math
from pathlib import Path
O=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def save(name,value):(O/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
tasks=['classify_objects','general_pickup'];records=[];stages=[];proposals=[];task_results={};interruptions=[]
for task in tasks:
    assert read(O/(task+'-finish-status.json'))['state'] in ['completed','completed_with_runtime_failure']
    selection=read(O/'selection'/f'{task}.json')
    for stage in ['parent','candidates','heldout']:
        phase=task+'-'+stage;summary=read(O/phase/'analysis/summary.json');assert summary['state'] in ['verified','verified_partial']
        rows=read(O/phase/'analysis/episodes.json');assert summary['valid_native_episodes']==len(rows)
        records.extend(rows);stages.append(dict(task=task,phase=phase,native_episodes=len(rows),videos=summary['videos'],role=stage))
        if summary['state']=='verified_partial':
            assert stage=='heldout','Development selection requires separately designed partial handling'
            interruptions.extend(read(O/phase/'analysis/interrupted-attempts.json'))
    parent=next(x for x in read(O/(task+'-parent')/'analysis/summary.json')['summaries'] if x['condition']=='parent')
    candidate_summary=read(O/(task+'-candidates')/'analysis/summary.json')['summaries']
    audit=read(O/(task+'-candidates')/'native-preparation/candidate-audit.json')
    request_rows=read(O/(task+'-generation.json'))['requests']
    summaries={r['condition']:r for r in candidate_summary};admission={r['name']:r for r in audit}
    groups={}
    for condition in ['basic','execution_feedback']:
        selected=[r for r in request_rows if r['condition']==condition]
        stats=[summaries[r['id']] for r in selected if r['id'] in summaries]
        groups[condition]=dict(generated=len(selected),admitted=len(stats),candidate_means=[r['mean_score'] for r in stats],best_development_mean=max([r['mean_score'] for r in stats],default=None),fully_successful_native_episodes=sum(r['complete_successes'] for r in stats),native_episodes=sum(r['n'] for r in stats),unit='Three candidate generations; five matched layouts per admitted candidate. Do not treat15 correlated rollouts as15 independent generated strategies.')
        for r in selected:proposals.append(dict(task=task,condition=condition,candidate=r['id'],admitted=admission[r['id']]['admitted'],errors=admission[r['id']].get('errors'),scores=summaries.get(r['id'],{}).get('scores'),native_episodes=summaries.get(r['id'],{}).get('n',0)))
    held=read(O/(task+'-heldout')/'analysis/summary.json')['summaries'];held={r['condition']:r for r in held};base=held['parent'];paired={}
    for condition,name in selection['selected_views'].items():
        cur=held[name];delta=[a-b if a is not None and b is not None else None for a,b in zip(cur['scores'],base['scores'])];valid_delta=[x for x in delta if x is not None]
        paired[condition]=dict(selected_source=name,reuses_parent_evidence=name=='parent',scores=cur['scores'],complete_successes=cur['complete_successes'],mean_score=cur['mean_score'],paired_score_differences=delta,mean_difference=sum(valid_delta)/len(valid_delta) if valid_delta else None,improved=sum(d>1e-12 for d in valid_delta),worse=sum(d< -1e-12 for d in valid_delta),equal=sum(abs(d)<=1e-12 for d in valid_delta),n=len(valid_delta),planned_n=len(delta),missing_pairs=len(delta)-len(valid_delta))
    task_results[task]=dict(parent_development=parent,candidate_groups=groups,selection=selection['decisions'],heldout_parent=base,heldout_selected_views=paired,heldout_capacity_reference=held.get('pi05_reference'),heldout_overlap_audit=read(O/'layouts'/task/'heldout/overlap-audit.json'))
smoke=read(O/'general_pickup-smoke/analysis/summary.json');stages.insert(0,dict(task='general_pickup',phase='general_pickup-smoke',native_episodes=smoke['valid_native_episodes'],videos=smoke['videos'],role='preparation_not_formal'))
ledger=read(O/'generation-snapshots/general_pickup/ledger.json')
assert len(ledger)==12
generation_costs=[]
for task in tasks:
    request_rows=read(O/(task+'-generation.json'))['requests']
    for condition in ['basic','execution_feedback']:
        ids={r['id'] for r in request_rows if r['condition']==condition}
        rows=[r for r in ledger if r['id'] in ids]
        generation_costs.append(dict(task=task,condition=condition,requests=len(rows),input_tokens=sum(r.get('usage',{}).get('prompt_tokens',0) for r in rows),output_tokens=sum(r.get('usage',{}).get('completion_tokens',0) for r in rows),cached_input_subset=sum((r.get('usage',{}).get('prompt_tokens_details') or {}).get('cached_tokens',0) for r in rows),reasoning_output_subset=sum((r.get('usage',{}).get('completion_tokens_details') or {}).get('reasoning_tokens',0) for r in rows),api_seconds=sum(r.get('seconds',0) for r in rows),estimated_standard_usd=sum(r.get('estimated_standard_usd',0) for r in rows)))
api=dict(requests=len(ledger),http_200=sum(r['http_status']==200 for r in ledger),estimated_standard_usd=sum(r.get('estimated_standard_usd',0) for r in ledger),conservative_reserved_usd=sum(r['reserve_usd'] for r in ledger),cap_usd=10,input_tokens=sum(r.get('usage',{}).get('prompt_tokens',0) for r in ledger),output_tokens=sum(r.get('usage',{}).get('completion_tokens',0) for r in ledger),cached_input_tokens=sum((r.get('usage',{}).get('prompt_tokens_details') or {}).get('cached_tokens',0) for r in ledger),reasoning_output_subset=sum((r.get('usage',{}).get('completion_tokens_details') or {}).get('reasoning_tokens',0) for r in ledger),scope='All12 proposal requests, including rejected or invalid outputs. Cache is part of input; reasoning is part of output. Cost estimated from reported usage; provider invoice authoritative.')
assert api['conservative_reserved_usd']<=10
result=dict(state='completed',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),tasks=task_results,api=api,stage_accounting=stages,actual_native_episodes=sum(r['native_episodes'] for r in stages),actual_videos=sum(r['videos'] for r in stages),formal_native_episodes=len(records),native_initializations=sum(len(list((O/'layouts'/task).glob('*/initialization/*/*/initialization.json'))) for task in tasks),rejected_candidates=sum(not r['admitted'] for r in proposals),scope='Two-task, one-round System2 feedback pilot; study code parents and task-specific observable RGB adapters; not official full benchmark, multi-round self-improvement, or cross-task transfer proof.')
result['generation_by_task_condition']=generation_costs
result['runtime_interruptions']=interruptions
result['runtime_interrupted_episodes']=len(interruptions)
result['actual_native_attempts']=result['actual_native_episodes']+len(interruptions)
result['formal_native_attempts']=len(records)+len(interruptions)
result['completion_qualification']=f'All planned evaluations attempted; {len(interruptions)} heldout executions interrupted and have no native terminal score. No retry or score imputation.' if interruptions else 'All planned native evaluations completed.'
for r in stages:
    r['runtime_interrupted_episodes']=sum(x['phase']==r['phase'] for x in interruptions)
    r['native_attempts']=r['native_episodes']+r['runtime_interrupted_episodes']
save('FINAL_SUMMARY.json',result);save('proposal-accounting.json',proposals)
for name,rows in [('stage-accounting.csv',stages),('episodes.csv',records),('generation-costs.csv',generation_costs)]:
    with (O/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
lines=['MULTI-TASK SYSTEM 2 FEEDBACK PILOT','',result['scope'],'',result['completion_qualification'],'','Sequence: resource qualification -> frozen protocol -> development -> proposals -> admission -> matched evaluation -> selection -> heldout attempt -> evidence verification.','',f"Native executions with terminal scores: {result['actual_native_episodes']} (including one preparation smoke); formal scored executions: {len(records)}; runtime-interrupted attempts: {len(interruptions)}; all native attempts: {result['actual_native_attempts']}; videos: {result['actual_videos']}. Logical selected views reusing the parent are not extra executions. Missing terminal scores are null, never zero.",f"API: {api['requests']} paid requests; estimated USD {api['estimated_standard_usd']:.6f}; conservative reservation USD {api['conservative_reserved_usd']:.2f} / USD10 cap.",'']
for task,r in task_results.items():
    lines += [task, 'Development parent scores: '+str(r['parent_development']['scores'])]
    for condition,g in r['candidate_groups'].items():lines += [f"  {condition}: admitted {g['admitted']}/{g['generated']}; candidate mean scores {g['candidate_means']}; native full successes {g['fully_successful_native_episodes']}/{g['native_episodes']}."]
    lines += ['Selection: '+json.dumps(r['selection']), 'Heldout parent scores: '+str(r['heldout_parent']['scores'])+'; conditional mean uses only completed layouts; missing terminal score does not imply successful acceptance.']
    if r['heldout_capacity_reference']:
        lines += ['Heldout pretrained pi05 reference scores: '+str(r['heldout_capacity_reference']['scores'])+'. Improvement over the study code parent does NOT by itself establish improvement over this released pretrained skill.']
    for condition,g in r['heldout_selected_views'].items():lines += [f"  {condition}: source {g['selected_source']}; scores {g['scores']}; paired differences {g['paired_score_differences']}; improved/worse/equal {g['improved']}/{g['worse']}/{g['equal']}; parent evidence reused={g['reuses_parent_evidence']}."]
    lines+=['']
lines += ['Interpretation limits:', '- Candidate generation and admission are separate from physical execution; rejected source has unknown native score, not zero.', '- These API totals cover System2 proposal generation only. Native evaluations use fixed routes, without high-level System1 API calls. Local DINO/pi05 inference uses compute time, not zero overall resource cost. Do not interpret this pilot as whole-Agent or cross-project token savings.', '- The pickup parent was authored for this study; pi05 is a separate pretrained capacity reference, not an editable parent or equivalent action API.', '- RGB pickup geometry uses an assumed table height and nominal object dimensions. Classification also has task-specific perception assumptions. Zero improvement does not identify System2 itself as the cause.', '- Five development and five heldout layouts per task are a small pilot; selecting a best development candidate is optimistic and requires the reported heldout check. Each policy-layout pair has one native rollout, so simulator/planner variation is not independently estimated.', '- No automatic claim of cross-task skill reuse or complete multi-round self-improvement. Only within-task feedback conditions were controlled.', '- Scoring, action budgets and native task physics were preserved. Native steps include terminal hold; completed API calls do not prove delivery/lift.', '- Preparation failures and the postprocessing repair are preserved separately. No task score was invented or changed.', '- Generated public-configuration layouts are not a claim of matching the entire official benchmark distribution.', '', 'Next decision: use actual common failure types in execution-feedback.json and primitive traces to choose one correction; freeze it within each task and rerun a matched control. Do not add interfaces, change model and enlarge candidate count together.', '', 'Evidence: protocol.json, qualification.json, parents/, interfaces/, requests/, responses/, candidates/, generation-snapshots/, each phase/native-campaign and analysis/, selection/, layouts/*/heldout/overlap-audit.json, asset-downloads/, preparation-failures/.']
(O/'REPORT.txt').write_text('\n'.join(lines)+'\n')
print(json.dumps(dict(state='completed',actual_native_episodes=result['actual_native_episodes'],videos=result['actual_videos'],api=api)))
