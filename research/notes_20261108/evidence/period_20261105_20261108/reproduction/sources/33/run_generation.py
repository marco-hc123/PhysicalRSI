"""Six preregistered, capped calls. Credential is hidden-input memory only."""
import ast,datetime,fcntl,getpass,hashlib,importlib.util,json,os,resource,time,urllib.request,urllib.error
from pathlib import Path
R=Path('/mnt/data/joey_tr/physical-RSI');O=R/'result/33_system2_capability_feedback/20261106_v1'
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def read(p):return json.loads(p.read_text())
def write(n,x):p=O/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*a,**k):raise RuntimeError('Redirect refused')
def main():
 os.umask(0o077);resource.setrlimit(resource.RLIMIT_CORE,(0,0))
 lock=(O/'generation.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert read(O/'status.json')['state']=='protocol_frozen'
 assert not (O/'ledger.json').exists()
 protocol=read(O/'protocol.json');assert protocol['combined_reserved_upper_usd']<10
 key=getpass.getpass('Ephemeral API key (hidden, not persisted): ').strip()
 if not key:raise RuntimeError('Missing ephemeral key')
 spec=importlib.util.spec_from_file_location('guard',R/'result/27_system2_offline_diagnostics/20261104_cpu_v1/run_cpu_batch.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.OUT=O
 write('write-isolation.json',m.guard());os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1')
 opener=urllib.request.build_opener(NoRedirect())
 def call(path,payload=None):
  raw=json.dumps(payload,ensure_ascii=False).encode() if payload is not None else None
  request=urllib.request.Request('https://api.openai.com/v1'+path,data=raw,headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'},method='POST' if raw else 'GET')
  try:
   with opener.open(request,timeout=600) as response:return dict(status=response.status,request_id=response.headers.get('x-request-id'),body=json.loads(response.read()))
  except urllib.error.HTTPError as e:
   data=e.read().decode(errors='replace').replace(key,'[REDACTED]')
   return dict(status=e.code,request_id=e.headers.get('x-request-id'),error_body=data)
  except Exception as e:return dict(status=None,error_type=type(e).__name__)
 auth=call('/models/gpt-6.1-sol');write('model-access.json',auth)
 if auth.get('status')!=200:
  write('status.json',dict(state='blocked_model_access',pid=None,generation_requests=0,api_cost_usd=0,http_status=auth.get('status'),updated_utc=now()));print('MODEL_ACCESS_FAILED',auth.get('status'),flush=True);return
 ledger=[];reserved=protocol['previous_reserved_usd']
 for row in protocol['requests']:
  assert sha(O/row['request_file'])==row['request_sha256']
  assert reserved+row['reserved_usd']<=protocol['budget_usd']
  reserved+=row['reserved_usd'];entry=dict(row,state='reserved',started_utc=now());ledger.append(entry)
  write('ledger.json',ledger);write('status.json',dict(state='generation_running',pid=os.getpid(),active=row['id'],attempts=len(ledger),combined_reserved_usd=reserved,updated_utc=now()))
  t=time.monotonic();result=call('/chat/completions',read(O/row['request_file']));entry.update(seconds=time.monotonic()-t,finished_utc=now(),http_status=result.get('status'),state='received' if result.get('status')==200 else 'failed')
  write('responses/'+row['id']+'.json',result)
  if result.get('status')==200:
   body=result['body'];u=body['usage'];entry['usage']=u;d=u.get('prompt_tokens_details') or {}
   inp=u['prompt_tokens'];out=u['completion_tokens'];cached=d.get('cached_tokens',0);cw=d.get('cache_write_tokens',0)
   assert 0<=cached+cw<=inp
   entry['estimated_standard_usd']=((inp-cached-cw)*2+cached*.1+cw*2.5+out*10)/1e6
   entry['cost_scope']='Cached/cache-write input subsets; reasoning included in completion. Estimate, invoice authoritative.'
   choice=body['choices'][0];entry['finish_reason']=choice.get('finish_reason')
   try:
    proposal=json.loads(choice['message']['content']);assert isinstance(proposal['source'],str) and isinstance(proposal['memory'],dict) and isinstance(proposal['rationale'],str)
    ast.parse(proposal['source']);p=O/'candidates'/row['id'];p.mkdir(parents=True,exist_ok=False)
    (p/'candidate.py').write_text(proposal['source']);write('candidates/'+row['id']+'/proposal.json',proposal)
    entry.update(json_and_python_syntax_valid=True,source_sha256=sha(p/'candidate.py'),proposal_sha256=sha(p/'proposal.json'))
   except Exception as e:entry.update(json_and_python_syntax_valid=False,parse_error=type(e).__name__+': '+str(e))
  write('ledger.json',ledger)
  print(json.dumps(dict(id=row['id'],state=entry['state'],seconds=round(entry['seconds'],2),estimated_usd=entry.get('estimated_standard_usd'),syntax_valid=entry.get('json_and_python_syntax_valid'))),flush=True)
  if result.get('status') in [401,403,404] or result.get('status') is None:break
 key=None
 write('status.json',dict(state='generation_complete' if len(ledger)==6 and all(x['state']=='received' for x in ledger) else 'generation_incomplete',pid=None,attempts=len(ledger),combined_reserved_usd=reserved,estimated_standard_usd=sum(x.get('estimated_standard_usd',0) for x in ledger),unknown_cost_requests=[x['id'] for x in ledger if 'estimated_standard_usd' not in x],new_native_cases=0,finished_utc=now()))
if __name__=='__main__':main()
