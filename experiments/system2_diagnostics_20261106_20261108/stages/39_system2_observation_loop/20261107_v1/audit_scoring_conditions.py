"""CPU-only post-hoc geometry audit using frozen original membership functions.

This never replaces the native receipt or supplies truth to a policy. The
normalized observation gripper gate and post-step sampling may differ at a
transition boundary from the original reward-manager evaluation time.
"""
from pathlib import Path
import ast,csv,hashlib,json,collections,sys
import numpy as np
import transforms3d as t3d
from shapely.geometry import Point,Polygon,MultiPoint
L=Path(__file__).resolve().parent;N=L/'native-validation';S=L/'scoring-reference'
O=L
if len(sys.argv)==2:
    N=Path(sys.argv[1]);O=L/'scoring-audit-preflight';O.mkdir(exist_ok=True)
def read(p):return json.loads(p.read_text())
manifest=read(S/'source-manifest.json')
for row in manifest:assert hashlib.sha256((S/row['name']).read_bytes()).hexdigest()==row['sha256']
scope=dict(np=np,t3d=t3d,Point=Point,Polygon=Polygon,MultiPoint=MultiPoint,check_1d=lambda x:isinstance(x,list) and not any(isinstance(v,list) for v in x))
tree=ast.parse((S/'transformer.py').read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='calc_polygon')
exec(compile(ast.Module(body=[node],type_ignores=[]),'frozen_calc_polygon','exec'),scope)
tree=ast.parse((S/'func_parser.py').read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and any(isinstance(x,ast.FunctionDef) and x.name=='is_A_in_B' for x in n.body))
methods=[n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name in ['is_A_in_B','is_A_z_lower_than_B_bbox_zmax']]
stub=ast.ClassDef(name='FrozenMembership',bases=[],keywords=[],body=methods,decorator_list=[])
mod=ast.fix_missing_locations(ast.Module(body=[stub],type_ignores=[]));exec(compile(mod,'frozen_membership','exec'),scope)
Member=scope['FrozenMembership']
class Layout:
    def __init__(self,snapshot,metadata):self.objects=snapshot['objects'];self.metadata=metadata
    def get_instance_name(self,label,env_idx):return label if label in self.objects else None
    def get_instance_pose(self,inst_name,env_idx):
        p=self.objects[inst_name];return p['position_world'],p['quaternion_wxyz']
    def get_instance_bbox_vertices(self,inst_name,env_idx):return self.metadata[inst_name]

matrix=read(N/'analysis/matrix-analysis.json')
records=collections.defaultdict(list)
for path in (N/'sim-diagnostics').rglob('*.jsonl'):
    for line in path.open():
        x=json.loads(line)
        if x.get('event')=='snapshot':records[(path.parent.name,int(x['layout_seed']))].append(x)
results=[];details=[]
for key,snapshots in sorted(records.items()):
    condition,idx=key;snapshots.sort(key=lambda x:x['monotonic_ns'])
    case=matrix['layouts'][idx];file=Path('generated/classify_objects')/str(case['source_layout_id'])/'layout.json'
    layout=read(N/'analysis/reference-layouts'/file)
    metadata={b['label']:read(S/('basket_'+str(b['category_idx']).zfill(5)+'.json'))['geometry']['oriented_bbox']['vertices'] for b in layout['Geometry']['basket']}
    assert all(b['scale']==[1.0,1.0,1.0] for b in layout['Geometry']['basket'])
    first_hits={};max_groups=0;last=None
    for snap in snapshots:
        parser=Member();parser.layout_manager=Layout(snap,metadata);groups=[];per_basket={}
        labels={i:sorted(k for k in snap['objects'] if k.startswith('cat'+str(i)+'_')) for i in range(3)}
        assert all(labels.values()),'No empty category accepted'
        for b in metadata:
            memberships={k:bool(parser.is_A_in_B(dict(env_idx=0,label_A=k,label_B=b))) for ls in labels.values() for k in ls}
            settled={k:bool(parser.is_A_z_lower_than_B_bbox_zmax(dict(env_idx=0,label_A=k,label_B=b,z_threshold=.01))) for ls in labels.values() for k in ls}
            complete=[i for i,ls in labels.items() if all(memberships[k] and settled[k] for k in ls) and not any(memberships[k] for j,other in labels.items() if j!=i for k in other)]
            if complete:groups.append(dict(basket=b,category=complete[0]))
            per_basket[b]=dict(inside=[k for k,v in memberships.items() if v],settled_inside=[k for k,v in memberships.items() if v and settled[k]],complete_pure_categories=complete)
        grip={k:float(np.mean(v)) for k,v in snap['observation_state'].items() if k.endswith('_ee_joint_state')}
        assert len(grip)==2
        opened=all(v>=.8 for v in grip.values());n=len(groups)
        if opened:
            max_groups=max(max_groups,n)
            for count in range(1,n+1):first_hits.setdefault(str(count),snap['native_action_count'])
        last=dict(condition=condition,layout_id=idx,action=snap['native_action_count'],complete_groups=groups,all_grippers_open_observation=opened,normalized_grippers=grip,baskets=per_basket)
        if snap is snapshots[0] or snap is snapshots[-1]:details.append(dict(phase='initial' if snap is snapshots[0] else 'final',**last))
    receipt=next(x for x in matrix['episodes'] if x['condition']==condition and x['layout_id']==idx)
    results.append(dict(condition=condition,layout_id=idx,snapshots=len(snapshots),native_score_100=receipt['normalized_score']*100,native_success=receipt['success'],max_complete_pure_groups_while_open=max_groups,first_sampled_complete_group_actions=first_hits,final_complete_pure_groups=len(last['complete_groups']),final_all_grippers_open=last['all_grippers_open_observation'],final_groups=last['complete_groups']))
out=dict(state='completed',native_cases_added=0,api_calls=0,gpu_used=False,rows=results,initial_and_final=details,source_manifest='scoring-reference/source-manifest.json',method='Original frozen calc_polygon/is_A_in_B/is_A_z_lower_than_B_bbox_zmax executed with archived post-step object poses and exact unit-scale basket metadata; normalized observed gripper>=0.8 gate.',limits=['This is post-hoc geometry evidence, not a replacement reward manager.','Native score is transition history; maximum sampled groups is a separate descriptive quantity.','Post-step observation time may differ from reward evaluation, especially at boundaries.','Full success includes separate native checks and is taken only from raw receipt.','Object root point membership is the frozen scoring definition, not a physical collision/contact certificate.','No privileged state was passed to candidate decisions.'])
(O/'scoring-condition-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
with (O/'scoring-condition-audit.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(results[0]));w.writeheader();w.writerows({k:json.dumps(v) if isinstance(v,(dict,list)) else v for k,v in row.items()} for row in results)
print(json.dumps(results,ensure_ascii=False))
