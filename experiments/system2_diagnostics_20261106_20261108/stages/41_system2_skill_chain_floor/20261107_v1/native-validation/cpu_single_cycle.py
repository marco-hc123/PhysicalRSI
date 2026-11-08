"""Exercise exact candidate source with the real transformed child wrapper."""
import ast,io,json,sys,time,hashlib
from pathlib import Path
O=Path(__file__).resolve().parent;sys.path.insert(0,str(O/'code'))
from structured_feedback import transform_driver
tree=ast.parse((O/'driver-contract-provenance/code_execution.py').read_text())
driver=transform_driver(next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='_DRIVER' for t in n.targets)))
cls=next(n for n in ast.parse(driver).body if isinstance(n,ast.ClassDef))
src=(O/'candidates/single_cycle/candidate.py').read_text();rows=[]
scene={'objects':{'basket_1':{'pose':[-.30,0,.8,1,0,0,0],'dims':[.15,.15,.1]},'toy_car_1':{'pose':[-.22,-.22,.8,1,0,0,0],'dims':[.04,.04,.02]},'toy_car_2':{'pose':[-.1,-.3,.8,1,0,0,0],'dims':[.04,.04,.02]}}}
for kind in ['success','first_pregrasp_rejection','all_pregrasp_rejected','transport_rejection']:
    requests=[];responses={};moves=[0]
    def publish(q):
        requests.append(q);method=q['method']
        value=scene if method=='scene' else dict(state={},action_steps=1)
        if method=='approach':
            moves[0]+=1;n=moves[0]
            reject=(kind=='first_pregrasp_rejection' and n==1) or kind=='all_pregrasp_rejected' or (kind=='transport_rejection' and n==4)
            if reject:value=dict(primitive_error='no_collision_free_path',state={},action_steps=0)
        responses[q['id']]=dict(id=q['id'],value=value)
    ns={'_publish':publish,'_json':json,'_time':time,'open':lambda p:io.StringIO(json.dumps(responses[requests[-1]['id']]))}
    exec(compile(ast.Module(body=[cls],type_ignores=[]),'exact_child','exec'),ns)
    scope={};exec(compile(src,'exact_candidate','exec'),scope);scope['policy'](ns['_Robot'](),{})
    closes=sum(q['method']=='gripper' and q['kwargs']['command']==0 for q in requests)
    assert closes==(0 if kind=='all_pregrasp_rejected' else 1)
    assert moves[0]==dict(success=4,first_pregrasp_rejection=5,all_pregrasp_rejected=2,transport_rejection=4)[kind]
    if kind in ['success','first_pregrasp_rejection']:assert requests[-1]['method']=='gripper' and requests[-1]['kwargs']['command']==1
    rows.append(dict(condition=kind,requests=requests,closes=closes,moves=moves[0]))
out=dict(state='passed',fixtures=len(rows),source_sha256=hashlib.sha256(src.encode()).hexdigest(),driver_sha256=hashlib.sha256(driver.encode()).hexdigest(),rows=rows,physical_success_claim=False,api_calls=0)
(O/'cpu-single-cycle.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(state='passed',fixtures=4)))
