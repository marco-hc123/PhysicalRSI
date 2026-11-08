"""Replay saved replies through the ACTUAL saved child wrapper, with hard bounds.

The counterfactual stops before any unrecorded response; it is not a native run.
"""
import ast, copy, csv, hashlib, io, json, sys, time
from pathlib import Path
L=Path(__file__).resolve().parent;N=L/'native-validation'
def read(p):return json.loads(p.read_text())
def sha(s):return hashlib.sha256(s.encode()).hexdigest()
class TapeBoundary(BaseException):pass
class TapeMismatch(BaseException):pass
old="raise RuntimeError('No collision-free path; no action executed by this call')"
rows=[]
for actor in read(N/'analysis/matrix-analysis.json')['actors']:
    p=N/actor['process_record'];root=p.parents[2]/'root'
    packet=read(root/'input.json');source=packet['source'];wrapper=(root/'policy.py').read_text()
    assert wrapper.count(old)==1
    calls=sorted(read(p)['calls'],key=lambda x:x['request']['id'])
    for mode in ['recorded_native_wrapper','structured_rejection_return']:
        driver=wrapper if mode=='recorded_native_wrapper' else wrapper.replace(old,'return value')
        cls=next(n for n in ast.parse(driver).body if isinstance(n,ast.ClassDef) and n.name=='_Robot')
        ix=[0];reply=[None];events=[];boundary=[]
        def publish(q):
            q=json.loads(json.dumps(q))
            if ix[0]>=len(calls):
                boundary.append(q);raise TapeBoundary('No saved response; no outcome inferred')
            row=calls[ix[0]]
            if q!=row['request']:raise TapeMismatch(str((ix[0],q,row['request'])))
            ix[0]+=1
            if 'response' not in row:raise TapeBoundary('Saved pending call')
            reply[0]=copy.deepcopy(row['response'])
        def fakeopen(path):
            assert path=='/response.json' and reply[0] is not None
            return io.StringIO(json.dumps(reply[0]))
        ns={'_publish':publish,'_json':json,'_time':time,'open':fakeopen}
        exec(compile(ast.Module(body=[cls],type_ignores=[]),'saved-wrapper','exec'),ns)
        candidate={};filename='saved-candidate'
        exec(compile(source,filename,'exec'),candidate)
        def trace(frame,event,arg):
            if frame.f_code.co_filename==filename and frame.f_code.co_name=='policy' and event in ('return','exception'):
                v=frame.f_locals
                events.append(dict(event=event,line=frame.f_lineno,source_line=source.splitlines()[frame.f_lineno-1].strip(),turn=v.get('turn'),attempted=len(v.get('attempted',[])),choices=len(v.get('choices',[])),exception=type(arg[1]).__name__ if event=='exception' else None,message=str(arg[1]) if event=='exception' else None))
            return trace
        stopped=False;sys.settrace(trace)
        try:candidate['policy'](ns['_Robot'](),copy.deepcopy(packet['memory']))
        except TapeBoundary:stopped=True
        finally:sys.settrace(None)
        assert ix[0]==len(calls)
        terminal=next((e for e in reversed(events) if e['event']=='return'),None)
        if stopped:reason='unrecorded_next_call_no_counterfactual_outcome'
        elif any(e['exception']=='RuntimeError' and e['message']=='No collision-free path; no action executed by this call' for e in events):reason='wrapper_converts_rejection_to_exception_candidate_catches_and_returns'
        elif terminal and source.splitlines()[terminal['line']-2].strip()=='if not choices:':reason='no_eligible_visible_choice'
        else:reason='other_return_review_source'
        rows.append(dict(layout_id=actor['mapped_layout_id'],actor=actor['actor_episode_id'],mode=mode,source_sha256=sha(source),wrapper_sha256=sha(wrapper),tested_driver_sha256=sha(driver),matched_recorded_calls=ix[0],exact_native_termination_reproduced=mode=='recorded_native_wrapper' and not stopped,reason=reason,trace=events,next_unrecorded_request=boundary))
rows.sort(key=lambda r:(r['layout_id'],r['mode']))
native=[r for r in rows if r['mode']=='recorded_native_wrapper'];future=[r for r in rows if r['mode']=='structured_rejection_return']
assert all(r['exact_native_termination_reproduced'] for r in native)
assert [r['layout_id'] for r in native if r['reason'].startswith('wrapper_')]==[1,4]
assert [r['layout_id'] for r in future if r['next_unrecorded_request']]==[1,4]
out=dict(state='passed',native_replays=5,counterfactual_prefixes=5,new_native_cases=0,new_api_calls=0,gpu_used=False,rows=rows,correction='terminal-replay.json v1 omitted the saved child-wrapper exception semantics and used a catchable AssertionError at the tape boundary. Its claimed exact termination for layouts1,4 is superseded. Scores and original records are unchanged.',limits=['Counterfactual next call has no response; no trajectory or score is inferred.','This diagnoses the saved experiment integration contract, not all upstream PhysicalRSI versions.'])
(L/'driver-contract-replay-v2.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(dict(state=out['state'],native_reasons=[dict(layout=r['layout_id'],reason=r['reason']) for r in native],counterfactual_next_calls=[dict(layout=r['layout_id'],request=r['next_unrecorded_request']) for r in future if r['next_unrecorded_request']])))
