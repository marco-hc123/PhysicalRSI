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
    delivered=bool(target and stable[target] and not row['initial_membership'][target]['inside'] and release is not None)
    row['selected_object_delivered_proxy']=delivered
    row['complete_chain_proxy']=bool(delivered and row['lift_proxy'] and transport is not None)
    row['physical_diagnosis']=('complete_chain_kinematic_evidence' if row['complete_chain_proxy'] else 'no_completed_lift_evidence' if not row['lift_proxy'] else 'no_completed_transport' if transport is None else 'no_release' if release is None else 'not_stably_in_target_basket')
    row['initial_root_xyz']=initial;row['final_root_xyz']=final
    return row
campaign=read(O/'native-campaign/campaign.json');matrix=read(O/'analysis/matrix-analysis.json');post=read(O/'analysis/postgrasp-analysis.json')
layouts=[read(Path(campaign['layout_root'])/c['file']) for c in campaign['cases']]
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

dump(O/'candidate-chain-analysis.json',dict(state='candidate_cohort_only',native_cases=5,cases=rows,api_calls=0))
print(json.dumps([{k:r.get(k) for k in ['layout_id','source_label','lift_root_rise_m','selected_object_delivered_proxy','complete_chain_proxy','physical_diagnosis','motion_endpoints']} for r in rows]))
