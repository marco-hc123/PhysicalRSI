"""Prespecified lexicographic development selection, incumbent wins ties."""
import json,sys,datetime,hashlib
from pathlib import Path
O=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def metric(rows):return (sum(x['success'] for x in rows),sum(x['normalized_score'] for x in rows)/len(rows))
def choose(rows,names,incumbent):
 current=incumbent;trace=[]
 for name in names:
  group=[x for x in rows if x['condition']==name]
  if not group:trace.append(dict(candidate=name,state='not_admitted_or_not_executed'));continue
  parent=[x for x in rows if x['condition']==current];assert len(group)==len(parent)==5
  better=metric(group)>metric(parent);trace.append(dict(candidate=name,metric=metric(group),incumbent=current,incumbent_metric=metric(parent),selected=better))
  if better:current=name
 return dict(selected=current,metric=metric([x for x in rows if x['condition']==current]),trace=trace)
if __name__=='__main__':
 phase=sys.argv[1]
 if phase=='sampling':
  sources=[O/'parent/analysis/matrix-analysis.json',O/'sampling/analysis/matrix-analysis.json'];rows=sum([read(p)['episodes'] for p in sources],[])
  result=dict(budget1=choose(rows,['sample_01'],'fixed_parent'),budget5=choose(rows,[f'sample_{i:02}' for i in range(1,6)],'fixed_parent'))
 else:raise ValueError('Only initial development selection is defined here')
 result.update(phase=phase,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),heldout_seen=False,rule='Full-success count then mean native score; retain incumbent on tie; increasing generation order',sources=[dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sources],scope='One nested candidate pool, not replicated search budgets; development choice is subject to selection bias and needs independent validation.')
 p=O/'sampling-selection.json';assert not p.exists();p.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
