"""Audit actual candidate input coverage; ground truth is analysis-only."""
from pathlib import Path
from collections import Counter
import json,csv,hashlib
L=Path(__file__).resolve().parent;N=L/'native-validation'
def read(p):return json.loads(p.read_text())
matrix=read(N/'analysis/matrix-analysis.json')
def valid_objects(scene):
    out=[]
    for key,obj in list(scene.get('objects',{}).items())[:64]:
        if not isinstance(key,str) or '_' not in key or not isinstance(obj,dict):continue
        category,suffix=key.rsplit('_',1)
        if not category or not suffix.isdigit() or int(suffix)<1:continue
        p,d=obj.get('pose',[]),obj.get('dims',[])
        if len(p)!=7 or len(d)!=3:continue
        if not all(isinstance(v,(int,float)) and v==v and abs(v)<10 for v in list(p)+list(d)):continue
        if not all(v>0 for v in d):continue
        out.append(dict(key=key,category=category,pose=p,dims=d))
    return out
rows=[];scene_rows=[]
for actor in matrix['actors']:
    assert actor['mapping_qualified'];name=actor['condition'];idx=actor['mapped_layout_id']
    path=N/actor['process_record'];calls=sorted(read(path)['calls'],key=lambda x:x['request']['id'])
    scenes=[c for c in calls if c['request']['method']=='scene' and 'response' in c]
    assert scenes
    expected=matrix['layouts'][idx]['categories'];expected={('camera' if k=='action_camera' else k):v for k,v in expected.items()}
    initial=valid_objects(scenes[0]['response']['value']);initial_items=[x for x in initial if x['category']!='basket']
    counts=Counter(x['category'] for x in initial_items);initial_categories=set(counts);seen=set();later_unassigned=set()
    for j,call in enumerate(scenes):
        objects=valid_objects(call['response']['value']);c=Counter(x['category'] for x in objects if x['category']!='basket');seen.update(c)
        unseen=set(c)-initial_categories
        if j:later_unassigned.update(unseen)
        scene_rows.append(dict(condition=name,layout_id=idx,scene_ordinal=j,rpc_call_id=call['request']['id'],visible_categories=dict(c),visible_baskets=sum(x['category']=='basket' for x in objects),categories_outside_initial_assignments=sorted(unseen),objects=objects))
    close_count=sum(c['request']['method']=='gripper' and c['request']['kwargs'].get('command')==0 for c in calls)
    loop_bound=min(6,len(initial_items));last=scene_rows[-1]
    rows.append(dict(condition=name,layout_id=idx,expected_object_count=sum(expected.values()),expected_categories=expected,first_scene_items=len(initial_items),first_scene_categories=dict(counts),missing_categories_first=sorted(set(expected)-initial_categories),minimum_count_deficit_first=sum(max(0,v-counts.get(k,0)) for k,v in expected.items()),frozen_loop_bound=loop_bound,actual_close_commands=close_count,reached_loop_bound=close_count==loop_bound,new_categories_seen_later_but_unassigned=sorted(later_unassigned),categories_never_seen=sorted(set(expected)-seen),last_scene_visible_baskets=last['visible_baskets'],native_score_100=next(x['normalized_score']*100 for x in matrix['episodes'] if x['condition']==name and x['layout_id']==idx),process_record=actor['process_record']))
rows.sort(key=lambda x:(x['condition'],x['layout_id']))
out=dict(state='completed',new_native_cases=0,new_api_calls=0,gpu_used=False,rows=rows,scenes=scene_rows,method='Actual isolated process scene responses passed through the exact candidate input-validation rules; category counts compared with frozen layout, camera alias normalized. Program source freezes assignments and min(6,len(initial_items)) before execution.',limits=['Object-count deficit does not prove an individual detection false negative without image/identity review.','Returned object numeric suffixes are not assumed persistent identities.','This is an analysis-only comparison to layout truth, never a policy input.','Latent coverage limits may not explain a run that already stops on an earlier planning failure.','Missing first-view categories do not prove the underlying vision model cannot detect them in another view.'])
(L/'observation-coverage-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
with (L/'observation-coverage-audit.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows({k:json.dumps(v) if isinstance(v,(dict,list)) else v for k,v in r.items()} for r in rows)
print(json.dumps(rows,ensure_ascii=False))
