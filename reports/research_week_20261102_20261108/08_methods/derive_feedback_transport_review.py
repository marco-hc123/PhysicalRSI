"""Posthoc compact trace review; no new simulation or strategy change."""
from pathlib import Path
import collections,csv,hashlib,json,math
B=Path(__file__).resolve().parents[1];O=B/'evidence/result/43_system2_multitask/20261108_v1/native-validation';D=B/'audit/multitask'
def read(p):return json.loads(p.read_text())
f=read(O/'classify_objects-candidates/analysis/execution-feedback.json');a=read(D/'mechanism-audit.json');lookup={x['actor_uuid']:x for x in a['actors']};rows=[]
for group in f:
 if 'execution_feedback' not in group['condition']:continue
 code=O/'candidates'/group['condition']/'candidate.py';source=code.read_text()
 assert 'if not move(arm, [bx, by,' in source
 for actor in group['actors']:
  uuid=Path(actor['file']).parents[4].name;calls=actor['last_calls'];assert actor['calls']==len(calls)==8
  app=[r for r in calls if r['request']['method']=='approach'];assert len(app)==4
  assert all(r['state']=='completed' and not r.get('response',{}).get('value',{}).get('primitive_error') for r in app[:3])
  last=app[-1];assert last['state']=='completed' and last['response']['value']['primitive_error']=='no_collision_free_path'
  target=last['request']['kwargs']['position_m'];assert abs(target[2]-1.06)<1e-12
  scenes=[r['response']['value'] for r in calls if r['request']['method']=='scene'];scene=scenes[-1]
  baskets=[v['pose'] for k,v in scene['objects'].items() if k.startswith('basket_')]
  distance=min(math.dist(target[:2],v[:2]) for v in baskets);assert distance<1e-10
  m=lookup[uuid];assert m['observed_stop_class']=='program_returned_after_explicit_rejection' and actor['process_state']=='completed'
  rows.append(dict(condition=group['condition'],layout_id=m['layout_id'],actor_uuid=uuid,score_100=100*m['native_score'],approach_calls=4,first_three_calls_returned_without_explicit_rejection=True,last_target=target,last_target_matches_visible_basket_xy=True,last_rejection='no_collision_free_path',native_success=False,process_state='completed',source_file=actor['file'],candidate_source=str(code.relative_to(O)),candidate_sha256=hashlib.sha256(code.read_bytes()).hexdigest()))
assert len(rows)==15
pick=[r for r in a['actors'] if r['phase']=='general_pickup-candidates'];assert len(pick)==30
out=dict(state='verified_posthoc',classification_feedback_episodes=15,classification_feedback_pattern_count=15,classification_feedback_records=rows,pickup_candidate_stop_counts=dict(collections.Counter(r['observed_stop_class'] for r in pick)),scope='Read-only posthoc localization from copied original RPC responses, scene values, native outcomes and candidate source. Planning rejection is an observed status, not proof of collision or unavoidable geometric infeasibility. First three returned approaches do not establish grasp attachment.',paid_api_requests=0,new_native_episodes=0)
(D/'feedback-transport-detail.json').write_text(json.dumps(out,indent=2)+'\n')
with (D/'feedback-transport-detail.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print(json.dumps({k:v for k,v in out.items() if k!='classification_feedback_records'}))
