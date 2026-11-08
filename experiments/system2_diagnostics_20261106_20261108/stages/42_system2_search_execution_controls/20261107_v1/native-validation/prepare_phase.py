"""Stage-local, immutable candidate/runtime binding; no global environment edits."""
import ast, copy, json, shutil, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent;R=ROOT.parents[1]
I=R/'result/25_system2_integration_20261030T050100Z/integration-sources'
P=R/'result/43_rejection_contract_20261107'
sys.path[:0]=[str(ROOT/'code'),str(I),str(I/'framework-validation-v3')]
from PhysicalRSI_core.infra.storage import atomic_json,read_json,file_digest
from PhysicalRSI_core.self_harness.artifacts import verify_harness
from PhysicalRSI_baselines.robodojo.native_runtime import NativeRuntime
from PhysicalRSI_baselines.robodojo.workflow import manifest
from PhysicalRSI_baselines.robodojo.evidence import verify_case
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
def main(phase):
 plan=read_json(ROOT/(phase+'-plan.json'));O=ROOT/phase;O.mkdir()
 old=read_json(P/'native-campaign/campaign.json');parent=old['entries'][0]
 assert verify_harness(parent['harness'])==parent['harness_sha256']
 cases=plan.get('cases',old['cases']);layout_root=plan.get('layout_root',old['layout_root'])
 for case in cases:verify_case(case,layout_root)
 shutil.copytree(ROOT/'code',O/'code');shutil.copytree(P/'driver-contract-provenance',O/'driver-contract-provenance')
 sys.path.insert(0,str(O/'code'))
 for name in ['run_native.py','analyze_native.py','validate_native.py','physical_metrics.py','selected_sidecars.py','diagnose_phase.py']:
  shutil.copy2(ROOT/'templates'/name,O/name)
 shutil.copytree(R/'result/44_skill_chain_floor_20261107/scoring-reference',O/'scoring-reference')
 shutil.copy2(R/'result/44_skill_chain_floor_20261107/analysis-criteria.json',O/'analysis-criteria.json')
 atomic_json(O/'protocol.json',dict(campaign_protocol=str(ROOT/'protocol.json'),campaign_sha256=file_digest(ROOT/'protocol.json'),phase=phase,plan=plan))
 C=O/'native-campaign';C.mkdir();entries=[];audits=[]
 for row in plan['entries']:
  name=row['name'];is_parent=row.get('parent',False)
  src=Path(parent['harness']['root'])/'code/classify_objects.py' if is_parent else ROOT/row['source']
  if not src.is_file():audits.append(dict(name=name,admitted=False,reason='No syntactically parsed proposal',native_score=None));continue
  proposal=read_json(ROOT/row['proposal']) if row.get('proposal') else None
  if proposal is not None:assert proposal['source']==src.read_text()
  check=audit(src.read_text());audits.append(dict(name=name,source_sha256=file_digest(src),**check))
  if not check['admitted']:continue
  cfg=copy.deepcopy(read_json(parent['runtime']))
  files={str(p):file_digest(p) for p in (O/'code').glob('*.py')}
  dp=O/'driver-contract-provenance/code_execution.py';files[str(dp)]=file_digest(dp)
  for key in ['files','policy_files']:cfg[key].update(files)
  cfg['policy_spec']['files'].update(files)
  cfg['policy_spec']['entrypoint']=row.get('entrypoint','structured_feedback:assemble')
  cfg['policy_spec']['configuration']['output']=str(O/'backend-traces'/name)
  cfg['policy_spec']['configuration'].update(row.get('configuration_updates',{}))
  for k in ['simulator_environment','policy_environment']:cfg[k]['PYTHONPATH']=str(O/'code')+':'+cfg[k]['PYTHONPATH']
  cfg['simulator_environment']['PHYSICALRSI_SIDECAR_ROOT']=str(O/'sim-diagnostics'/name)
  rp=O/'runtimes'/(name+'.json');rp.parent.mkdir(exist_ok=True);atomic_json(rp,cfg)
  runtime=NativeRuntime(cfg);target=C/'harnesses'/name
  shutil.copytree(parent['harness']['root'],target,symlinks=False)
  atomic_json(target/'assets.json',runtime.identity());shutil.copy2(src,target/'code/classify_objects.py')
  expert=dict(name='code.classify_objects',revision=file_digest(src))
  atomic_json(target/'skills.json',{expert['name']:dict(revision=expert['revision'],source='code/classify_objects.py')})
  atomic_json(target/'skill_selection.json',dict(skill_choices={'classify_objects':expert}))
  if proposal is not None:
   memory=read_json(target/'memory_rules.json');memory['classify_objects']=proposal['memory'];atomic_json(target/'memory_rules.json',memory)
  h=manifest(target,'search_controls_'+phase+'_'+name);revision=verify_harness(h)
  pre=runtime.check();admit=runtime.admit(h,O/'native-preparation/admission'/name)
  atomic_json(O/'native-preparation'/name/'check.json',pre)
  assert pre['ready'],pre
  audits[-1]['native_admission']=admit
  if not admit['accepted']:audits[-1]['admitted']=False;continue
  entries.append(dict(name=name,expert=expert,harness=h,harness_sha256=revision,runtime=str(rp),runtime_sha256=file_digest(rp),source_sha256=file_digest(src),origin=row))
 atomic_json(O/'native-preparation/candidate-audit.json',audits)
 assert entries,'No admitted entries; no native results fabricated'
 atomic_json(C/'campaign.json',dict(protocol=str(O/'protocol.json'),protocol_sha256=file_digest(O/'protocol.json'),runtime=entries[0]['runtime'],runtime_sha256=entries[0]['runtime_sha256'],per_entry_runtime=True,layout_root=layout_root,cases=cases,entries=entries,planned_cases=len(cases)*len(entries),api_calls=0,selection=plan['selection'],raw_task_budget_unchanged=1100))
 print(json.dumps(dict(phase=phase,admitted=len(entries),native_cases=len(cases)*len(entries),rejected=len(audits)-len(entries))))
if __name__=='__main__':main(sys.argv[1])
