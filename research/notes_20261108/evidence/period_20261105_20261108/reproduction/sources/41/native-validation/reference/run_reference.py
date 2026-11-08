"""Sequential positive-reference test; never overlaps the current GPU cohort."""
import datetime,fcntl,hashlib,json,os,subprocess,sys,time,traceback,signal
from pathlib import Path
O=Path(__file__).resolve().parent;P=O.parent
I=O.parents[1]/'25_system2_integration_20261030T050100Z/integration-sources'
sys.path[:0]=[str(I),str(I/'framework-validation-v3')]
from PhysicalRSI_baselines.robodojo.native_execution import execute
from PhysicalRSI_baselines.robodojo.expert_model import websocket_client
from PhysicalRSI_core.infra.storage import atomic_json
def read(p):return json.loads(p.read_text())
def status(state,**x):atomic_json(O/'status.json',dict(state=state,pid=os.getpid(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),api_calls=0,lab_gpu_used=False,**x))
lock=(O/'controller.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not (O/'native').exists() and not (O/'ready.json').exists(),'Do not replay an existing attempt'
service=None;client=None
try:
 status('waiting_for_previous_cohort');deadline=time.monotonic()+7200
 while True:
  d=read(P/'native-campaign/status.json')
  assert d['state']!='stopped_for_diagnosis','Prior cohort needs investigation'
  if d['state']=='diagnostic_matrix_completed':break
  if time.monotonic()>deadline:raise TimeoutError('Previous cohort still active')
  time.sleep(15)
 deadline=time.monotonic()+600
 while subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip():
  if time.monotonic()>deadline:raise TimeoutError('GPU still occupied; leave other tasks alone')
  time.sleep(10)
 cfg=read(O/'environment.json');spec=read(O/'reference-spec.json');protocol=read(O/'protocol.json')
 for name,wanted in protocol['code_sha256'].items():assert hashlib.sha256((O/name).read_bytes()).hexdigest()==wanted
 env=dict(os.environ,**cfg['policy_environment']);env.update(CLASSIFY_RESULTS=str(O/'model-evidence'),CLASSIFY_TRACE_DIR=str(O/'model-traces'),PYTHONDONTWRITEBYTECODE='1')
 # Keep frozen dependency paths, omit only preceding instrumentation overlays.
 env['PYTHONPATH']=str(O.parent/'code')+':'+env['PYTHONPATH']
 log=(O/'service.log').open('w');service=subprocess.Popen([cfg['policy_python'],'-B',str(O/'reference_service.py')],env=env,stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 status('model_loading',service_pid=service.pid);deadline=time.monotonic()+900
 while not (O/'ready.json').exists():
  if service.poll() is not None:raise RuntimeError('Reference model startup failed, exit='+str(service.returncode)+'; see service.log')
  if time.monotonic()>deadline:raise TimeoutError('Reference startup timeout')
  time.sleep(2)
 ready=read(O/'ready.json');client=websocket_client(endpoint=ready['endpoint'],timeout_s=300)
 assert client.call(func_name='physicalrsi_identity')==dict(name=spec['name'],revision=spec['revision'])
 client.close();client=None
 request=read(O/'request-template.json');request.update(endpoint=ready['endpoint'],port=int(ready['endpoint'].rsplit(':',1)[1]))
 env=dict(os.environ,**cfg['simulator_environment']);env['PHYSICALRSI_SIDECAR_ROOT']=str(O/'sim-diagnostics')
 env['PYTHONPATH']=str(O.parent/'code')+':'+env['PYTHONPATH']
 status('reference_native_running',service_pid=service.pid,planned_cases=5)
 started=time.monotonic();receipts=execute(request,python=cfg['simulator_python'],environment=env,output=O/'native',timeout_s=3600)
 assert len(receipts)==5
 rows=[dict(layout_id=i,**{k:read(p)[k] for k in ['episode_score','success','diagnostics','layout_sha256']}) for i,p in enumerate(receipts)]
 atomic_json(O/'outcomes.json',dict(rows=rows,native_cases=5,api_calls=0,wall_s=time.monotonic()-started,scope='Released first-source-to-basket cycle capability reference; richer APIs than generated candidate; not full-task evaluation or a new System2 candidate'))
 status('reference_completed',native_cases=5,scores=[r['episode_score'] for r in rows],successes=sum(r['success'] for r in rows))
except BaseException as e:
 atomic_json(O/'failure.json',dict(error=repr(e),traceback=traceback.format_exc(),policy_zero_score=False));status('requires_diagnosis',error=repr(e));raise
finally:
 if client:client.close()
 if service and service.poll() is None:
  os.killpg(service.pid,signal.SIGTERM)
  try:service.wait(timeout=30)
  except subprocess.TimeoutExpired:os.killpg(service.pid,signal.SIGKILL);service.wait(timeout=15)
 if service and service.stdin:service.stdin.close()
 if 'log' in locals():log.close()
