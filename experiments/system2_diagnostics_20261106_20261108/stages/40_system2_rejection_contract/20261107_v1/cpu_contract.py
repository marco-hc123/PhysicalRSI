"""Exercise the exact recorded child class and one-line transformation on CPU."""
import ast, hashlib, io, json, sys, time
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H/'code'))
from structured_feedback import transform_driver
tree=ast.parse((H/'driver-contract-provenance/code_execution.py').read_text())
original=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='_DRIVER' for t in n.targets))
patched=transform_driver(original);rows=[]
for mode,driver in [('original',original),('structured',patched)]:
    cls=next(n for n in ast.parse(driver).body if isinstance(n,ast.ClassDef))
    for kind,value in [('success',{'state':{},'action_steps':1}),('zero_action_rejection',{'primitive_error':'no_collision_free_path','state':{},'action_steps':0}),('other_error',{'primitive_error':'unknown','state':{}})]:
        requests=[]
        ns={'_publish':requests.append,'_json':json,'_time':time,'open':lambda p:io.StringIO(json.dumps(dict(id=0,value=value)))}
        exec(compile(ast.Module(body=[cls],type_ignores=[]),'driver','exec'),ns)
        error=None;returned=None
        try:returned=ns['_Robot']().approach(arm='left')
        except RuntimeError as e:error=str(e)
        expected_error=mode=='original' and kind=='zero_action_rejection'
        assert (error is not None)==expected_error
        if not expected_error:assert returned==value
        assert requests==[dict(kind='call',id=0,method='approach',args=(),kwargs={'arm':'left'})]
        rows.append(dict(mode=mode,response=kind,raises=error,returned=returned))
out=dict(state='passed',fixtures=6,new_native_cases=0,new_api_calls=0,gpu_used=False,original_driver_sha256=hashlib.sha256(original.encode()).hexdigest(),patched_driver_sha256=hashlib.sha256(patched.encode()).hexdigest(),rows=rows,limits=['Protocol fixtures only; no physical outcome.','Five saved native tapes and bounded alternate-arm continuations are independently validated by prior stage driver-contract-replay-v2.json.'])
(H/'cpu-contract-results.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(state='passed',fixtures=6,original_sha256=out['original_driver_sha256'],patched_sha256=out['patched_driver_sha256'])))
