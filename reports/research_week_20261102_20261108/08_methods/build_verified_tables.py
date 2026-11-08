"""Create compact, reproducible reporting tables from original receipts/usage."""
import csv, hashlib, json, re
from pathlib import Path
B=Path(__file__).resolve().parents[1];R=B/'evidence/result';O=B/'derived';O.mkdir(exist_ok=True)
def read(p):return json.loads(p.read_text())
def save(n,d):(O/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def table(n,rows):
 with (O/n).open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def root(n):return next(R.glob(str(n)+'*'))
rows=[]
audit=read(B/'audit/native-receipt-audit.json')
assert len(audit['episodes'])==203 and not audit['issues']
for r in audit['episodes']:
 assert r['valid_terminal'] and r['score_agreement'] is True
 p=r['path'];batch=int(p[:2]);parts=Path(p).parts
 m=re.search(r'/runs/([^/]+)/attempt-',p)
 condition=m.group(1) if m else ('released_first_basket_cycle' if batch==41 else 'released_complete_controller' if batch==37 else 'unknown')
 phase='development'
 if batch==32:phase='retreat_destination' if 'retreat-followup' in parts else 'lift_guard'
 if batch==42:phase=parts[parts.index('native-validation')+1]
 local=int(r['layout_key']);source_layout=4 if batch==35 and local==2 else local
 rows.append(dict(batch=batch,phase=phase,task=r['task'],condition=condition,layout_key=local,source_layout_id=source_layout,score_100=100*float(r['score']),success=bool(r['success']),layout_sha256=r['layout_sha256'],receipt_sha256=r['sha256'],source=p,evidence_role='new_native_execution'))
for p in sorted(root(24).glob('*/evidence/*/native-result.json')):
 d=read(p);task='classify_objects_by_language' if 'by_language' in str(p) else 'classify_objects'
 assert d['eval_time']==len(d['details'])==5
 assert abs(d['score']-sum(x['score'] for x in d['details'].values())/5*100)<1e-8
 for k,v in d['details'].items():rows.append(dict(batch=24,phase='model_swap',task=task,condition='gpt61sol_medium_agent',layout_key=int(k),source_layout_id=v['layout_id'],score_100=v['score']*100,success=v['success'],layout_sha256=None,receipt_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),source=str(p.relative_to(R)),evidence_role='new_native_execution'))
for p in sorted(root(25).glob('*/native-receipts/batch-*/0.json')):
 d=read(p);assert d['state']=='completed' and d['native_exit_code']==0 and d['natural_terminal']
 cond='pi05_parent' if d['expert']=='pi05' else 'gpt_candidate'
 rows.append(dict(batch=25,phase='model_swap_validation',task=d['task'],condition=cond,layout_key=p.parent.name,source_layout_id=None,score_100=100*float(d['episode_score']),success=d['success'],layout_sha256=d['layout_sha256'],receipt_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),source=str(p.relative_to(R)),evidence_role='new_native_execution'))
assert len(rows)==223
save('native_episodes_pre43.json',rows);table('native_episodes_pre43.csv',rows)
groups={}
for r in rows:groups.setdefault((r['batch'],r['phase'],r['task'],r['condition']),[]).append(r)
cohorts=[]
for (batch,phase,task,condition),rs in sorted(groups.items()):
 cohorts.append(dict(batch=batch,phase=phase,task=task,condition=condition,native_executions=len(rs),full_successes=sum(r['success'] for r in rs),mean_score_100=sum(r['score_100'] for r in rs)/len(rs),scores_100=json.dumps([r['score_100'] for r in rs]),layout_sha256s=json.dumps([r['layout_sha256'] for r in rs]),scope='Within batch/phase; repeated layouts and different controllers must not be pooled as independent tasks'))
save('cohort_results_pre43.json',cohorts);table('cohort_results_pre43.csv',cohorts)

sources=[(24,next(root(24).glob('*/budget-ledger.json'))),(25,next(root(25).glob('*/budget-ledger.json'))),(29,next(root(29).glob('*/ledger.json'))),(33,next(root(33).glob('*/ledger.json'))),(42,next(root(42).glob('*/native-validation/ledger.json')))]
live=B.parent/'server_preparation/multitask_system2_20261108/ledger.json'
if live.exists():sources.append((43,live))
api=[]
for batch,p in sources:
 d=read(p);entries=d['attempts'] if isinstance(d,dict) else d
 for r in entries:
  u=r['usage'];inp=u['prompt_tokens'];out=u['completion_tokens'];det=u.get('prompt_tokens_details') or {};cached=det.get('cached_tokens',0);write=det.get('cache_write_tokens',0);reason=(u.get('completion_tokens_details') or {}).get('reasoning_tokens',0)
  assert inp+out==u['total_tokens'] and 0<=cached+write<=inp and 0<=reason<=out
  name=r.get('id',r.get('request_id'));group=r.get('arm',r.get('batch',''))
  if batch==43:group='execution_feedback' if 'execution_feedback' in name else 'basic'
  task='general_pickup' if 'general_pickup' in name else 'classify_objects_by_language' if 'by_language' in name else 'classify_objects'
  role='API_preflight' if name.startswith('smoke') else 'System1_skill_selection' if batch==24 else 'System2_candidate_generation'
  if role=='API_preflight':task='none'
  reviewed=((inp-cached-write)*2+cached*.1+write*2.5+out*10)/1e6
  original=r.get('estimated_standard_usd',r.get('estimated_cost_lower_usd'))
  api.append(dict(batch=batch,id=name,role=role,task=task,condition=group,reasoning_effort='high' if batch>=42 else 'medium',http_status=r['http_status'],input_tokens=inp,output_tokens=out,total_tokens=inp+out,cached_input_subset=cached,cache_write_input_subset=write,reasoning_output_subset=reason,api_seconds=r.get('seconds'),recorded_estimate_usd=original,recomputed_estimate_usd=reviewed,estimate_difference=None if original is None else reviewed-original,source=str(p.relative_to(R)) if p.is_relative_to(R) else 'batch43/ledger.json'))
save('api_requests.json',api);table('api_requests.csv',api)
costgroups={}
for r in api:costgroups.setdefault((r['batch'],r['role'],r['task'],r['condition']),[]).append(r)
costs=[]
for (batch,role,task,condition),rs in costgroups.items():
 costs.append(dict(batch=batch,role=role,task=task,condition=condition,requests=len(rs),mean_input_tokens=sum(x['input_tokens'] for x in rs)/len(rs),mean_output_tokens=sum(x['output_tokens'] for x in rs)/len(rs),input_tokens=sum(x['input_tokens'] for x in rs),output_tokens=sum(x['output_tokens'] for x in rs),total_tokens=sum(x['total_tokens'] for x in rs),cached_input_subset=sum(x['cached_input_subset'] for x in rs),cache_write_input_subset=sum(x['cache_write_input_subset'] for x in rs),reasoning_output_subset=sum(x['reasoning_output_subset'] for x in rs),api_seconds=sum(x['api_seconds'] for x in rs),recomputed_estimate_usd=sum(x['recomputed_estimate_usd'] for x in rs)))
save('api_by_condition.json',costs);table('api_by_condition.csv',costs)
save('recomputation_summary.json',dict(native_pre43=len(rows),native_pre43_full_successes=sum(r['success'] for r in rows),native_batches={str(i):sum(r['batch']==i for r in rows) for i in sorted({r['batch'] for r in rows})},api_requests=len(api),api_http200=sum(r['http_status']==200 for r in api),total_input_tokens=sum(r['input_tokens'] for r in api),total_output_tokens=sum(r['output_tokens'] for r in api),recomputed_estimate_usd=sum(r['recomputed_estimate_usd'] for r in api),pricing_basis='Recompute using the frozen campaign accounting formula: $2/M uncached input, $0.1/M cache read, $2.5/M cache write, $10/M output. This is a usage-based estimate, not invoice payment. Historical ledger differences retained.',batch43_native_pending=True,important='Scores and cost intervals must be read by experimental condition. The pooled full-success count has no comparable benchmark denominator.'))
print(json.dumps(read(O/'recomputation_summary.json'),ensure_ascii=False))
