"""Append batch43 actual native executions, never logical selected views."""
import collections,csv,hashlib,json
from pathlib import Path
B=Path(__file__).resolve().parents[1];D=B/'derived'
R=B/'evidence/result';O=R/'43_system2_multitask/20261108_v1/native-validation'
def read(p):return json.loads(p.read_text())
def save(n,v):(D/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def table(n,rows):
 with (D/n).open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
s=read(O/'FINAL_SUMMARY.json');assert s['state']=='completed'
gate=read(B/'audit/batch43-archive-gate.json');assert gate['state']=='passed'
rows=read(D/'native_episodes_pre43.json');assert len(rows)==223
new=[]
for stage in s['stage_accounting']:
 phase=stage['phase'];episodes=read(O/phase/'analysis/episodes.json')
 assert len(episodes)==stage['native_episodes']
 for r in episodes:
  if not r['receipt']:
   verify=read(O/phase/'analysis/partial-evidence-verification.json');assert verify['state']=='verified_partial'
   rawrel=Path(r['raw_result']).relative_to('/mnt/data/physical-RSI/result/46_system2_multitask_20261108');rawp=O/rawrel;raw=read(rawp)
   detail=next(v for v in raw['details'].values() if v['layout_id']==r['layout_id'])
   assert detail['score']==r['score'] and detail['success']==r['success']
   new.append(dict(batch=43,phase=phase,task=r['task'],condition=r['condition'],layout_key=r['layout_id'],source_layout_id=r['layout_id'],score_100=r['score_100'],success=r['success'],layout_sha256=r['layout_sha256'],receipt_sha256='',source=str(rawp.relative_to(R))+'#layout_id='+str(r['layout_id']),evidence_role='natural_terminal_in_interrupted_cohort; original evaluator record; no complete-cohort framework receipt'))
   continue
  rel=Path(r['receipt']).relative_to('/mnt/data/physical-RSI/result/46_system2_multitask_20261108')
  p=O/rel;d=read(p)
  assert d['natural_terminal'] and d['native_exit_code']==0
  assert d['episode_score']==r['score'] and d['success']==r['success'] and d['layout_sha256']==r['layout_sha256']
  rawrel=Path(r['raw_result']).relative_to('/mnt/data/physical-RSI/result/46_system2_multitask_20261108');raw=read(O/rawrel)
  detail=raw['details'][str(r['layout_id'])]
  assert detail['score']==r['score'] and detail['success']==r['success']
  new.append(dict(batch=43,phase=phase,task=r['task'],condition=r['condition'],layout_key=r['layout_id'],source_layout_id=r['layout_id'],score_100=r['score_100'],success=r['success'],layout_sha256=r['layout_sha256'],receipt_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),source=str(p.relative_to(R)),evidence_role='preparation_native_smoke' if stage['role']=='preparation_not_formal' else 'new_native_execution'))
assert len(new)==s['actual_native_episodes']
assert len({r['source'] for r in new})==len(new),'Do not double count shared parent selected views'
rows+=new
save('native_episodes_all.json',rows);table('native_episodes_all.csv',rows)
groups=collections.defaultdict(list)
for r in rows:groups[r['batch'],r['phase'],r['task'],r['condition']].append(r)
cohorts=[]
for (batch,phase,task,cond),rs in sorted(groups.items()):
 cohorts.append(dict(batch=batch,phase=phase,task=task,condition=cond,native_executions=len(rs),full_successes=sum(x['success'] for x in rs),mean_score_100=sum(x['score_100'] for x in rs)/len(rs),scores_100=json.dumps([x['score_100'] for x in rs]),layout_sha256s=json.dumps([x['layout_sha256'] for x in rs]),scope='Within batch/phase; repeated layouts and different controllers must not be pooled as independent tasks'))
save('cohort_results_all.json',cohorts);table('cohort_results_all.csv',cohorts)
v=read(D/'recomputation_summary.json')
v.update(native_total=len(rows),native_batch43=len(new),batch43_formal_native_episodes=s['formal_native_episodes'],native_batches={str(k):sum(x['batch']==k for x in rows) for k in sorted({x['batch'] for x in rows})},batch43_native_pending=False,interpretation='The total is an execution ledger, not a comparable benchmark success-rate denominator. One batch43 preparation smoke is separately labelled.')
v['batch43_runtime_interrupted_episodes']=s.get('runtime_interrupted_episodes',0)
v['batch43_native_attempts']=s.get('actual_native_attempts',len(new))
v['interpretation']+=' native_total counts terminal-score executions only. Interrupted attempts are listed separately and not imputed as zero.'
save('interrupted_native_attempts_batch43.json',s.get('runtime_interruptions',[]))
if s.get('runtime_interruptions'):table('interrupted_native_attempts_batch43.csv',s['runtime_interruptions'])
save('recomputation_summary.json',v)
print(json.dumps(dict(actual_native=len(rows),new_batch43=len(new),cohorts=len(cohorts))))
