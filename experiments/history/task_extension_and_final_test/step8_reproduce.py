"""Verify archived evidence or rerun explicit cohorts under a new output namespace.

No action is dispatched by verify. Reruns must be explicitly selected and are
excluded from the original formal/final score denominators.
"""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys,shutil,subprocess,ast,os
MODE,O=sys.argv[1],Path(sys.argv[2]).resolve()
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def verify():
 manifest=read(O/'exports/file-manifest.json')
 for n,v in manifest.items():assert sha(O/'exports'/n)==v['sha256'],n
 for p,h in read(O/'protocol.json')['source_hashes'].items():assert sha(Path(p))==h,p
 for n,h in read(O/'procedure-registration.json').items():assert sha(O/'analysis-sources'/n)==h,n
 for n,h in read(O/'closure-procedure-registration.json').items():assert sha(O/n)==h,n
 assert read(O/'completion.json')['complete']
 return dict(complete=True,checked_exports=len(manifest),original_protocol_sha256=sha(O/'protocol.json'),model_calls=0,native_dispatches=0)
if MODE=='verify':
 result=verify();write(O/'reproduction-verification.json',result);print(json.dumps(result))
elif MODE=='rerun-new-tasks':
 assert len(sys.argv)==4,'Provide a NEW absolute output directory';verify();N=Path(sys.argv[3]).resolve();N.mkdir(exist_ok=False)
 shutil.copytree(O/'analysis-sources',N/'analysis-sources');p=read(O/'protocol.json');p['cohort_role']='explicit_rerun_not_original_formal';p['source_run']=str(O);write(N/'protocol.json',p)
 for name in ['procedure-registration.json','preparation-status.json','analysis-status.json','formal-freeze.json']:shutil.copy2(O/name,N/name)
 subprocess.run(['python3',str(N/'analysis-sources/step7_controller.py'),str(N),'formal'],check=True)
elif MODE=='rerun-final':
 assert len(sys.argv)==4,'Provide a NEW absolute output directory';verify();N=Path(sys.argv[3]).resolve();N.mkdir(exist_ok=False)
 source=O/'step7_final.py';tree=ast.parse(source.read_text());body=[]
 for node in tree.body:
  if isinstance(node,ast.If) and ast.unparse(node.test).startswith("MODE =="):break
  body.append(node)
 ns={'__name__':'frozen_final_replay','__file__':str(source)};saved=sys.argv
 try:
  sys.argv=[str(source),'library',str(O)];exec(compile(ast.Module(body=body,type_ignores=[]),str(source),'exec'),ns)
 finally:sys.argv=saved
 _,task,runtime=ns['objects']()
 from PhysicalRSI_baselines.robodojo.workflow import RoboDojoTask
 from PhysicalRSI.Embodied_Harness.memory.store import MemoryStore
 comparison=read(O/'final-test/comparison.json');out=[]
 write(N/'replay-provenance.json',dict(source=str(O),source_comparison_sha256=sha(O/'final-test/comparison.json'),role='explicit_exact_layout_replay_not_original_final',new_http_calls=0))
 for name in ['classify_objects','classify_objects_by_language']:
  cohort=O/'final-test/cohorts'/name;cases=read(cohort/'cases.json');harness=comparison['ordinary_harness'] if name=='classify_objects' else comparison['language_transfer_harness'];task.memory=MemoryStore(N/'memory'/name)
  for i,case in enumerate(cases):
   out.extend(RoboDojoTask.execute_batch(task,harness,[case],cohort,N/'native'/name/f'{i:02d}'));write(N/'results.json',out)
 write(N/'complete.json',dict(complete=True,episodes=len(out),new_http_calls=0))
else:raise ValueError('Use verify, rerun-new-tasks or rerun-final')
