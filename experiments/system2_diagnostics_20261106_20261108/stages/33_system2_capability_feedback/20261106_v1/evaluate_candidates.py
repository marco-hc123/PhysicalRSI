"""Bounded CPU diagnostics; preserve generated source and memory unchanged."""
import ast,builtins,copy,hashlib,importlib.util,inspect,json,os,resource
from pathlib import Path
R=Path('/mnt/data/joey_tr/physical-RSI');A=R/'result/33_system2_capability_feedback/20261106_v1';O=A/'offline-validation'
C=R/'result/27_system2_offline_diagnostics/20261104_cpu_v1'
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def read(p):return json.loads(p.read_text())
def save(n,v):p=O/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert read(A/'status.json')['state']=='generation_complete'
assert not (O/'completion.json').exists()
O.mkdir(exist_ok=True)
m=load('cpu',C/'run_cpu_batch.py');m.OUT=O
# Use the same narrowly scoped admission rules as the previous diagnostic batch.
def audit(source):
 t=ast.parse(source);errors=[]
 if len(t.body)!=1 or not isinstance(t.body[0],ast.FunctionDef) or t.body[0].name!='policy':errors.append('Expected only policy function at module scope')
 for n in ast.walk(t):
  if isinstance(n,(ast.Import,ast.ImportFrom,ast.ClassDef,ast.Global,ast.Nonlocal,ast.AsyncFunctionDef,ast.Await,ast.Yield,ast.YieldFrom)):errors.append(type(n).__name__)
  if isinstance(n,ast.Attribute) and n.attr.startswith('_'):errors.append('private attribute '+n.attr)
  if isinstance(n,ast.Name) and (n.id.startswith('__') or n.id in ['open','eval','exec','compile','globals','locals','vars','getattr','setattr','delattr','type','object','breakpoint','input','help']):errors.append('forbidden capability '+n.id)
  if isinstance(n,ast.Attribute) and isinstance(n.value,ast.Name) and n.value.id=='robot' and n.attr not in ['scene','approach','gripper','reobserve']:errors.append('robot capability '+n.attr)
  if isinstance(n,ast.FunctionDef) and n.decorator_list:errors.append('decorator')
 return dict(admitted=not errors,errors=sorted(set(errors)))
resource.setrlimit(resource.RLIMIT_CORE,(0,0));resource.setrlimit(resource.RLIMIT_AS,(768*1024*1024,768*1024*1024));resource.setrlimit(resource.RLIMIT_CPU,(90,90))
os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1');save('write-isolation.json',m.guard())
safe=['abs','all','any','bool','dict','enumerate','float','int','isinstance','iter','len','list','max','min','next','range','reversed','round','set','sorted','str','sum','tuple','zip','Exception','RuntimeError','ValueError','TypeError','KeyError','IndexError','TimeoutError']
m.SAFE_BUILTINS={n:getattr(builtins,n) for n in safe}
source=inspect.getsource(m.probe);assert source.count('scope={};exec')==1
source=source.replace('scope={};exec',"scope={'__builtins__': SAFE_BUILTINS};exec")
save('protocol.json',dict(scope='CPU fixtures and recorded-scene first-action checks only, not native scores or unobserved dynamics',new_native_cases=0,new_api_calls=0,cases_per_candidate=20,prior_fixture_types=9,axis_aligned_geometry_cases=6,recorded_initial_scenes=5,generated_memory_passed=True,selection='No performance filtering; admitted candidates continue to native, including behaviorally unsuccessful ones.'))
(O/'restricted_probe.py').write_text(source);exec(compile(source,'<restricted-diagnostic-harness>','exec'),m.__dict__)
rows=[];audits=[];input_hashes=[]
for entry in read(A/'ledger.json'):
 name=entry['id'];p=A/'candidates'/name/'candidate.py'
 if not p.exists():audits.append(dict(candidate=name,admitted=False,errors=['No valid parsed candidate']));continue
 proposal=read(p.parent/'proposal.json');code=p.read_text();assert code==proposal['source'] and sha(p)==entry['source_sha256']
 a=dict(candidate=name,source_sha256=sha(p),proposal_sha256=sha(p.parent/'proposal.json'),**audit(code));audits.append(a)
 if not a['admitted']:continue
 fixtures=[]
 for f in ['empty','named_static','named_no_path','named_transport_error','dynamic_category','missing_pose','underscore_category','above_basket','insufficient_baskets']:
  fp=C/'fixtures'/(f+'.json');d=read(fp);fixtures.append((f,d['scenes'],d['action_mode']));input_hashes.append(dict(path=str(fp),sha256=sha(fp)))
 for f,x,y in [('center',0,0),('inside',.09,.07),('outside_x',.15,0),('outside_y',0,.12),('outside_both',.15,.12),('far',.3,0)]:fixtures.append(('geometry_'+f,[m.scene({'basket_1':m.basket(),'watch_1':m.obj(x,y)})],'prefix'))
 for layout in range(5):
  fp=C/f'followup_v2/ordered_scenes/layout{layout}.json';fixtures.append((f'initial_recorded_scene_{layout}',read(fp),'prefix'));input_hashes.append(dict(path=str(fp),sha256=sha(fp)))
 for f,scenes,mode in fixtures:
  result=m.probe(code,scenes,mode,memory=copy.deepcopy(proposal['memory']))
  save('cases/'+name+'__'+f+'.json',result)
  rows.append(dict(candidate=name,arm=entry['arm'],fixture=f,terminal=result['terminal'],error=result['error'],rpc_calls=len(result['calls']),invalid_calls=len(result['invalid_calls']),native_score=None))
 assert sha(p)==entry['source_sha256']
save('candidate-audit.json',audits);save('results.json',rows);save('input-manifest.json',list({r['path']:r for r in input_hashes}.values()))
completion=dict(state='completed',generated_candidates=len(audits),admitted=sum(x['admitted'] for x in audits),cpu_cases=len(rows),new_native_cases=0,new_api_calls=0,sources_unchanged=True)
save('completion.json',completion);print(json.dumps(completion))
