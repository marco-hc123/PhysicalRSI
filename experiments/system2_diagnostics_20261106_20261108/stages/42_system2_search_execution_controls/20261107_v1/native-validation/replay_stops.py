"""Post-hoc source replay against recorded RPC replies. Never executes robot actions."""
import ast,builtins,copy,hashlib,json,resource,subprocess,sys,collections,os
from pathlib import Path
class Boundary(BaseException):pass
def worker():
 resource.setrlimit(resource.RLIMIT_CORE,(0,0));resource.setrlimit(resource.RLIMIT_CPU,(5,5));resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,512*1024*1024))
 data=json.load(sys.stdin);source=data['source'];calls=data['calls'];index=0;mismatch=None;recent=collections.deque(maxlen=30);exceptions=[];exit_line=None;steps=0
 safe_names=['abs','all','any','bool','dict','enumerate','float','int','isinstance','iter','len','list','max','min','next','range','reversed','round','set','sorted','str','sum','tuple','zip','map','filter','pow','divmod','chr','ord','repr','format','slice','frozenset','Exception','RuntimeError','ValueError','TypeError','KeyError','IndexError','TimeoutError','StopIteration','ZeroDivisionError','ArithmeticError','OverflowError','AssertionError']
 class Robot:
  def rpc(self,method,args,kwargs):
   nonlocal index,mismatch
   if index>=len(calls):raise Boundary('Beyond recorded RPC boundary')
   row=calls[index];request=row['request']
   if request['method']!=method or request.get('args',[])!=list(args) or request.get('kwargs',{})!=kwargs:
    mismatch=dict(index=index,expected_method=request['method'],actual_method=method,expected_kwargs=request.get('kwargs',{}),actual_kwargs=kwargs);raise Boundary('Recorded call mismatch')
   index+=1
   if 'response' not in row:raise Boundary('Recorded incomplete RPC; no invented reply')
   response=row['response']
   if 'error' in response:raise RuntimeError(str(response['error']))
   return copy.deepcopy(response['value'])
  def scene(self,*args,**kwargs):return self.rpc('scene',args,kwargs)
  def approach(self,*args,**kwargs):return self.rpc('approach',args,kwargs)
  def gripper(self,*args,**kwargs):return self.rpc('gripper',args,kwargs)
  def reobserve(self,*args,**kwargs):return self.rpc('reobserve',args,kwargs)
 def trace(frame,event,arg):
  nonlocal steps,exit_line
  if frame.f_code.co_filename!='<recorded-candidate>':return trace
  steps+=1
  if steps>200000:raise Boundary('Bounded replay trace limit')
  if event=='line':recent.append(dict(function=frame.f_code.co_name,line=frame.f_lineno))
  if event=='exception' and len(exceptions)<40:exceptions.append(dict(function=frame.f_code.co_name,line=frame.f_lineno,type=arg[0].__name__,message=str(arg[1])[:400]))
  if event=='return' and frame.f_code.co_name=='policy':exit_line=frame.f_lineno
  return trace
 scope={'__builtins__':{k:getattr(builtins,k) for k in safe_names}}
 terminal=None
 try:
  exec(compile(source,'<recorded-candidate>','exec'),scope)
  sys.settrace(trace);value=scope['policy'](Robot(),copy.deepcopy(data['memory']));terminal='returned'
 except BaseException as e:terminal=type(e).__name__+': '+str(e)
 finally:sys.settrace(None)
 lines=source.splitlines();result=dict(terminal=terminal,consumed_calls=index,recorded_calls=len(calls),all_recorded_calls_matched=index==len(calls) and mismatch is None,mismatch=mismatch,policy_exit_line=exit_line,policy_exit_source=lines[exit_line-1] if exit_line else None,recent_lines=list(recent),exceptions=exceptions,trace_events=steps,scope='Recorded-reply replay only; no native dynamics, no invented responses. Runtime-error projection may differ in wording; exact RPC sequence required for attribution.')
 print(json.dumps(result))
def main(phase):
 os.environ['CUDA_VISIBLE_DEVICES']=''
 O=Path(__file__).resolve().parent;P=O/phase;read=lambda p:json.loads(p.read_text())
 c=read(P/'native-campaign/campaign.json');m=read(P/'analysis/matrix-analysis.json');out=[]
 for actor in m['actors']:
  e=next(x for x in c['entries'] if x['name']==actor['condition']);h=Path(e['harness']['root']);source=(h/'code/classify_objects.py').read_text();memory=read(h/'memory_rules.json').get('classify_objects',{})
  process=read(P/actor['process_record']);payload=dict(source=source,memory=memory,calls=process['calls'])
  binding=read(P/actor['binding_record'])
  canonical_digest=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
  assert canonical_digest(source)==binding['source_sha256']
  assert canonical_digest(memory)==binding['memory_sha256']
  # The same admission used before native execution; do not execute unaudited text.
  sys.path.insert(0,str(O));from prepare_phase import audit
  assert audit(source)['admitted']
  try:
   p=subprocess.run([sys.executable,'-B',__file__,'--worker'],input=json.dumps(payload),capture_output=True,text=True,timeout=8)
   result=json.loads(p.stdout) if p.returncode==0 else dict(terminal='worker_failed',returncode=p.returncode,error=p.stderr[-500:])
  except subprocess.TimeoutExpired:result=dict(terminal='replay_timeout')
  result.update(condition=actor['condition'],layout_id=actor['mapped_layout_id'],actor_episode_id=actor['actor_episode_id'],source_sha256=hashlib.sha256(source.encode()).hexdigest(),original_process_record=actor['process_record'],actual_actor_final_state=actor['actor_final_state'],actual_return_record_exists=actor['return_record_exists'])
  result.update(initial_source_and_memory_binding_verified=True,binding_record=actor['binding_record'])
  result['qualified_return_location']=bool(result.get('all_recorded_calls_matched') and result['terminal']=='returned' and actor['return_record_exists'])
  out.append(result)
 result=dict(state='completed',cases=out,native_episodes=0,api_calls=0,gpu_used=False,qualified_return_locations=sum(x['qualified_return_location'] for x in out),scope='Exact code plus initial harness memory, recorded candidate-visible RPC replies. Does not prove unobserved dynamics; mismatches remain unqualified.')
 destination=P/'analysis/source-stop-replay-v2.json';assert not destination.exists()
 destination.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(dict(cases=len(out),qualified=result['qualified_return_locations'])))
if __name__=='__main__':
 if sys.argv[1]=='--worker':worker()
 else:main(sys.argv[1])
