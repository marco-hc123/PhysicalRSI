"""Focused synthetic response-contract checks, no physics or paid calls."""
import ast,builtins,copy,datetime,hashlib,importlib.util,inspect,json,os,resource
from pathlib import Path
P=Path('/mnt/data/joey_tr/physical-RSI');R=P/'result/33_system2_capability_feedback/20261106_v1';O=R/'error-contract-check'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):p=O/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
assert not (O/'summary.json').exists();O.mkdir(exist_ok=True)
m=load('contract_mock',P/'result/27_system2_offline_diagnostics/20261104_cpu_v1/run_cpu_batch.py');m.OUT=O
N=P/'result/32_system2_lift_gate_diagnosis/20261106_v1/native-validation'
source_actor=next(a for a in read(N/'analysis/matrix-analysis.json')['actors'] if a['condition']=='bypass_lift_guard' and a['mapped_layout_id']==0)
source_path=N/source_actor['process_record'];proc=read(source_path)
record=next(c for c in proc['calls'] if c.get('response',{}).get('value',{}).get('primitive_error')=='no_collision_free_path')
error_response=record['response']['value']
resource.setrlimit(resource.RLIMIT_CORE,(0,0));resource.setrlimit(resource.RLIMIT_AS,(768*1024*1024,768*1024*1024));resource.setrlimit(resource.RLIMIT_CPU,(60,60))
os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1');save('write-isolation.json',m.guard())
safe=['abs','all','any','bool','dict','enumerate','float','int','isinstance','iter','len','list','max','min','next','range','reversed','round','set','sorted','str','sum','tuple','zip','Exception','RuntimeError','ValueError','TypeError','KeyError','IndexError','TimeoutError']
m.SAFE_BUILTINS={n:getattr(builtins,n) for n in safe}
src=inspect.getsource(m.probe).replace('scope={};exec',"scope={'__builtins__': SAFE_BUILTINS};exec")
exec(compile(src,'<restricted-probe>','exec'),m.__dict__)
Original=m.Robot
class ContractRobot(Original):
 def call(self,method,**kw):
  if method!='approach':return super().call(method,**kw)
  previous=self.action_mode;self.action_mode='prefix'
  try:super().call(method,**kw)
  except m.ProbeStop:pass
  finally:self.action_mode=previous
  row=self.calls[-1];count=sum(x['method']=='approach' for x in self.calls)
  if previous=='uncertain_timeout':row['error']='synthetic uncertain execution timeout';raise TimeoutError(row['error'])
  if previous=='first_reject_then_boundary' and count>1:row['unexecuted']=True;raise m.ProbeStop('Next approach requested; no post-intervention motion or observation invented')
  value=copy.deepcopy(error_response)
  if previous=='unknown_error':value['primitive_error']='synthetic_unknown_error'
  row['output']=value;row['qualification']='Injected recorded response schema on a synthetic scene; zero physical execution';return value
m.Robot=ContractRobot
modes=['explicit_zero_execution_no_path','uncertain_timeout','unknown_error','first_reject_then_boundary']
save('protocol.json',dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='24 response-schema fixture executions; not recorded trajectory replay, solver feasibility or native task results',
 original_fixture_limitation='Earlier named_no_path fixture throws RuntimeError (legacy description); it does not test current compatibility adapter error dictionaries. Both records are preserved.',
 source_response=dict(path=str(source_path),sha256=sha(source_path),call_id=record['request']['id'],value=error_response),modes=modes,
 hypotheses=['Capability candidates request at most one alternate-arm attempt after explicit zero-execution no-path','Both arms stop on uncertain exception and unknown error','First-reject/boundary test never supplies a fabricated successful response'],new_api_calls=0,new_gpu_calls=0,new_native_cases=0))
rows=[]
for entry in read(R/'ledger.json'):
 p=R/'candidates'/entry['id']/'candidate.py';proposal=read(p.parent/'proposal.json');assert sha(p)==entry['source_sha256']
 for mode in modes:
  res=m.probe(p.read_text(),[m.NAMED],mode,memory=proposal['memory']);save('cases/'+entry['id']+'__'+mode+'.json',res)
  actions=[c for c in res['calls'] if c['method']=='approach']
  rows.append(dict(candidate=entry['id'],arm=entry['arm'],fixture=mode,terminal=res['terminal'],approach_requests=len(actions),approach_arms=[a['input']['arm'] for a in actions],invalid_requests=len(res['invalid_calls']),physical_execution_count=0,full_trace='cases/'+entry['id']+'__'+mode+'.json'))
save('results.json',rows)
summary=dict(state='completed',cpu_fixture_cases=len(rows),new_native_cases=0,new_api_calls=0,
 by_condition={arm:{mode:[r['approach_requests'] for r in rows if r['arm']==arm and r['fixture']==mode] for mode in modes} for arm in ['legacy_feedback','capability_feedback']},
 hypotheses_held=all(r['approach_requests']==(2 if r['arm']=='capability_feedback' and r['fixture'] in ['explicit_zero_execution_no_path','first_reject_then_boundary'] else 1) for r in rows),
 interpretation='Verifies generated branching under explicit response contracts, not safe recovery, completed movement or improved task score.')
save('summary.json',summary);print(json.dumps(summary))
