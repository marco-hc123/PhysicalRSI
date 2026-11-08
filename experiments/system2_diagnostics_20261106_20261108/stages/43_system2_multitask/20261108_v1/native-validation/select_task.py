"""Freeze task-specific selections before any heldout layout is generated."""
import datetime,json,hashlib
import sys
from pathlib import Path
O=Path(__file__).resolve().parent;task=sys.argv[1]
def read(p):return json.loads(p.read_text())
parent=next(x for x in read(O/(task+'-parent')/'analysis/summary.json')['summaries'] if x['condition']=='parent')
summaries=read(O/(task+'-candidates')/'analysis/summary.json')['summaries']
generation=read(O/(task+'-generation.json'))
sources={r['id']:r for r in generation['requests']}
base=dict(name='parent',source=f'parents/{task}.py',source_sha256=parent['source_sha256'])
entries=[base];views={};selection=[]
for condition in ['basic','execution_feedback']:
    group=[r for r in summaries if sources[r['condition']]['condition']==condition]
    eligible=[r for r in group if r['mean_score']>parent['mean_score']+1e-12 and r['complete_successes']>=parent['complete_successes']]
    eligible.sort(key=lambda r:(-r['mean_score'],-r['complete_successes'],r['source_sha256']))
    if eligible:
        best=eligible[0];name=best['condition'];row=dict(name=condition+'_selected',source=f'candidates/{name}/candidate.py',proposal=f'candidates/{name}/proposal.json',source_sha256=best['source_sha256'])
        existing=next((x for x in entries if x['source_sha256']==row['source_sha256']),None)
        if existing:views[condition]=existing['name']
        else:entries.append(row);views[condition]=row['name']
        selection.append(dict(condition=condition,decision='candidate_selected',candidate=name,development=best))
    else:
        views[condition]='parent';selection.append(dict(condition=condition,decision='retain_parent',admitted_evaluated=len(group),eligible=0))
result=dict(task=task,frozen_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),heldout_seen=False,parent_development=parent,decisions=selection,selected_views=views,unique_entries=entries,criterion='Strictly higher mean development score, no reduction in complete successes; ties retain parent. Candidate ties: mean, successes, source SHA256.',scope='One-generation-round task-specific feedback pilot; reused parent selections are not independent execution evidence.')
p=O/'selection'/f'{task}.json';p.parent.mkdir(exist_ok=True);assert not p.exists();p.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
