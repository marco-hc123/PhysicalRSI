"""Post-hoc capability audit. Truth stays in diagnostic files, never in policy."""
import ast,csv,json,math,hashlib,datetime
from pathlib import Path
import numpy as np
import transforms3d as t3d
from shapely.geometry import Point,Polygon,MultiPoint
O=Path(__file__).resolve().parent;S=O/'scoring-reference'
def read(p):return json.loads(Path(p).read_text())
def lines(p):return [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def flat(x):
    while isinstance(x,list) and len(x)==1 and isinstance(x[0],list):x=x[0]
    return x
criteria=read(O/'analysis-criteria.json')
for row in read(S/'source-manifest.json'):assert hashlib.sha256((S/row['name']).read_bytes()).hexdigest()==row['sha256']
scope=dict(np=np,t3d=t3d,Point=Point,Polygon=Polygon,MultiPoint=MultiPoint,check_1d=lambda x:isinstance(x,list) and not any(isinstance(v,list) for v in x))
tree=ast.parse((S/'transformer.py').read_text());f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='calc_polygon')
exec(compile(ast.Module(body=[f],type_ignores=[]),'frozen_polygon','exec'),scope)
tree=ast.parse((S/'func_parser.py').read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and any(isinstance(f,ast.FunctionDef) and f.name=='is_A_in_B' for f in n.body))
methods=[n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name in ['is_A_in_B','is_A_z_lower_than_B_bbox_zmax']]
stub=ast.ClassDef(name='FrozenMembership',bases=[],keywords=[],body=methods,decorator_list=[])
exec(compile(ast.fix_missing_locations(ast.Module(body=[stub],type_ignores=[])),'frozen_membership','exec'),scope)
Member=scope['FrozenMembership']
class Layout:
    def __init__(self,snapshot,meta):self.objects=snapshot['objects'];self.metadata=meta
    def get_instance_name(self,label,env_idx):return label if label in self.objects else None
    def get_instance_pose(self,inst_name,env_idx):
        p=self.objects[inst_name];return p['position_world'],p['quaternion_wxyz']
    def get_instance_bbox_vertices(self,inst_name,env_idx):return self.metadata[inst_name]
def memberships(snap,meta,label):
    p=Member();p.layout_manager=Layout(snap,meta);out={}
    for b in meta:
        inside=bool(p.is_A_in_B(dict(env_idx=0,label_A=label,label_B=b)))
        settled=bool(p.is_A_z_lower_than_B_bbox_zmax(dict(env_idx=0,label_A=label,label_B=b,z_threshold=.01)))
        out[b]=dict(inside=inside,settled_inside=inside and settled)
    return out
def assoc(snap,xy,basket=False):
    rows=sorted((math.dist(xy[:2],v['position_world'][:2]),k) for k,v in snap['objects'].items() if k.startswith('basket' if basket else 'cat'))
    if not rows:return None,dict(qualified=False)
    d,k=rows[0];margin=rows[1][0]-d if len(rows)>1 else None
    good=(d<(.15 if basket else .05) and (margin is None or margin>(.05 if basket else .01)))
    return k if good else None,dict(qualified=good,nearest=k,distance_m=d,margin_m=margin)
def near(snapshots,ns):
    before=[x for x in snapshots if x['monotonic_ns']<=ns]
    return before[-1] if before else snapshots[0]
def measure(row,snaps,meta,source_xy,arm,phase,destination=None):
    first=phase.get('selection',snaps[0]);label,association=assoc(first,source_xy) if source_xy else (None,dict(qualified=False))
    row.update(source_association=association,source_label=label,arm=arm,phase_action_indices={k:v['native_action_count'] for k,v in phase.items()})
    if not label:row.update(complete_chain_proxy=None,physical_diagnosis='source identity unknown');return row
    row['source_instance']=first['objects'][label]['instance']
    initial=first['objects'][label]['position_world'];final=snaps[-1]['objects'][label]['position_world']
    phase_objects={}
    for stage,snap in dict(phase,final=snaps[-1]).items():
        obj=snap['objects'][label]['position_world'];key=next((k for k in snap['robots'] if arm and k.startswith(arm)),None)
        ee=flat(snap['robots'][key]['ee_pose_world'])[:3] if key else None
        phase_objects[stage]=dict(root_xyz=obj,root_rise_m=obj[2]-initial[2],basket_membership=memberships(snap,meta,label),ee_xyz=ee,object_minus_ee_xyz=[a-b for a,b in zip(obj,ee)] if ee else None)
    row['phase_object_states']=phase_objects
    lift=phase.get('lift');transport=phase.get('transport');release=phase.get('release')
    rise=lift['objects'][label]['position_world'][2]-initial[2] if lift else None
    row['lift_root_rise_m']=rise;row['lift_proxy']=rise>=.02 if rise is not None else False
    row['max_root_rise_m']=max(s['objects'][label]['position_world'][2]-initial[2] for s in snaps)
    row['final_displacement_xy_m']=math.dist(initial[:2],final[:2])
    row['object_transport_xy_m']=None;row['object_ee_comotion_residual_m']=None
    if lift and transport:
        lp=lift['objects'][label]['position_world'];tp=transport['objects'][label]['position_world']
        row['object_transport_xy_m']=math.dist(lp[:2],tp[:2])
        key=next((k for k in lift['robots'] if arm and k.startswith(arm)),None)
        if key:
            le=flat(lift['robots'][key]['ee_pose_world'])[:3];te=flat(transport['robots'][key]['ee_pose_world'])[:3]
            row['object_ee_comotion_residual_m']=math.dist([b-a for a,b in zip(lp,tp)],[b-a for a,b in zip(le,te)])
    target,target_assoc=assoc(first,destination,True) if destination else (None,dict(qualified=False))
    row['target_basket']=target;row['target_association']=target_assoc
    row['initial_membership']=memberships(first,meta,label);row['final_membership']=memberships(snaps[-1],meta,label)
    stable={b:all(memberships(s,meta,label)[b]['settled_inside'] for s in snaps[-10:]) for b in meta}
    row['stable_final_membership']=stable
    row['release_observed']=release is not None
    grip_key=arm+'_ee_joint_state' if arm else None
    grip=flat(snaps[-1]['observation_state'].get(grip_key,[])) if grip_key else []
    row['final_gripper_normalized']=float(np.mean(grip)) if grip else None
    delivered=bool(target and stable[target] and not row['initial_membership'][target]['inside'] and release is not None)
    row['selected_object_delivered_proxy']=delivered
    row['complete_chain_proxy']=bool(delivered and row['lift_proxy'] and transport is not None)
    row['physical_diagnosis']=('complete_chain_kinematic_evidence' if row['complete_chain_proxy'] else 'no_completed_lift_evidence' if not row['lift_proxy'] else 'no_completed_transport' if transport is None else 'no_release' if release is None else 'not_stably_in_target_basket')
    row['initial_root_xyz']=initial;row['final_root_xyz']=final
    return row
campaign=read(O/'native-campaign/campaign.json');matrix=read(O/'analysis/matrix-analysis.json');post=read(O/'analysis/postgrasp-analysis.json')
layouts=[read(O/'analysis/reference-layouts'/c['file'] if (O/'analysis/reference-layouts'/c['file']).exists() else Path(campaign['layout_root'])/c['file']) for c in campaign['cases']]
def metadata(i):
    return {b['label']:read(S/('basket_'+str(b['category_idx']).zfill(5)+'.json'))['geometry']['oriented_bbox']['vertices'] for b in layouts[i]['Geometry']['basket']}
from selected_sidecars import select
paths,binding=select(O);all_snaps=[x for p in paths for x in lines(p) if x.get('event')=='snapshot'];rows=[]
for a in matrix['actors']:
    assert a['mapping_qualified'];i=a['mapped_layout_id'];snaps=sorted([x for x in all_snaps if x['layout_seed']==i],key=lambda x:x['native_action_count'])
    assert [x['native_action_count'] for x in snaps]==list(range(1101))
    ps=sorted([x for x in post['primitives'] if x['actor_episode_id']==a['actor_episode_id']],key=lambda x:x['ordinal'])
    motions=[p for p in ps if p['method']=='approach'];closes=[p for p in ps if p['method']=='gripper' and p['kwargs']['command']==0];assert len(closes)<=1
    phase={};source_xy=motions[0]['kwargs']['position_m'] if motions else None;arm=None;destination=None
    if motions:phase['selection']=near(snaps,motions[0]['begin_ns'])
    def accepted(p):return p['return_event']=='return' and not (p.get('result') or {}).get('primitive_error')
    if closes:
        close=closes[0];arm=close['arm'];phase['close']=near(snaps,close['end_ns'])
        following=[p for p in ps if p['ordinal']>close['ordinal'] and p['method']=='approach']
        for name,p in zip(['lift','transport'],following):
            if accepted(p):phase[name]=near(snaps,p['end_ns'])
            if name=='transport':destination=p['kwargs']['position_m']
        release=next((p for p in ps if p['ordinal']>close['ordinal'] and p['method']=='gripper' and p['kwargs']['command']==1),None)
        if release:phase['release']=near(snaps,release['end_ns'])
    e=next(x for x in matrix['episodes'] if x['layout_id']==i)
    endpoints=[];opened=False;closed=False;after_close=0
    for p in ps:
        if p['method']=='gripper':
            if p['kwargs']['command']==0:closed=True;after_close=0
            else:opened=True
        elif p['method']=='approach':
            if closed:
                after_close+=1;stage='lift' if after_close==1 else 'transport'
            else:stage='contact' if opened else 'pregrasp'
            endpoints.append(dict(stage=stage,arm=p['arm'],accepted=accepted(p),error=(p.get('result') or {}).get('primitive_error') or p.get('error'),ee_translation_error_m=p['ee_translation_error_m'],start_action=p['start_action'],end_action=p['end_action']))
    row=dict(condition='single_cycle',layout_id=i,native_score_100=100*e['normalized_score'],native_full_success=e['success'],motion_calls=len(motions),closed=bool(closes),completed_motion_calls=sum(accepted(p) for p in motions),first_error=a['first_error'],motion_endpoints=endpoints,candidate_sha256=hashlib.sha256((O/'candidates/single_cycle/candidate.py').read_bytes()).hexdigest(),runtime_scope='Four candidate primitives, historical corrected execution contracts')
    rows.append(measure(row,snaps,metadata(i),source_xy,arm,phase,destination))
D=O/'reference';validation=read(D/'analysis/independent-validation.json');events=lines(D/'service-events.jsonl')
active_ids=list(dict.fromkeys(x['episode'] for x in events if x['event']=='initial_observation'));assert len(active_ids)==5
process=read(D/'native/processes/simulator/process.json');assert process['state']=='completed' and process['returncode']==0
sp=D/'sim-diagnostics'/f'simulator-{process["pid"]}.jsonl';ref_snaps=[x for x in lines(sp) if x.get('event')=='snapshot']
for i,(episode_id,e) in enumerate(zip(active_ids,validation['episodes'])):
    snaps=sorted([x for x in ref_snaps if x['layout_seed']==i],key=lambda x:x['native_action_count']);assert [x['native_action_count'] for x in snaps]==list(range(1101))
    obs=[x for x in events if x.get('episode')==episode_id and x['event']=='observation']
    traces=[x for p in e['source_traces'] for x in lines(D/p)]
    begins=[x for x in traces if x.get('capacity_transfer_begin')]
    basket=next((x for x in begins if x['capacity_transfer_tag']=='basket'),None)
    selected=basket or (begins[0] if begins else None);phase={};xy=None;arm=None;destination=None
    def at(index):
        exact=[o for o in obs if o['model_action_index']==index]
        assert exact,('Trace-observation join absent',i,index)
        return near(snaps,exact[-1]['monotonic_ns'])
    if selected:
        xy=selected['capacity_source']['xyz'];arm=selected['capacity_arm'];destination=selected['capacity_destination'] if basket else None
        phase['selection']=at(selected['action_index']);cut=selected['action_index']
        segment=[x for x in traces if x['action_index']>=cut]
        # Stage transition into the next movement identifies the previous phase endpoint.
        for name,next_stage in [('close','capture_lift'),('lift','transport'),('transport','basket_lower'),('release','retreat')]:
            event=next((x for x in segment if x.get('stage')==next_stage),None)
            if event:phase[name]=at(event['action_index'])
    release_kind='planned' if 'release' in phase else None
    failure_release=next((x for x in traces if x.get('physical_release') is True and x.get('failure')),None)
    if release_kind is None and failure_release and 'lift' in phase:
        # The released controller explicitly opens both grippers on RuntimeError.
        # Keep this distinguishable from successfully completing its transfer.
        next_obs=next((o for o in obs if o['model_action_index']>failure_release['action_index']),None)
        if next_obs:phase['release']=near(snaps,next_obs['monotonic_ns']);release_kind='failure_cleanup'
    row=dict(condition='released_first_basket_cycle',layout_id=i,native_score_100=100*e['episode_score'],native_full_success=e['success'],last_stage=e['last_model_stage'],first_error=e['last_model_failure'],observed_stages=e['observed_stages'],transfer_attempts=len(begins),basket_boundary_reached=any(x.get('capacity_cycle_boundary') for x in traces),release_kind=release_kind,source_traces=e['source_traces'],runtime_scope='Complete released controller; richer perception/IK/joint/endpoint/recovery interface')
    rows.append(measure(row,snaps,metadata(i),xy,arm,phase,destination))
rows.sort(key=lambda x:(x['condition'],x['layout_id']))
groups=[]
for condition in sorted(set(x['condition'] for x in rows)):
    r=[x for x in rows if x['condition']==condition]
    groups.append(dict(condition=condition,cases=len(r),qualified_source_associations=sum(x['source_association']['qualified'] for x in r),completed_lift_proxies=sum(x.get('lift_proxy',False) for x in r),release_observed=sum(x.get('release_observed',False) for x in r),delivered_proxies=sum(x.get('selected_object_delivered_proxy',False) for x in r),complete_chain_proxies=sum(x.get('complete_chain_proxy') is True for x in r),unknown_chain_cases=sum(x.get('complete_chain_proxy') is None for x in r),native_scores_100=[x['native_score_100'] for x in r],native_full_successes=sum(x['native_full_success'] for x in r)))
out=dict(state='completed',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),new_native_cases=10,new_api_calls=0,lab_gpu_used=False,unique_exposed_layouts=5,groups=groups,cases=rows,analysis_criteria=criteria,limitations=read(O/'protocol.json')['limits'],no_policy_promotion=True)
dump(O/'chain-analysis.json',out)
fields=list(dict.fromkeys(k for r in rows for k in r))
with (O/'chain-results.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in r.items()} for r in rows)
print(json.dumps(groups))
