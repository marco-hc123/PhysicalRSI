"""Versioned CPU diagnostic study. No model calls or physical scoring."""
import ast, collections, copy, csv, ctypes, datetime, hashlib, io, json, math, os
from pathlib import Path
import signal, sys, time, traceback

ROOT = Path('/mnt/data/joey_tr/physical-RSI')
OUT = ROOT / 'result/27_system2_offline_diagnostics/20261104_cpu_v1'
DIAG = ROOT / 'result/21_system2_failure_mechanisms/36_system2_mechanism_20261031T010000Z_v3'
ITER = ROOT / 'result/17_system2_iterations'
RUNS = ['29_system2_api_20261030T101800Z', '31_system2_final_validation_20261030T121000Z']
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(b): return hashlib.sha256(b).hexdigest()
def write(name, data):
    p=OUT/name; p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def read(p): return json.loads(Path(p).read_text())
def table(name, rows):
    with (OUT/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def guard():
    lib=ctypes.CDLL(None,use_errno=True);abi=lib.syscall(444,0,0,1)
    if abi<3:raise RuntimeError('Landlock ABI>=3 required; no unconfined execution')
    class Rules(ctypes.Structure): _fields_=[('rights',ctypes.c_uint64)]
    class Beneath(ctypes.Structure):
        _pack_=1;_fields_=[('rights',ctypes.c_uint64),('fd',ctypes.c_int32)]
    rights=(1<<1)|sum(1<<n for n in range(4,15))
    rules=Rules(rights);fd=lib.syscall(444,ctypes.byref(rules),ctypes.sizeof(rules),0)
    if fd<0:raise OSError(ctypes.get_errno(),'Landlock create')
    for path,access in [(OUT,rights),(Path('/dev/null'),(1<<1)|(1<<14))]:
        pfd=os.open(path,os.O_PATH|os.O_CLOEXEC);rule=Beneath(access,pfd)
        if lib.syscall(445,fd,1,ctypes.byref(rule),0)<0:raise OSError(ctypes.get_errno(),'Landlock rule')
        os.close(pfd)
    if lib.prctl(38,1,0,0,0)!=0 or lib.syscall(446,fd,0)!=0:raise OSError(ctypes.get_errno(),'Landlock enforce')
    os.close(fd)
    return {'abi':abi,'filesystem_mutation_allowed':[str(OUT),'/dev/null'],'no_privileged_operations':True}

class ProbeStop(BaseException): pass
class BudgetStop(BaseException): pass
class ProbeTimeout(BaseException): pass
def alarm(*args):raise ProbeTimeout('CPU probe time budget')
signal.signal(signal.SIGALRM,alarm)

def obj(x,y,z=.79,dims=None):return {'pose':[x,y,z,1.,0.,0.,0.],'dims':dims or [.05,.04,.05]}
def scene(objects):return {'frame':'world','unit':'m','objects':objects}
def basket(x=0,y=0):return obj(x,y,.8,[.2,.15,.07])
NAMED=scene({'basket_1':basket(),'watch_1':obj(.3,-.2)})

class Robot:
    def __init__(self, scenes, action_mode='success', max_calls=100):
        self.scenes=scenes;self.action_mode=action_mode;self.max_calls=max_calls
        self.calls=[];self.scene_index=0;self.invalid=[]
    def call(self,method,**kw):
        if len(self.calls)>=self.max_calls:raise BudgetStop('RPC budget reached')
        row={'index':len(self.calls),'method':method,'input':copy.deepcopy(kw)};self.calls.append(row)
        if method=='scene':
            v=copy.deepcopy(self.scenes[min(self.scene_index,len(self.scenes)-1)]);self.scene_index+=1
            row['output']=v;return v
        if method=='approach':
            p=kw.get('position_m');q=kw.get('quaternion_wxyz')
            valid=(kw.get('arm') in ['left','right'] and isinstance(p,list) and len(p)==3 and isinstance(q,list) and len(q)==4 and all(isinstance(x,(int,float)) and math.isfinite(x) for x in p+q))
            if valid:valid=abs(sum(x*x for x in q)-1)<.005
            if not valid:self.invalid.append(row['index']);raise ValueError('invalid approach contract')
            if self.action_mode=='prefix':raise ProbeStop('First approach observed; no physical action simulated')
            if self.action_mode=='no_path':row['error']='no_collision_free_path';raise RuntimeError('No collision-free path; no action executed by this call')
            if self.action_mode=='transport_error':row['error']='transport_timeout';raise TimeoutError('injected transport timeout')
        if method=='gripper' and (kw.get('arm') not in ['left','right'] or kw.get('command') not in [0,1]):
            self.invalid.append(row['index']);raise ValueError('invalid gripper contract')
        row['output']={'state':{'synthetic':True},'qualification':'mock acknowledgement, no measured motion'}
        return copy.deepcopy(row['output'])
    def scene(self):return self.call('scene')
    def approach(self,**kw):return self.call('approach',**kw)
    def gripper(self,**kw):return self.call('gripper',**kw)
    def reobserve(self):return self.call('reobserve')

def probe(source, scenes, mode='success', memory=None):
    tree=ast.parse(source)
    if any(isinstance(x,(ast.Import,ast.ImportFrom)) for x in ast.walk(tree)):raise ValueError('Unexpected candidate import')
    scope={};exec(compile(tree,'<audited-candidate>','exec'),scope)
    robot=Robot(scenes,mode);mem=copy.deepcopy(memory or {});terminal='returned';err=None;value=None
    signal.setitimer(signal.ITIMER_REAL,2)
    try:value=scope['policy'](robot,mem)
    except ProbeStop as e:terminal='prefix_observed';err=str(e)
    except BudgetStop as e:terminal='budget_exhausted';err=str(e)
    except ProbeTimeout as e:terminal='cpu_timeout';err=str(e)
    except Exception as e:terminal='exception';err=type(e).__name__+': '+str(e)
    finally:signal.setitimer(signal.ITIMER_REAL,0)
    return {'terminal':terminal,'error':err,'return_value':value,'calls':robot.calls,'counts':dict(collections.Counter(x['method'] for x in robot.calls)),'invalid_calls':robot.invalid,'memory_after_in_process':mem,'native_score':None,'scope':'CPU fixture only; no physics, no new robot episode'}

def exact_driver_probe(driver, source, memory, primitive_output):
    """Run exact driver text against virtual IO; not a chroot/security qualification."""
    storage={'/input.json':json.dumps({'source':source,'memory':copy.deepcopy(memory)}),'/response.json':'{}'}
    class Virtual(io.StringIO):
        def __init__(self,path,mode):self.path=path;self.mode=mode;super().__init__(storage.get(path,'') if 'r' in mode else '')
        def close(self):
            if not self.closed and 'w' in self.mode:
                storage[self.path]=self.getvalue()
                message=json.loads(self.getvalue())
                if message.get('kind')=='call':storage['/response.json']=json.dumps({'id':message['id'],'value':primitive_output})
            super().close()
    def vopen(path,mode='r',*a,**k):
        if path not in ['/input.json','/response.json','/output/result.json']:raise PermissionError(path)
        return Virtual(path,mode)
    import builtins
    b=dict(vars(builtins));b['open']=vopen
    scope={'__builtins__':b};exec(compile(driver,'<exact-recorded-driver>','exec'),scope)
    return json.loads(storage['/output/result.json'])

def main():
    if (OUT/'completion.json').exists():raise RuntimeError('Completed batch exists; do not rerun or overwrite')
    OUT.mkdir(parents=True,exist_ok=True)
    isolation=guard();write('write-isolation.json',isolation)
    for n in ['tmp','cache','cache/xdg']:(OUT/n).mkdir(parents=True,exist_ok=True)
    os.environ.update(PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',TMPDIR=str(OUT/'tmp'),XDG_CACHE_HOME=str(OUT/'cache/xdg'))
    status={'started_utc':now(),'pid':os.getpid(),'state':'running','phase':'protocol','gpu_jobs':0,'api_calls':0,'native_episodes':0}
    def progress(phase):status.update(phase=phase,updated_utc=now());write('status.json',status);print(phase,flush=True)
    progress('protocol')
    write('protocol.json',{'version':'cpu-diagnostics/v1','created_utc':now(),'goal':'Localize candidate failure and verify offline contract semantics before native intervention','scope':'Existing candidates and supplied synthetic/recorded observations only; zero new native scores','hypotheses':['H1 overbroad round2 basket predicate skips outside points','H2 newly observed categories can trigger round2 KeyError','H3 static observations can exhaust the admitted RPC prefix budget','H4 recorded driver converts recoverable no-path but does not publish mutated memory'],'fixed':['original candidate hashes','100 RPC fixture budget','unchanged historical native score and runtime'],'treatments':['Only replace round2 XY predicate with half-dimensions, axis-aligned diagnostic assumption','Only extend round2 category assignment when a free basket exists','Only add mutated memory to copied driver result schema'],'exclusions':['No hardware motion, perception truth, robot success, task score, generation quality or full isolation-backend claim'],'future_evaluation':'Historical diagnostic layouts are development evidence; reserve previously unseen layouts before native acceptance','gpu_permission':'Separate pending user confirmation; this script always CPU only','write_scope':str(OUT)})
    sources={};manifest=[]
    for i,run in enumerate(RUNS,1):
        p=ITER/run/'workspace/rounds/round-000000/candidate/code/classify_objects.py';b=p.read_bytes();sources['qwen_round'+str(i)]=b.decode();manifest.append({'role':'candidate','path':str(p),'sha256':sha(b),'bytes':len(b)})
    p=ROOT/'result/25_system2_model_swap/38_system2_gpt61sol_20261102/model-candidate.py';b=p.read_bytes();sources['gpt_candidate']=b.decode();manifest.append({'role':'candidate','path':str(p),'sha256':sha(b),'bytes':len(b)})
    expected=['a425b904c62f1637c040765e23e49a180e4b4803c04109ce10f7b5a16346e4e8','3a0fc9f9dc6d8b49ff6a5b234feca660f4d8cc5e4259c36d4a273f9802068195']
    assert [sha(sources['qwen_round'+str(i)].encode()) for i in [1,2]]==expected
    for name,src in sources.items():
        p=OUT/'candidates'/f'{name}.py';p.parent.mkdir(exist_ok=True);p.write_text(src)
    write('source-manifest.json',manifest)
    progress('historical_evidence')
    mapping=read(ROOT/'configs/organization/path-mapping.json')['mapping']
    def mapped(p):
        s=str(p).removeprefix('/mnt/data/physical-RSI/')
        for k in sorted(mapping,key=len,reverse=True):
            if s==k or s.startswith(k+'/'):return ROOT/(mapping[k]+s[len(k):])
        raise ValueError('Unmapped source: '+str(p))
    audit=read(DIAG/'historical-candidate-audit.json');historical=[];observations=[];fingerprints=[];trace_examples=[]
    for row in audit:
        base=mapped(row['path']);episodes=list((base/'episodes').glob('*.json'));assert len(episodes)==1
        ep=read(episodes[0]);counts=collections.Counter();no_path=0;scenes=[]
        for f in sorted(base.glob('model/expert/*/0/execution/rpc/*.json')):
            raw=f.read_bytes();v=json.loads(raw);fingerprints.append({'path':str(f),'sha256':sha(raw),'bytes':len(raw)})
            counts[v.get('method')]+=1
            if isinstance(v.get('output'),dict) and v['output'].get('primitive_error')=='no_collision_free_path':
                no_path+=1
                if row['round']==2:trace_examples.append({'layout':row['layout'],'source':str(f),'receipt':v})
            if v.get('method')=='scene' and isinstance(v.get('output'),dict):scenes.append({'path':str(f),'value':v['output']})
        scene_values=[x['value'] for x in scenes]
        if row['round']==2 and scenes:trace_examples.append({'layout':row['layout'],'source':scenes[0]['path'],'recorded_scene':scenes[0]['value']})
        observations.append({'round':row['round'],'layout':row['layout'],'scenes':scenes})
        assert ep['revision']==expected[row['round']-1]
        historical.append({'round':row['round'],'layout':row['layout'],'candidate_sha256':ep['revision'],'native_state':ep.get('state'),'native_score':ep.get('episode_score'),'native_success':ep.get('success'),'scene_calls':counts['scene'],'approach_calls':counts['approach'],'gripper_calls':counts['gripper'],'no_path_count':no_path,'historical_completed_primitive_steps':row.get('completed_primitive_action_steps'),'historical_policy_result_exists':row.get('policy_result',{}).get('exists'),'scope':'Reanalysis of old native evidence, zero new episodes'})
        if scene_values:write(f'fixtures/recorded_round{row["round"]}_layout{row["layout"]}.json',scene_values)
    table('historical-failure-points.csv',historical);write('historical-failure-points.json',historical);write('historical-rpc-fingerprints.json',fingerprints)
    progress('candidate_fixture_matrix')
    dynamic0=scene({'basket_1':basket(),'basket_2':basket(-.3,0),'watch_1':obj(.3,-.2)})
    dynamic1=scene({'basket_1':basket(),'basket_2':basket(-.3,0),'pen_1':obj(.3,-.2)})
    fixture_defs=[('empty',[scene({})],'success'),('named_static',[NAMED],'success'),('named_no_path',[NAMED],'no_path'),('named_transport_error',[NAMED],'transport_error'),('dynamic_category',[dynamic0,dynamic1],'prefix'),('missing_pose',[scene({'basket_1':basket(),'watch_1':{'dims':[.05,.05,.05]}})],'prefix'),('underscore_category',[scene({'basket_1':basket(),'toy_car_1':obj(.3,-.2)})],'prefix'),('above_basket',[scene({'basket_1':basket(),'watch_1':obj(0,0,1.3)})],'prefix'),('insufficient_baskets',[scene({'basket_1':basket(),'watch_1':obj(.3,-.2),'pen_1':obj(.4,-.2)})],'prefix')]
    matrix=[]
    for name,seq,mode in fixture_defs:
        write('fixtures/'+name+'.json',{'scenes':seq,'action_mode':mode})
        for candidate,source in sources.items():
            result=probe(source,seq,mode);write('fixture_results/'+candidate+'__'+name+'.json',result)
            matrix.append({'candidate':candidate,'fixture':name,'terminal':result['terminal'],'error':result['error'],'scene_calls':result['counts'].get('scene',0),'approach_calls':result['counts'].get('approach',0),'gripper_calls':result['counts'].get('gripper',0),'invalid_calls':len(result['invalid_calls']),'native_score':None})
    table('candidate-fixture-matrix.csv',matrix)
    progress('single_variable_repairs')
    original=sources['qwen_round2'];old='if abs(item_x - b_x) < 0.2 and abs(item_y - b_y) < 0.2:'
    assert original.count(old)==1
    bbox=original.replace(old,'if abs(item_x - b_x) < b_data["dims"][0] / 2 and abs(item_y - b_y) < b_data["dims"][1] / 2:')
    marker='        basket_key = basket_assignment[category]';assert original.count(marker)==1
    category=original.replace(marker,'        if category not in basket_assignment:\n            free_baskets = [b for b in basket_list if b not in basket_assignment.values()]\n            if not free_baskets:\n                failed_items.add(key)\n                continue\n            basket_assignment[category] = free_baskets[0]\n'+marker)
    (OUT/'candidates/round2_bbox_only.py').write_text(bbox);(OUT/'candidates/round2_category_only.py').write_text(category)
    repairs=[]
    for label,x,y,inside in [('center',0,0,True),('inside',.09,.07,True),('outside_x',.15,0,False),('outside_y',0,.12,False),('outside_both',.15,.12,False),('far',.3,0,False)]:
        sc=scene({'basket_1':basket(),'watch_1':obj(x,y)})
        for name,source in [('original',original),('bbox_only',bbox)]:
            result=probe(source,[sc],'prefix');write('repair_results/'+name+'__'+label+'.json',result)
            attempted=result['counts'].get('approach',0)>0
            repairs.append({'test':label,'variant':name,'expected_attempt_under_axis_aligned_center_fixture':not inside,'observed_attempt':attempted,'contract_match':attempted==(not inside),'terminal':result['terminal'],'native_score':None})
    for name,source in [('original',original),('category_only',category)]:
        result=probe(source,[dynamic0,dynamic1],'prefix');write('repair_results/'+name+'__dynamic_category.json',result)
        repairs.append({'test':'dynamic_category','variant':name,'expected_attempt_under_axis_aligned_center_fixture':None,'observed_attempt':result['counts'].get('approach',0)>0,'contract_match':result['terminal']=='prefix_observed','terminal':result['terminal'],'native_score':None})
    table('single-variable-repairs.csv',repairs)
    recorded=[]
    for v in observations:
        if v['round']!=2 or not v['scenes']:continue
        for name,source in [('original',original),('bbox_only',bbox)]:
            seq=[x['value'] for x in v['scenes']];result=probe(source,seq,'prefix');write(f'recorded_prefix/{name}_layout{v["layout"]}.json',result)
            recorded.append({'layout':v['layout'],'variant':name,'terminal':result['terminal'],'approach_requests':result['counts'].get('approach',0),'qualification':'Historical observations + mock stop before first action; not physical replay','native_score':None})
    table('recorded-observation-prefix.csv',recorded)
    progress('driver_semantics')
    driver_path=ROOT/'result/16_system2_integration/25_system2_integration_20261030T050100Z/integration-sources/framework-validation-v3/PhysicalRSI_baselines/robodojo/code_execution.py'
    driver_file=driver_path.read_text();tree=ast.parse(driver_file)
    driver=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='_DRIVER' for t in n.targets))
    base_source='def policy(robot, memory):\n    memory["counter"] = memory.get("counter", 0) + 1\n    return None\n'
    original_payload=exact_driver_probe(driver,base_source,{}, {})
    fixed_driver=driver.replace("_publish(dict(kind='result', value=_value))","_publish(dict(kind='result', value=_value, memory=_input['memory']))")
    assert fixed_driver!=driver
    m={};roundtrip=[]
    for i in range(2):
        payload=exact_driver_probe(fixed_driver,base_source,m,{});m=payload['memory'];roundtrip.append(payload)
    no_path_source='def policy(robot, memory):\n    try:\n        robot.approach()\n    except RuntimeError:\n        return {"caught_no_path": True}\n    return {"caught_no_path": False}\n'
    no_path_payload=exact_driver_probe(driver,no_path_source,{}, {'primitive_error':'no_collision_free_path'})
    memory_result={'driver_sha256':sha(driver_file.encode()),'scope':'Exact recorded driver string with virtual IO; no process-isolation qualification','original_payload':original_payload,'mutated_memory_published_original':'memory' in original_payload,'memory_schema_prototype_roundtrip':roundtrip,'recoverable_no_path_payload':no_path_payload,'native_score':None,'meaning':'Explicit memory-return schema prototype only, not deployed or evidence of VLA sparse-memory failure'}
    write('driver-memory-and-error-contract.json',memory_result);(OUT/'candidates/driver_memory_return_prototype.txt').write_text(fixed_driver)
    assert 'memory' not in original_payload and m['counter']==2 and no_path_payload['value']['caught_no_path'] is True
    progress('feedback_packets')
    request=read(ITER/RUNS[1]/'workspace/rounds/round-000000/proposals/classify_objects/request.json')
    write('feedback/baseline_structured_request.json',request)
    failed_history={'source_type':'rejected_candidate_history','selected_parent':'pi05; unchanged','candidate_source':original,'candidate_sha256':sha(original.encode()),'historical_native_evidence':[x for x in historical if x['round']==2],'recorded_rpc_examples':trace_examples,'trace_sources':[x for x in fingerprints if RUNS[1] in x['path']],'warnings':['Historical validation layouts used here become development/diagnostic evidence; not future held-out evaluation','CPU fixtures and manual repairs are excluded from this feedback packet','No hidden simulator ground truth or hand-written repaired code included']}
    enhanced=copy.deepcopy(request);enhanced['diagnostic_history']=failed_history
    write('feedback/enhanced_request_design.json',enhanced)
    # Baseline transport does not automatically consume new fields: explicit adapter work is pending.
    write('feedback/paired-design.json',{'status':'prepared_not_submitted','baseline_bytes':len(json.dumps(request,ensure_ascii=False).encode()),'enhanced_bytes':len(json.dumps(enhanced,ensure_ascii=False).encode()),'actual_token_usage':None,'api_calls':0,'only_treatment':'Append attributed rejected-candidate code and historical failure records to an explicit prompt section','required_adapter_change':'Render diagnostic_history into a delimited user-message section; unknown JSON fields alone are not guaranteed to reach the model','fixed_conditions':['same selected pi05 parent','same model/settings','same generation count and output budget','same validation and selection rules'],'generation_and_native_comparison_status':'not_run','held_out_layouts':'must be selected after checking prior use; not the diagnostics above'})
    progress('verification')
    unchanged=[{'path':m['path'],'unchanged':sha(Path(m['path']).read_bytes())==m['sha256']} for m in manifest]
    assert all(x['unchanged'] for x in unchanged)
    expected_checks={'original_bbox_false_skip_reproduced':any(x['test']=='outside_x' and x['variant']=='original' and not x['contract_match'] for x in repairs),'bbox_fixture_all_six_matched':all(x['contract_match'] for x in repairs if x['variant']=='bbox_only'),'dynamic_category_error_reproduced':any(x['candidate']=='qwen_round2' and x['fixture']=='dynamic_category' and 'KeyError' in str(x['error']) for x in matrix),'dynamic_category_repair_reaches_action':next(x['contract_match'] for x in repairs if x['variant']=='category_only'),'static_scene_budget_exhaustion_reproduced':any(x['candidate']=='qwen_round2' and x['fixture']=='named_static' and x['terminal']=='budget_exhausted' for x in matrix),'driver_no_path_conversion_verified':no_path_payload['value']['caught_no_path'],'memory_prototype_roundtrip_verified':m['counter']==2 if isinstance(m,dict) and 'counter' in m else roundtrip[-1]['memory']['counter']==2,'sources_unchanged':all(x['unchanged'] for x in unchanged)}
    write('verification.json',{'checks':expected_checks,'sources':unchanged,'all_expected_checks_passed':all(expected_checks.values())})
    completion={'state':'complete' if all(expected_checks.values()) else 'complete_with_unmet_expectations','completed_utc':now(),'historical_candidate_episodes_reanalyzed':len(historical),'historical_rpc_records_read':len(fingerprints),'candidate_fixture_executions':len(matrix),'single_variable_fixture_executions':len(repairs),'recorded_observation_prefix_executions':len(recorded),'exact_driver_virtual_io_executions':4,'new_native_episodes':0,'api_calls':0,'gpu_jobs':0,'new_task_scores':0,'all_expected_checks_passed':all(expected_checks.values()),'privileged_isolation_backend':'Not exercised: joey_tr is non-root and unprivileged user-namespace mapping was denied; semantic harness does not replace production isolation gate','next':'Render controlled feedback prompts; API generation and any GPU acceptance require separate resources/credentials; native scoring requires RT-capable simulation host'}
    write('completion.json',completion);status.update(state=completion['state'],phase='complete',completed_utc=now(),pid=None);write('status.json',status)
    print(json.dumps(completion),flush=True)

if __name__=='__main__':
    try:main()
    except BaseException as e:
        if OUT.exists():
            write('failure.json',{'time':now(),'error':type(e).__name__+': '+str(e),'traceback':traceback.format_exc()})
            write('status.json',{'state':'failed','pid':None,'updated_utc':now(),'error':type(e).__name__+': '+str(e)})
        raise
