"""Immutable per-task binding of saved policies, layouts and runtime."""
import ast, copy, json, shutil, sys
from pathlib import Path
O=Path(__file__).resolve().parent; R=O.parents[1]
I=R/'result/25_system2_integration_20261030T050100Z/integration-sources'
P=R/'result/45_search_execution_controls_20261107/parent'
sys.path[:0]=[str(O/'code'),str(I),str(I/'framework-validation-v3')]
from PhysicalRSI_core.infra.storage import atomic_json,read_json,file_digest
from PhysicalRSI_core.self_harness.artifacts import verify_harness
from PhysicalRSI_baselines.robodojo.native_runtime import NativeRuntime
from PhysicalRSI_baselines.robodojo.workflow import manifest
from PhysicalRSI_baselines.robodojo.evidence import verify_case

def audit(source):
    errors=[]
    try:t=ast.parse(source)
    except SyntaxError as e:return dict(admitted=False,errors=[str(e)])
    if len(t.body)!=1 or not isinstance(t.body[0],ast.FunctionDef) or t.body[0].name!='policy':errors.append('Expected only policy function at module scope')
    for n in ast.walk(t):
        if isinstance(n,(ast.Import,ast.ImportFrom,ast.ClassDef,ast.Global,ast.Nonlocal,ast.AsyncFunctionDef,ast.Await,ast.Yield,ast.YieldFrom)):errors.append(type(n).__name__)
        if isinstance(n,ast.Attribute) and n.attr.startswith('_'):errors.append('private attribute '+n.attr)
        if isinstance(n,ast.Name) and (n.id.startswith('__') or n.id in ['open','eval','exec','compile','globals','locals','vars','getattr','setattr','delattr','type','object','breakpoint','input','help']):errors.append('forbidden capability '+n.id)
        if isinstance(n,ast.Attribute) and isinstance(n.value,ast.Name) and n.value.id=='robot' and n.attr not in ['scene','approach','gripper','reobserve']:errors.append('robot capability '+n.attr)
        if isinstance(n,ast.FunctionDef) and n.decorator_list:errors.append('decorator')
    return dict(admitted=not errors,errors=sorted(set(errors)))

def config(task,phase_root,name):
    cfg=read_json(P/'runtimes/fixed_parent.json')
    files={str(p):file_digest(p) for p in (phase_root/'code').glob('*.py')}
    evidence=phase_root/'driver-contract-provenance/code_execution.py';files[str(evidence)]=file_digest(evidence)
    for field in ['files','policy_files']:cfg[field].update(files)
    cfg['policy_spec']['files'].update(files)
    cfg['policy_spec']['entrypoint']='pickup_adapter:assemble' if task=='general_pickup' else 'structured_feedback:assemble'
    cfg['policy_spec']['configuration']['output']=str(phase_root/'backend-traces'/name)
    cfg['policy_spec']['completion_hold_steps']={'general_pickup':200,'classify_objects':1100}[task]
    for field in ['policy_environment','simulator_environment']:
        cfg[field]['PYTHONPATH']=str(phase_root/'code')+':'+cfg[field]['PYTHONPATH']
    cfg['simulator_environment']['PHYSICALRSI_SIDECAR_ROOT']=str(phase_root/'sim-diagnostics'/name)
    cfg['skill_api']=read_json(O/'interfaces'/f'{task}.json')
    return cfg

def main(phase):
    plan=read_json(O/(phase+'-plan.json'));task=plan['task'];D=O/phase;D.mkdir()
    old=read_json(P/'native-campaign/campaign.json');parent=old['entries'][0]
    assert verify_harness(parent['harness'])==parent['harness_sha256']
    cases=plan['cases'];layout_root=plan['layout_root']
    for case in cases:
        assert case['task']==task
        verify_case(case,layout_root)
    shutil.copytree(O/'code',D/'code')
    shutil.copytree(P/'driver-contract-provenance',D/'driver-contract-provenance')
    for name in ['run_native.py','analyze_native.py']:
        shutil.copy2(O/'templates'/name,D/name)
    sys.path.insert(0,str(D/'code'))
    protocol=O/('protocol.json' if (O/'protocol.json').exists() else 'protocol-draft.json')
    atomic_json(D/'protocol.json',dict(campaign_protocol=str(protocol),campaign_sha256=file_digest(protocol),phase=phase,plan=plan))
    C=D/'native-campaign';C.mkdir();entries=[];audits=[]
    for row in plan['entries']:
        name=row['name'];src=O/row['source'] if row.get('source') else None
        if src and not src.is_file():
            audits.append(dict(name=name,admitted=False,reason='No parsed source',native_score=None));continue
        check=audit(src.read_text()) if src else dict(admitted=True,errors=[])
        audits.append(dict(name=name,source_sha256=file_digest(src) if src else None,**check))
        if not check['admitted']:continue
        cfg=config(task,D,name);rp=D/'runtimes'/(name+'.json');rp.parent.mkdir(exist_ok=True);atomic_json(rp,cfg)
        runtime=NativeRuntime(cfg);target=C/'harnesses'/name
        shutil.copytree(parent['harness']['root'],target,symlinks=False)
        atomic_json(target/'assets.json',runtime.identity())
        for p in (target/'code').glob('*.py'):p.unlink()  # Only this new harness copy.
        if src:
            shutil.copy2(src,target/'code'/f'{task}.py')
            expert=dict(name='code.'+task,revision=file_digest(src))
            skills={expert['name']:dict(revision=expert['revision'],source=f'code/{task}.py')}
        else:
            expert=copy.deepcopy(cfg['experts'][row['expert']]['expert']);skills={}
        atomic_json(target/'skills.json',skills)
        atomic_json(target/'skill_selection.json',dict(skill_choices={task:expert}))
        memories={}
        if row.get('proposal'):
            proposal=read_json(O/row['proposal']);assert proposal['source']==src.read_text();memories[task]=proposal['memory']
        elif task=='classify_objects':
            memories=read_json(Path(parent['harness']['root'])/'memory_rules.json')
        atomic_json(target/'memory_rules.json',memories)
        conf=read_json(target/'configuration.json');conf['tasks']=[task];atomic_json(target/'configuration.json',conf)
        atomic_json(target/'tools.json',cfg['skill_api'])
        h=manifest(target,'multitask_'+phase+'_'+name);revision=verify_harness(h)
        check=runtime.check();atomic_json(D/'native-preparation'/name/'check.json',check);assert check['ready'],check
        admit=runtime.admit(h,D/'native-preparation/admission'/name);audits[-1]['native_admission']=admit
        if not admit['accepted']:audits[-1]['admitted']=False;continue
        entries.append(dict(name=name,expert=expert,harness=h,harness_sha256=revision,runtime=str(rp),runtime_sha256=file_digest(rp),source_sha256=file_digest(src) if src else None,origin=row))
    atomic_json(D/'native-preparation/candidate-audit.json',audits)
    atomic_json(C/'campaign.json',dict(protocol=str(D/'protocol.json'),protocol_sha256=file_digest(D/'protocol.json'),runtime=entries[0]['runtime'] if entries else None,runtime_sha256=entries[0]['runtime_sha256'] if entries else None,per_entry_runtime=True,layout_root=layout_root,cases=cases,entries=entries,planned_cases=len(cases)*len(entries),api_calls=0,selection=plan['selection'],raw_task_budget_unchanged={'general_pickup':200,'classify_objects':1100}[task]))
    print(json.dumps(dict(phase=phase,admitted=len(entries),native_cases=len(cases)*len(entries),rejected=len(audits)-len(entries))))
if __name__=='__main__':main(sys.argv[1])
