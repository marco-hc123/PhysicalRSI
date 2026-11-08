"""Verify native scores against raw evaluator records; preserve structured feedback."""
import collections,csv,json,sys
from pathlib import Path
O=Path(__file__).resolve().parent;D=O/'analysis';D.mkdir(exist_ok=True)
I=Path('/mnt/data/physical-RSI/result/25_system2_integration_20261030T050100Z/integration-sources')
sys.path[:0]=[str(I),str(I/'framework-validation-v3')]
from PhysicalRSI_core.infra.storage import read_json,atomic_json,file_digest
from PhysicalRSI_baselines.robodojo.evidence import episode_receipt
C=O/'native-campaign';campaign=read_json(C/'campaign.json');rows=[];summaries=[];feedback=[];videos=[]
for entry in campaign['entries']:
    base=C/'runs'/entry['name'];done=read_json(base/'completed.json');run=Path(done['output'])
    raw_files=list(run.rglob('_result.json'));assert len(raw_files)==1
    raw=read_json(raw_files[0]);observed=read_json(run/'native/run/observed.json')
    assert raw['eval_time']==len(campaign['cases']) and not observed['failures']
    scores=[];successes=[]
    for i,case in enumerate(campaign['cases']):
        p=run/'episodes'/f'{i}.json'
        rec=episode_receipt(p,directory=run,task=case['task'],split=case['split'],layout_sha256=case['layout_sha256'],expert=entry['expert'],harness_sha256=entry['harness_sha256'])
        raw_receipt=read_json(p)
        assert raw_receipt['native_exit_code']==0 and raw_receipt['natural_terminal']
        assert rec['success']==raw['details'][str(i)]['success']
        assert abs(rec['episode_score']-raw['details'][str(i)]['score'])<1e-9
        score=rec['episode_score'];assert 0<=score<=1
        scores.append(score);successes.append(rec['success'])
        rows.append(dict(task=case['task'],phase=O.name,condition=entry['name'],layout_id=i,layout_sha256=case['layout_sha256'],score=score,score_100=100*score,success=rec['success'],native_action_count=rec['diagnostics']['action_count'],step_limit=rec['diagnostics']['step_limit'],receipt=str(p),raw_result=str(raw_files[0]),api_calls=0))
    group=[]
    for p in sorted((run/'model/expert').glob('*/0/policy/processes/isolated/process.json')):
        data=read_json(p);calls=data.get('calls',[])
        ids=[r['request']['id'] for r in calls];assert ids==list(range(len(ids)))
        assert all(r['request']['id']==r['response']['id'] for r in calls if 'response' in r)
        counts=collections.Counter(r['request']['method'] for r in calls)
        failures=[r for r in calls if r.get('state')!='completed' or r.get('response',{}).get('value',{}).get('primitive_error')]
        scene=next((r['response']['value'] for r in calls if r['request']['method']=='scene' and 'response' in r),None)
        compact=[{k:r.get(k) for k in ['request','response','state','error']} for r in calls[-8:]]
        group.append(dict(file=str(p),process_state=data.get('state'),exit_code=data.get('exit_code'),calls=len(calls),method_counts=dict(counts),failed_or_rejected_calls=len(failures),first_scene=scene,last_calls=compact))
    for p in sorted(run.rglob('*.mp4')):videos.append(dict(condition=entry['name'],path=str(p),bytes=p.stat().st_size,sha256=file_digest(p)))
    assert len(list(run.rglob('*.mp4')))==3*len(campaign['cases'])
    summaries.append(dict(task=campaign['cases'][0]['task'],condition=entry['name'],n=len(scores),scores=scores,mean_score=sum(scores)/len(scores),complete_successes=sum(successes),source_sha256=entry['source_sha256'],expert=entry['expert'],actors=len(group),failed_or_rejected_calls=sum(r['failed_or_rejected_calls'] for r in group),wall_seconds=read_json(base/'timing.json')['start_to_valid_receipts_s']))
    feedback.append(dict(condition=entry['name'],scores=scores,complete_successes=sum(successes),actors=group,notice='Actor UUIDs retained; no guessed actor-to-layout mapping. Native score order follows case manifest. A rejected call is not automatically a failed episode.'))
atomic_json(D/'summary.json',dict(state='verified',summaries=summaries,valid_native_episodes=len(rows),videos=len(videos),all_raw_receipts_consistent=True,score_scale='0..1, displayed x100'))
atomic_json(D/'episodes.json',rows);atomic_json(D/'execution-feedback.json',feedback);atomic_json(D/'videos.json',videos)
if rows:
    with (D/'episodes.csv').open('w',newline='') as stream:
        w=csv.DictWriter(stream,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print(json.dumps(dict(valid_native_episodes=len(rows),summaries=summaries)))
