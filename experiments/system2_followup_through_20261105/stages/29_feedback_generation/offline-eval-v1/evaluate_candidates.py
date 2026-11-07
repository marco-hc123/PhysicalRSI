"""Bounded offline evaluation of six saved API candidates; not native scoring."""
import ast,builtins,collections,copy,csv,hashlib,importlib.util,inspect,json,os,resource,sys,time
from pathlib import Path
R=Path('/mnt/data/joey_tr/physical-RSI')
C=R/'result/27_system2_offline_diagnostics/20261104_cpu_v1'
A=R/'result/29_system2_feedback_api/20261104_v1'
O=A/'offline-eval-v1'
spec=importlib.util.spec_from_file_location('cpu_probe',C/'run_cpu_batch.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.OUT=O
def read(p):return json.loads(Path(p).read_text())
def save(name,v):m.write(name,v)
def table(name,rows):
 with (O/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def audit(source):
 t=ast.parse(source);errors=[]
 if len(t.body)!=1 or not isinstance(t.body[0],ast.FunctionDef) or t.body[0].name!='policy':errors.append('Expected only policy function at module scope')
 for n in ast.walk(t):
  if isinstance(n,(ast.Import,ast.ImportFrom,ast.ClassDef,ast.Global,ast.Nonlocal,ast.AsyncFunctionDef,ast.Await,ast.Yield,ast.YieldFrom)):errors.append(type(n).__name__)
  if isinstance(n,ast.Attribute) and n.attr.startswith('_'):errors.append('private attribute '+n.attr)
  if isinstance(n,ast.Name) and (n.id.startswith('__') or n.id in ['open','eval','exec','compile','globals','locals','vars','getattr','setattr','delattr','type','object','breakpoint','input','help']):errors.append('forbidden capability '+n.id)
  if isinstance(n,ast.Attribute) and isinstance(n.value,ast.Name) and n.value.id=='robot' and n.attr not in ['scene','approach','gripper','reobserve']:errors.append('robot capability '+n.attr)
  if isinstance(n,ast.FunctionDef) and n.decorator_list:errors.append('decorator')
 return {'admitted':not errors,'errors':sorted(set(errors)),'imports':[],'lines':len(source.splitlines()),'sha256':hashlib.sha256(source.encode()).hexdigest()}
def run(source,scenes,mode):
 predicates=[]
 def profile(frame,event,arg):
  if event=='return' and frame.f_code.co_filename=='<audited-candidate>' and frame.f_code.co_name in ['inside','inside_basket'] and isinstance(arg,bool):
   if len(predicates)<100:predicates.append({'function':frame.f_code.co_name,'result':arg})
 sys.setprofile(profile)
 try:result=m.probe(source,scenes,mode)
 finally:sys.setprofile(None)
 result['containment_predicate_returns']=predicates
 return result
def row(name,test,r):
 approaches=[c for c in r['calls'] if c['method']=='approach']
 return {'candidate':name,'arm':name.rsplit('_',1)[0],'test':test,'terminal':r['terminal'],'error':r['error'],'total_rpc':len(r['calls']),'scene_rpc':r['counts'].get('scene',0),'approach_rpc':len(approaches),'gripper_rpc':r['counts'].get('gripper',0),'invalid_rpc':len(r['invalid_calls']),'first_action_arm':approaches[0]['input'].get('arm') if approaches else None,'first_action_z':approaches[0]['input'].get('position_m',[None]*3)[2] if approaches else None,'predicate_true_count':sum(p['result'] for p in r['containment_predicate_returns']),'predicate_false_count':sum(not p['result'] for p in r['containment_predicate_returns']),'native_score':None}
def main():
 if (O/'completion.json').exists():raise RuntimeError('Completed evaluation exists; do not repeat')
 assert read(A/'status.json')['state']=='generation_complete'
 O.mkdir(parents=True,exist_ok=True);os.umask(0o077);os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1')
 resource.setrlimit(resource.RLIMIT_CORE,(0,0));resource.setrlimit(resource.RLIMIT_AS,(768*1024*1024,768*1024*1024));resource.setrlimit(resource.RLIMIT_CPU,(90,90))
 save('write-isolation.json',m.guard())
 safe_names=['abs','all','any','bool','dict','enumerate','float','int','isinstance','iter','len','list','max','min','next','range','reversed','round','set','sorted','str','sum','tuple','zip','Exception','RuntimeError','ValueError','TypeError','KeyError','IndexError','TimeoutError']
 m.SAFE_BUILTINS={n:getattr(builtins,n) for n in safe_names}
 source=inspect.getsource(m.probe);assert source.count('scope={};exec')==1
 restricted=source.replace('scope={};exec',"scope={'__builtins__': SAFE_BUILTINS};exec")
 (O/'restricted_probe.py').write_text(restricted);exec(compile(restricted,'<restricted-diagnostic-harness>','exec'),m.__dict__)
 ledger=read(A/'ledger.json');candidates={};audits=[]
 for entry in ledger:
  p=A/'candidates'/entry['id']/'candidate.py';s=p.read_text();a=audit(s);assert a['sha256']==entry['source_sha256'];a.update(candidate=entry['id'],source=str(p));audits.append(a)
  if a['admitted']:candidates[entry['id']]=s
 save('candidate-audit.json',audits)
 save('protocol.json',{'created_utc':m.now(),'scope':'Exploratory offline diagnostics on saved candidates; no API, GPU or robot episode','feedback_generation_protocol':str(A/'protocol.json'),'candidates':6,'fixture_matrix':{'candidates':6,'prior_fixture_types':9,'executions':54},'geometry_matrix':{'candidates':6,'axis_aligned_center_cases':6,'executions':36},'recorded_prefix_matrix':{'candidates':6,'previously_inspected_layouts':5,'executions':30},'total_planned_cpu_executions':120,'fixed':['same original 9 fixtures and 100-RPC budget','same 6 center-position geometry cases','same chronologically sorted historical scene streams','same capability-restricted harness'],'limitations':['These layouts and hypotheses are diagnostic development data, not heldout','No physical dynamics, grasp outcome, perception ground truth or task success measured','Graceful return is not task completion','Geometry expectation is only an axis-aligned center-footprint surrogate, not physical containment','Above-basket action absence can also come from height safety bounds; predicate returns recorded separately','No production executor security qualification from this restricted diagnostic harness','Treatment changes feedback content and context length together'],'execution_controls':['AST admission','no imports/private attributes or filesystem/network builtins','100 RPC cap','2-second wall timer per probe','768 MiB address-space limit','Landlock project output confinement']})
 assert len(candidates)==6, 'Review rejected candidate before testing; no weakening admission'
 fixture_rows=[];geometry_rows=[];prefix_rows=[];source_hashes=[]
 fixture_names=['empty','named_static','named_no_path','named_transport_error','dynamic_category','missing_pose','underscore_category','above_basket','insufficient_baskets']
 for f in fixture_names:
  p=C/'fixtures'/(f+'.json');d=read(p);source_hashes.append({'path':str(p),'sha256':m.sha(p.read_bytes())})
  for name,s in candidates.items():
   res=run(s,d['scenes'],d['action_mode']);save('fixture_results/'+name+'__'+f+'.json',res);fixture_rows.append(row(name,f,res))
 cases=[('center',0,0,True),('inside',.09,.07,True),('outside_x',.15,0,False),('outside_y',0,.12,False),('outside_both',.15,.12,False),('far',.3,0,False)]
 for f,x,y,inside in cases:
  sc=m.scene({'basket_1':m.basket(),'watch_1':m.obj(x,y)})
  for name,s in candidates.items():
   res=run(s,[sc],'prefix');save('geometry_results/'+name+'__'+f+'.json',res);rr=row(name,f,res);rr.update(expected_attempt_axis_aligned_center_only=not inside,observed_attempt=rr['approach_rpc']>0,surrogate_match=(rr['approach_rpc']>0)==(not inside));geometry_rows.append(rr)
 for layout in range(5):
  p=C/f'followup_v2/ordered_scenes/layout{layout}.json';scenes=read(p);source_hashes.append({'path':str(p),'sha256':m.sha(p.read_bytes())});assert [x['observation']['sequence'] for x in scenes]==sorted(x['observation']['sequence'] for x in scenes)
  for name,s in candidates.items():
   res=run(s,scenes,'prefix');save('recorded_prefix/'+name+f'__layout{layout}.json',res);rr=row(name,'layout'+str(layout),res);rr['layout']=layout;prefix_rows.append(rr)
 save('input-manifest.json',source_hashes)
 for name,rows in [('fixture-matrix',fixture_rows),('geometry-matrix',geometry_rows),('recorded-prefix-matrix',prefix_rows)]:save(name+'.json',rows);table(name+'.csv',rows)
 summary=[]
 for name in candidates:
  fs=[r for r in fixture_rows if r['candidate']==name];gs=[r for r in geometry_rows if r['candidate']==name];ps=[r for r in prefix_rows if r['candidate']==name]
  static=next(r for r in fs if r['test']=='named_static');above=next(r for r in fs if r['test']=='above_basket')
  summary.append({'candidate':name,'arm':name.rsplit('_',1)[0],'fixture_exceptions':sum(r['terminal']=='exception' for r in fs),'fixture_budget_exhaustions':sum(r['terminal']=='budget_exhausted' for r in fs),'invalid_rpc_total':sum(r['invalid_rpc'] for r in fs+gs+ps),'geometry_surrogate_matches':sum(r['surrogate_match'] for r in gs),'geometry_denominator':6,'recorded_prefixes_with_approach':sum(r['approach_rpc']>0 for r in ps),'prefix_denominator':5,'static_scene_rpc':static['total_rpc'],'static_scene_terminal':static['terminal'],'above_predicate_true':above['predicate_true_count'],'above_predicate_false':above['predicate_false_count'],'native_score':None})
 save('summary.json',summary);table('summary.csv',summary)
 checks={'executions':len(fixture_rows)+len(geometry_rows)+len(prefix_rows),'sources_unchanged':all(hashlib.sha256(Path(a['source']).read_bytes()).hexdigest()==a['sha256'] for a in audits),'scene_inputs_unchanged':all(m.sha(Path(x['path']).read_bytes())==x['sha256'] for x in source_hashes)}
 assert checks['executions']==120 and checks['sources_unchanged'] and checks['scene_inputs_unchanged']
 save('completion.json',{'state':'complete','finished_utc':m.now(),**checks,'new_api_calls':0,'new_gpu_calls':0,'new_native_episodes':0,'new_task_scores':0})
 print(json.dumps({'summary':summary,'verification':checks},indent=2))
if __name__=='__main__':main()
