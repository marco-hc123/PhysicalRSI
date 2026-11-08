"""Recalculate native metrics from the verified project archive on lab CPU only."""
import csv,datetime,hashlib,json
from pathlib import Path
L=Path(__file__).resolve().parent;D=L/'native-validation';A=L/'archive-analysis';A.mkdir(exist_ok=True)
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
archive=read(D/'migration/ARCHIVE_VERIFIED.json');assert archive['state']=='verified'
summary=read(D/'FINAL_SUMMARY.json');rows=[];evidence=[];phase_counts={};all_hashes={}
for phase in summary['completed_native_phases']:
 P=D/phase;m=read(P/'analysis/matrix-analysis.json');v=read(P/'analysis/independent-validation.json');assert v['state']=='passed'
 phase_counts[phase]=0;all_hashes[phase]=set()
 for item in m['episodes']:
  receipt=P/item['receipt'];record=read(receipt);raw=read(P/item['result_file']);expected=next(x for x in v['receipt_checks'] if x['condition']==item['condition'] and x['layout_id']==item['layout_id'])
  assert sha(receipt)==expected['receipt_sha256']
  score=raw['details'][str(item['layout_id'])]['score'];success=raw['details'][str(item['layout_id'])]['success']
  assert score==record['episode_score']==item['normalized_score'] and success==record['success']==item['success']
  assert record['natural_terminal'] and record['native_exit_code']==0
  assert record['layout_sha256']==item['layout_sha256']
  rows.append(dict(phase=phase,condition=item['condition'],layout_id=item['layout_id'],score_100=score*100,success=success,layout_sha256=item['layout_sha256'],receipt=str(receipt.relative_to(D)),receipt_sha256=sha(receipt)))
  phase_counts[phase]+=1;all_hashes[phase].add(item['layout_sha256'])
 assert phase_counts[phase]==v['valid_native_cases']==m['qualified_cases']
 evidence.append(dict(phase=phase,matrix_sha256=sha(P/'analysis/matrix-analysis.json'),validation_sha256=sha(P/'analysis/independent-validation.json')))
assert sum(phase_counts.values())==summary['actual_native_episodes']==archive['native_cases']
assert not all_hashes['heldout'].intersection(set().union(*(x for p,x in all_hashes.items() if p!='heldout')))
groups=[]
for phase in summary['completed_native_phases']:
 for condition in sorted({x['condition'] for x in rows if x['phase']==phase}):
  data=[x for x in rows if x['phase']==phase and x['condition']==condition]
  groups.append(dict(phase=phase,condition=condition,n=len(data),successes=sum(x['success'] for x in data),mean_score_100=sum(x['score_100'] for x in data)/len(data),scores_100=[x['score_100'] for x in sorted(data,key=lambda x:x['layout_id'])]))
for name,data in [('verified-episodes.csv',rows),('verified-cohorts.csv',groups)]:
 with (A/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows({k:json.dumps(v) if isinstance(v,list) else v for k,v in x.items()} for x in data)
ledger=read(D/'ledger.json');estimated=sum(x.get('estimated_standard_usd',0) for x in ledger)
assert abs(estimated-summary['estimated_new_api_usd'])<1e-9
out=dict(state='verified',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),native_episodes=len(rows),phase_counts=phase_counts,groups=groups,paid_api_requests=len(ledger),estimated_api_usd=estimated,heldout_disjoint_from_development=True,lab_gpu_used=False,api_calls_during_reanalysis=0,source_archive_manifest=archive['manifest_sha256'],evidence=evidence,scope='Lab CPU recalculation from archived raw native result files and qualified receipt hashes. No rerun, no new task episodes, no System2 selection from heldout results.')
(A/'verified-summary.json').write_text(json.dumps(out,indent=2)+'\n')
text=['PhysicalRSI search and execution-control campaign: lab archive recalculation','',out['scope'],'','Actual native episodes: '+str(len(rows)),'Original videos: '+str(summary['original_videos']),'Paid generation requests: '+str(len(ledger)),'Estimated new API charge USD: '+str(estimated),'', 'Phase / strategy / n / full successes / native scores out of100']
text += [f"{x['phase']} / {x['condition']} / {x['n']} / {x['successes']} / {x['scores_100']}" for x in groups]
text += ['', 'Interpretation and limitations are in REPORT.txt and FINAL_SUMMARY.json.','Evidence reuse across identical heldout strategies is not an additional native run.','The fixed parent is a code candidate, not pi05. Manual target controls are separate from generated System2 proposals.']
(A/'ARCHIVE_ANALYSIS.txt').write_text('\n'.join(text)+'\n');print(json.dumps({k:out[k] for k in ['state','native_episodes','paid_api_requests','estimated_api_usd','lab_gpu_used']}))
