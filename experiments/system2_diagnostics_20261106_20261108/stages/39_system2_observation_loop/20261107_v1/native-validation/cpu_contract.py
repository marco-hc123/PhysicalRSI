"""The loop edit must preserve every saved action and only request another scene."""
from pathlib import Path
import copy,hashlib,json
H=Path(__file__).resolve().parent
control=(H/'control_candidate.py').read_text();source=(H/'candidates/fixed_six_turns/candidate.py').read_text()
assert source.replace('range(6)','range(min(6, len(items)))')==control
records=json.loads((H/'recorded-prefixes.json').read_text());rows=[]
class UnobservedNextCall(BaseException):pass
for record in records:
    assert hashlib.sha256(control.encode()).hexdigest()==record['source_sha256']
    calls=sorted(record['calls'],key=lambda x:x['request']['id'])
    for name,program in [('saved_control',control),('fixed_six_turns',source)]:
        index=[0];extra=[]
        class Robot:
            def __getattr__(self,method):
                assert method in ['scene','reobserve','approach','gripper']
                def invoke(*args,**kwargs):
                    i=index[0]
                    if i==len(calls):
                        extra.append(dict(method=method,args=list(args),kwargs=kwargs));raise UnobservedNextCall()
                    r=calls[i];q=r['request'];assert q['method']==method and q.get('args',[])==list(args) and q['kwargs']==kwargs
                    assert 'value'in r['response'];index[0]+=1;return copy.deepcopy(r['response']['value'])
                return invoke
        namespace={};exec(compile(program,'<fixed-source-loop-contract>','exec'),namespace)
        try:namespace['policy'](Robot(),copy.deepcopy(record['memory']))
        except UnobservedNextCall:pass
        assert index[0]==len(calls)
        assert extra==([] if name=='saved_control' else [dict(method='scene',args=[],kwargs={})])
        rows.append(dict(condition=name,layout_id=record['layout_id'],matched_existing_calls=index[0],first_unrecorded_call=extra,source_record_sha256=record['source_file_sha256']))
out=dict(state='passed',fixture_cases=len(rows),new_native_cases=0,api_calls=0,lab_gpu_used=False,source_only_loop_bound_changed=True,rows=rows,scope='Exact historical-response prefix replay. No future physical response is invented; treatment stops at its first additional scene request.')
(H/'cpu-contract-results.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(state='passed',fixture_cases=len(rows))))
