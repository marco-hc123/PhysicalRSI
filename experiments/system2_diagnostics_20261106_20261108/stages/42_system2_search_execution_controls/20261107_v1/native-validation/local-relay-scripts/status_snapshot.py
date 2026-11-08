"""Compact read-only campaign status; never starts or stops experiments."""
import json,sys
from remote_ops import C,CLOUD,call
phase=sys.argv[1] if len(sys.argv)>1 else 'sampling'
assert phase in ['parent','sampling','repair','rebind','round2','heldout']
print(call(CLOUD,f'''import json,datetime,subprocess
from pathlib import Path
r=Path({C!r});p=r/{phase!r};out=dict(utc=str(datetime.datetime.now(datetime.timezone.utc)),phase={phase!r})
for key,f in [('controller',r/({phase!r}+'-status.json')),('native',p/'native-campaign/status.json')]:
 if f.exists():out[key]=json.loads(f.read_text())
condition=out.get('native',{{}}).get('condition')
if condition:
 for f in (p/'sim-diagnostics'/condition).glob('simulator-*.jsonl'):
  with f.open('rb') as s:s.seek(max(0,f.stat().st_size-65536));lines=s.read().splitlines()
  for line in reversed(lines):
   try:d=json.loads(line)
   except ValueError:continue
   if d.get('event')=='snapshot':out['last_snapshot']=dict(layout=d.get('layout_seed'),step=d.get('native_action_count'));break
out['completed_scores']={{}}
receipts=list((p/'native-campaign/runs').glob('*/attempt-*/episodes/*.json'))
if 'native' in out:
 out['native']['cohort_accounted_cases']=out['native'].get('completed_cases')
 out['native']['completed_cases']=len(receipts)
 out['native']['completion_count_scope']='Written per-episode receipts; final independent validation remains pending until phase completion'
for f in sorted((p/'native-campaign/runs').glob('*/completed.json')):
 folder=Path(json.loads(f.read_text())['output']);episodes=[json.loads(x.read_text()) for x in sorted((folder/'episodes').glob('*.json'))]
 out['completed_scores'][f.parent.name]=dict(scores=[x['episode_score']*100 for x in episodes],successes=sum(x['success'] for x in episodes))
print(json.dumps(out))
''',True))
