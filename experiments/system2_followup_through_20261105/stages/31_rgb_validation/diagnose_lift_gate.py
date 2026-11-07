"""Static and recorded-value analysis only; never execute or modify a candidate."""
import csv,hashlib,json,math,shutil
from pathlib import Path
R=Path('/mnt/data/physical-RSI');O=R/'result/31_rgb_supplement_20261105';A=O/'analysis'
d=json.loads((A/'matrix-analysis.json').read_text());campaign=json.loads((O/'native-campaign/campaign.json').read_text())
entry=next(e for e in campaign['entries'] if e['name']=='augmented_3')
candidate=Path(entry['harness']['root'])/'skills/code/classify_objects.py'
if not candidate.exists():
    candidate=Path(entry['origin']['source'])
source=candidate.read_text();assert hashlib.sha256(candidate.read_bytes()).hexdigest()==entry['origin']['source_sha256']
assert "o['p'][2] > z + 0.025" in source and 'if len(lifted) != 1:' in source
reader_paths=list((R/'models/skill-assets/implementations/code-skills').glob('**/rdj_v1_classify_objects/perception.py'))
assert len({hashlib.sha256(p.read_bytes()).hexdigest() for p in reader_paths})==1
reader=reader_paths[0];text=reader.read_text();assert '.765+HEIGHT.get(cat,.04)/2' in text
ref=A/'reference-contract';ref.mkdir(exist_ok=True)
shutil.copy2(reader,ref/'released_rgb_reader.py');shutil.copy2(candidate,ref/'augmented_3.py')
rows=[]
for actor in d['actors']:
    if actor['condition']!='augmented_3':continue
    p=O/actor['process_record'];proc=json.loads(p.read_text());calls=sorted(proc['calls'],key=lambda c:c['request']['id'])
    assert [c['request']['method'] for c in calls]==['scene','scene','gripper','approach','approach','gripper','approach','scene']
    initial=calls[1]['response']['value'];last=calls[-1]['response']['value'];xy=calls[3]['request']['kwargs']['position_m'][:2]
    matches=[(math.dist(obj['pose'][:2],xy),name,obj) for name,obj in initial['objects'].items() if not name.startswith('basket_')];matches.sort(key=lambda x:x[0])
    assert matches[0][0]<1e-8 and (len(matches)==1 or matches[1][0]>1e-5)
    _,name,obj=matches[0];category=name.rsplit('_',1)[0];x,y,z=obj['pose'][:3]
    same=[(name,o) for name,o in last['objects'].items() if name.rsplit('_',1)[0]==category]
    qualifying=[name for name,o in same if (o['pose'][0]-x)**2+(o['pose'][1]-y)**2<.0036 and o['pose'][2]>z+.025]
    assert not qualifying
    rows.append(dict(layout_id=actor['mapped_layout_id'],mapping_qualified=actor['mapping_qualified'],category=category,initial_detected_name=name,initial_z_m=z,required_z_strictly_above_m=z+.025,after_lift_same_category_count=len(same),after_lift_same_category_z_m=[o['pose'][2] for _,o in same],after_lift_same_category_xy_distance_m=[math.dist(o['pose'][:2],[x,y]) for _,o in same],predicate_matching_count=len(qualifying),last_scene_call_id=calls[-1]['request']['id'],last_observation_sequence=last['observation']['sequence'],completed_primitive_action_steps=actor['trusted_primitive_action_steps'],native_step_limit=1100,actor_returned_normally=actor['isolated_state']=='completed' and actor['isolated_returncode']==0,source_record=actor['process_record'],source_sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
assert len(rows)==5
result=dict(scope='Recorded-value predicate evaluation and source inspection only; no new API/native/CPU candidate execution',candidate_source=str(candidate),candidate_sha256=entry['origin']['source_sha256'],reader_copies=[str(p) for p in reader_paths],reader_sha256=hashlib.sha256(reader.read_bytes()).hexdigest(),reader_height_rule='z = .765 + category HEIGHT / 2; calibrated camera ray receives this plane height, not measured object elevation',rows=rows,conclusion='Candidate lift-verification assumption is incompatible with the current RGB scene height capability. All recorded lift predicates yield zero qualifying detections, consistent with the immediately following return branch. This does not establish whether a physical grasp actually succeeded.',limitations=['Branch location inferred from unchanged source and recorded values; no new branch instrumentation was injected.','Missing detections, occlusion and category-plane heights must be separated.','This is specific to this saved candidate and pinned observation adapter, not a universal PhysicalRSI core defect.'])
(A/'lift-gate-diagnosis.json').write_text(json.dumps(result,indent=2)+'\n')
with (A/'lift-gate-diagnosis.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader()
    for row in rows:w.writerow({k:json.dumps(v) if isinstance(v,(dict,list)) else v for k,v in row.items()})
mapping=json.loads((A/'reference-path-map.json').read_text()) if (A/'reference-path-map.json').exists() else []
for source,target in [(reader,ref/'released_rgb_reader.py'),(candidate,ref/'augmented_3.py')]:
    item=dict(original=str(source),archived=str(target.relative_to(O)),sha256=hashlib.sha256(source.read_bytes()).hexdigest())
    if item not in mapping:mapping.append(item)
(A/'reference-path-map.json').write_text(json.dumps(mapping,indent=2)+'\n')
print(json.dumps({'layouts':len(rows),'predicate_matches':[x['predicate_matching_count'] for x in rows],'detected_after_lift':[x['after_lift_same_category_count'] for x in rows],'native_reruns':0}))
