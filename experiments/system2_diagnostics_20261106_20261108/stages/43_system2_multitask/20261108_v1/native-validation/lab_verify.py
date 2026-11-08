"""CPU-only recalculation of the copied native receipts and final comparisons."""
import datetime,hashlib,json
from pathlib import Path
O=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
manifest=read(O/'migration/source-manifest.json');mapping={r['path']:r for r in manifest['files']}
assert read(O/'migration/ARCHIVE_VERIFIED.json')['state']=='verified'
summary=read(O/'FINAL_SUMMARY.json');source=Path(manifest['source_root'])
def mapped(name):
    p=Path(name);return O/p.relative_to(source)
checks=[];total=0
for stage in summary['stage_accounting']:
    root=O/stage['phase'];campaign=read(root/'native-campaign/campaign.json');observed=[]
    if read(root/'analysis/summary.json')['state']=='verified_partial':
        v=read(root/'analysis/partial-evidence-verification.json');assert v['state']=='verified_partial' and v['retry_performed'] is False
        for src in v['source_hashes']:
            assert hashlib.sha256((O/src['path']).read_bytes()).hexdigest()==src['sha256']
        run=root/'native-campaign/runs/parent/attempt-001';raw=read(next(run.rglob('_result.json')))
        original=read(run/'native/run/observed.json');assert len(original['failures'])==1 and raw['eval_time']==4
        byid={int(x['layout_id']):x for x in raw['details'].values()}
        scores=[None]*len(campaign['cases']);successes=[]
        for r in read(root/'analysis/episodes.json'):
            if r['condition']!='parent':continue
            i=r['layout_id'];assert r['score']==byid[i]['score'] and r['success']==byid[i]['success']
            assert r['layout_sha256']==campaign['cases'][i]['layout_sha256'];scores[i]=r['score'];successes.append(r['success'])
        frozen=read(root/'analysis/summary.json')['summaries'][0];assert scores==frozen['scores'] and len(successes)==frozen['n']==4
        valid=[x for x in scores if x is not None];assert abs(sum(valid)/len(valid)-frozen['mean_score'])<1e-12
        checks.append(dict(phase=stage['phase'],condition='parent',scores=scores,successes=sum(successes),native_completed=4,native_interrupted=1));total+=4
    for entry in campaign['entries']:
        if read(root/'analysis/summary.json')['state']=='verified_partial' and entry['name']=='parent':continue
        run=mapped(read(root/'native-campaign/runs'/entry['name']/'completed.json')['output'])
        rawfiles=list(run.rglob('_result.json'));assert len(rawfiles)==1
        raw=read(rawfiles[0]);assert raw['eval_time']==len(campaign['cases'])
        scores=[];successes=[]
        for i,case in enumerate(campaign['cases']):
            p=run/'episodes'/f'{i}.json';r=read(p)
            assert r['native_exit_code']==0 and r['natural_terminal'] and r['task']==case['task']
            assert r['layout_sha256']==case['layout_sha256'] and r['harness_sha256']==entry['harness_sha256']
            assert r['success']==raw['details'][str(i)]['success']
            assert abs(r['episode_score']-raw['details'][str(i)]['score'])<1e-12
            scores.append(r['episode_score']);successes.append(r['success'])
        frozen=next(r for r in read(root/'analysis/summary.json')['summaries'] if r['condition']==entry['name'])
        assert frozen['scores']==scores and frozen['complete_successes']==sum(successes)
        assert abs(frozen['mean_score']-sum(scores)/len(scores))<1e-12
        checks.append(dict(phase=stage['phase'],condition=entry['name'],scores=scores,successes=sum(successes)));total+=len(scores)
assert total==summary['actual_native_episodes']==manifest['native_cases']
for task,r in summary['tasks'].items():
    base=r['heldout_parent']['scores']
    for condition,view in r['heldout_selected_views'].items():
        delta=[a-b if a is not None and b is not None else None for a,b in zip(view['scores'],base)];valid=[x for x in delta if x is not None]
        assert delta==view['paired_score_differences'] and abs(sum(valid)/len(valid)-view['mean_difference'])<1e-12
out=dict(state='passed',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),host='lab_archive',gpu_used=False,environment_modified=False,verified_native_episodes=total,runtime_interrupted_episodes=summary.get('runtime_interrupted_episodes',0),verified_cohorts=len(checks),checks=checks,scope='Independent CPU recalculation from raw copied native receipts/evaluator results and paired comparisons; partial heldout has no forged framework receipts and its missing terminal score stays null. Full payload SHA256 checked during archive transfer.')
(O/'migration/LAB_RECALCULATION.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='checks'}))
