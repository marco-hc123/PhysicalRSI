"""Replay exact recorded RPC responses, trace the unchanged candidate's exit.

No simulator/model/API call. This explains a saved execution, not performance of
a counterfactual world. Every request must match the saved method and arguments.
"""
from pathlib import Path
import builtins,copy,csv,hashlib,json,sys,ast
L=Path(__file__).resolve().parent;N=L/'native-validation'
def read(p):return json.loads(p.read_text())
matrix=read(N/'analysis/matrix-analysis.json');rows=[]
class EndOfRecordedExecution(BaseException):pass
for actor in matrix['actors']:
    assert actor['mapping_qualified']
    path=N/actor['process_record'];packet=read(path.parents[2]/'root/input.json');source=packet['source']
    assert source==(L/'candidates'/actor['condition']/'candidate.py').read_text()
    tree=ast.parse(source)
    assert len(tree.body)==1 and isinstance(tree.body[0],ast.FunctionDef) and tree.body[0].name=='policy'
    assert not any(isinstance(n,(ast.Import,ast.ImportFrom,ast.Global,ast.Nonlocal)) for n in ast.walk(tree))
    calls=sorted(read(path)['calls'],key=lambda x:x['request']['id']);index=[0];events=[]
    class Robot:
        def __getattr__(self,name):
            assert name in ['scene','reobserve','approach','gripper']
            def request(*args,**kwargs):
                i=index[0];assert i<len(calls),'Replay requested an unrecorded call'
                row=calls[i];r=row['request'];assert r['method']==name and r.get('args',[])==list(args) and r['kwargs']==kwargs,(i,name,'request mismatch')
                index[0]+=1
                if 'response' not in row:raise EndOfRecordedExecution('Recorded call has no response')
                response=row['response'];assert 'value'in response,response.keys()
                return copy.deepcopy(response['value'])
            return request
    filename='saved-candidate-'+actor['actor_episode_id']
    allowed=['sum','list','isinstance','str','dict','len','int','float','abs','all','any','enumerate','set','sorted','range','min','max','Exception','RuntimeError']
    namespace={'__builtins__':{k:getattr(builtins,k) for k in allowed}}
    exec(compile(tree,filename,'exec'),namespace)
    def trace(frame,event,arg):
        if frame.f_code.co_filename!=filename:return trace
        if frame.f_code.co_name=='policy' and event in ['return','exception']:
            local=frame.f_locals
            events.append(dict(event=event,line=frame.f_lineno,source_line=source.splitlines()[frame.f_lineno-1].strip(),turn=local.get('turn'),initial_item_count=len(local.get('items',[])),attempted=len(local.get('attempted',[])),choices=len(local.get('choices',[])),assignments=copy.deepcopy(local.get('assignments',{})),exception=type(arg[1]).__name__ if event=='exception' else None))
        return trace
    pending=False
    sys.settrace(trace)
    try:namespace['policy'](Robot(),copy.deepcopy(packet['memory']))
    except EndOfRecordedExecution:pending=True
    finally:sys.settrace(None)
    assert index[0]==len(calls),(actor['actor_episode_id'],index[0],len(calls))
    terminal=next((x for x in reversed(events) if x['event']=='return'),None)
    if pending:reason='recorded_pending_call_at_native_termination'
    elif terminal and terminal['source_line'].startswith('for turn in '):reason='initial_observation_loop_bound_exhausted'
    elif terminal and terminal['source_line']=='return':
        previous=source.splitlines()[terminal['line']-2].strip()
        if previous=='if not choices:':reason='no_eligible_visible_choice'
        elif previous.startswith('if not move('):reason='explicit_planning_rejection'
        else:reason='explicit_return_review_source'
    else:reason='implicit_return_review_trace'
    rows.append(dict(condition=actor['condition'],layout_id=actor['mapped_layout_id'],source_sha256=hashlib.sha256(source.encode()).hexdigest(),recorded_rpc_calls=len(calls),exact_request_response_replay=True,pending_call=pending,terminal_reason=reason,terminal=terminal,trace_events=events))
rows.sort(key=lambda x:(x['condition'],x['layout_id']))
out=dict(state='passed',replayed_episodes=len(rows),new_native_cases=0,new_api_calls=0,gpu_used=False,rows=rows,limits=['Exact fixed-response replay explains existing code decisions only; no new physical outcome or counterfactual improvement.','Pending native calls stop the replay without inventing their result.','Original source and memory are unchanged; recorded method/arguments and call counts must match exactly.'])
(L/'terminal-replay.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
with (L/'terminal-replay.csv').open('w',newline='') as f:
    fields=[k for k in rows[0] if k!='trace_events'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:json.dumps(r[k]) if isinstance(r[k],(dict,list)) else r[k] for k in fields} for r in rows)
print(json.dumps([{k:r[k] for k in ['condition','layout_id','terminal_reason','terminal']} for r in rows],ensure_ascii=False))
