"""Preserve an interrupted heldout cohort without imputation or retries.

This creates an analysis verification, not forged framework episode receipts.
The original native/status/log files stay unchanged. Only phase accounting and
task-controller completion status are updated to explicitly partial completion.
"""
import collections,csv,datetime,hashlib,json,os
from pathlib import Path
O=Path(__file__).resolve().parent;P=O/'classify_objects-heldout';D=P/'analysis'
assert not D.exists(),'Do not overwrite an existing heldout analysis'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
campaign=read(P/'native-campaign/campaign.json');assert len(campaign['entries'])==1 and campaign['entries'][0]['name']=='parent'
entry=campaign['entries'][0];run=P/'native-campaign/runs/parent/attempt-001'
obsfile=run/'native/run/observed.json';obs=read(obsfile)
assert len(obs['failures'])==1 and len(obs['outcomes'])==4
rawfile=next(run.rglob('_result.json'));raw=read(rawfile);assert raw['eval_time']==4
details={int(v['layout_id']):v for v in raw['details'].values()};assert set(details)=={0,2,3,4}
observed={int(v['layout_id']):v for v in obs['outcomes']};assert set(observed)==set(details)
cases=campaign['cases'];assert len(cases)==5
rows=[];sources=[obsfile,rawfile,P/'native-campaign/campaign.json'];scores=[None]*5
for i,v in sorted(observed.items()):
 case=cases[i];assert v['natural_terminal'] and v['action_count']==v['step_limit']==1100
 assert details[i]['score']==v['episode_score'] and details[i]['success']==v['success']
 scores[i]=v['episode_score']
 rows.append(dict(task=case['task'],phase=P.name,condition='parent',layout_id=i,layout_sha256=case['layout_sha256'],score=v['episode_score'],score_100=100*v['episode_score'],success=v['success'],native_action_count=v['action_count'],step_limit=v['step_limit'],receipt='',raw_result=str(rawfile),api_calls=0))
assert abs(raw['score']-sum(x for x in scores if x is not None)/4*100)<1e-9
groups=[];failed=[]
for p in sorted((run/'model/expert').glob('*/0/policy/processes/isolated/process.json')):
 d=read(p);calls=d.get('calls',[]);assert [x['request']['id'] for x in calls]==list(range(len(calls)))
 groups.append(dict(file=str(p),process_state=d.get('state'),error=d.get('error'),calls=len(calls),method_counts=dict(collections.Counter(x['request']['method'] for x in calls)),last_calls=calls[-3:]))
 sources.append(p)
 if d.get('state')=='failed':failed.append((p,d))
assert len(groups)==5 and len(failed)==1
p,d=failed[0];assert 'Observed robot diverged from planned trajectory' in d['error'];assert len(d['calls'])==43 and d['calls'][-1]['state']=='started'
actor=p.parents[4].name;trace=P/'backend-traces/parent'/actor/'0/primitive-events.jsonl';events=[json.loads(x) for x in trace.read_text().splitlines()];sources.append(trace)
end=[x for x in events if x.get('event')=='exception'][-1];assert 'Observed robot diverged' in end['error']
snapshots=[]
for p in sorted((P/'sim-diagnostics/parent').glob('*.jsonl')):
 sources.append(p);snapshots += [r for r in (json.loads(x) for x in p.read_text().splitlines()) if r.get('event')=='snapshot']
rs=[r for r in snapshots if r['layout_seed']==1];assert rs and max(r['native_action_count'] for r in rs)==214
assert min(r['monotonic_ns'] for r in rs)<=next(e for e in events if e['event']=='begin')['monotonic_ns']<=end['monotonic_ns']
videos=[dict(condition='parent',path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(run.rglob('*.mp4'))];assert len(videos)==12
status=read(P/'native-campaign/status.json');assert status['state']=='stopped_for_diagnosis'
summary=dict(state='verified_partial',valid_native_episodes=4,attempted_native_episodes=5,runtime_interrupted_episodes=1,videos=12,all_raw_receipts_consistent=False,raw_evaluator_and_observer_consistent=True,score_scale='0..1; null means missing native terminal score, never zero',summaries=[dict(task='classify_objects',condition='parent',n=4,planned_n=5,scores=scores,mean_score=sum(x for x in scores if x is not None)/4,complete_successes=0,runtime_interrupted=1,source_sha256=entry['source_sha256'],expert=entry['expert'],actors=5,failed_or_rejected_calls=None,wall_seconds=status['elapsed_s'],wall_scope='Entire attempted cohort controller wall time including partial episode/preflight; not start_to_valid_receipts',scope='Four natural terminals and one trajectory-tracking interruption; no complete-cohort framework receipts exist. Mean conditions on completed layouts; no full5-layout acceptance claim.')])
verification=dict(state='verified_partial',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),completed_layout_ids=[0,2,3,4],interrupted_layout_id=1,planned_layouts=5,valid_native_episodes=4,interrupted_attempts=1,interrupted_action_count=214,interrupted_actor_uuid=actor,error=d['error'],source_hashes=[dict(path=str(p.relative_to(O)),sha256=sha(p)) for p in sources],policy_zero_score=False,retry_performed=False,source_policy_modified=False,native_runtime_modified=False,interpretation='Actual execution tracking guard interrupted one layout. Not an infrastructure outage; physical root cause not uniquely established. Preserve native score as unknown, keep other4 natural outcomes, no best-of retry and no heldout tuning.')
save(D/'summary.json',summary);save(D/'episodes.json',rows);save(D/'videos.json',videos)
save(D/'execution-feedback.json',[dict(condition='parent',scores=scores,complete_successes=0,actors=groups,notice='Partial heldout, missing layout1 terminal score; failed actor error is a real execution guard, not a success-triggered cancellation.')])
save(D/'partial-evidence-verification.json',verification)
save(D/'interrupted-attempts.json',[dict(task='classify_objects',phase=P.name,condition='parent',layout_id=1,layout_sha256=cases[1]['layout_sha256'],score=None,success=None,natural_terminal=False,native_action_count=214,error=d['error'],actor_uuid=actor,evidence_status='runtime_interrupted_missing_native_terminal_score',verification=str(D/'partial-evidence-verification.json'))])
with (D/'episodes.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
review=O/'runtime-failure-review'
for name in ['classify_objects-finish-status.json','classify_objects-heldout-status.json']:
 original=O/name;copy=review/('original-'+name);assert not copy.exists();copy.write_bytes(original.read_bytes())
 save(original,dict(state='completed_with_runtime_failure',task='classify_objects',phase=P.name,pid=os.getpid(),utc=verification['utc'],native_completed=4,native_interrupted=1,verification=str(D/'partial-evidence-verification.json'),no_retry=True))
save(review/'classification-partial-resolution.json',verification)
print(json.dumps(dict(state='verified_partial',scores=scores,completed=4,interrupted=1,no_retry=True)))
