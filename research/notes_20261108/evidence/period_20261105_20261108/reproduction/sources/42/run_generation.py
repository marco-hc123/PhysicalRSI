"""Bounded paid generation; key remains only in this process's memory."""
import ast, datetime, fcntl, getpass, hashlib, json, os, resource, time
import urllib.request, urllib.error
from pathlib import Path
O=Path(__file__).resolve().parent
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def read(p): return json.loads(p.read_text())
def save(n,x):
 p=O/n;p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix(p.suffix+'.tmp')
 t.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');t.replace(p)
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*a,**k): raise RuntimeError('Redirect refused')
def main():
 os.umask(0o077);resource.setrlimit(resource.RLIMIT_CORE,(0,0))
 lock=(O/'generation.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not (O/'ledger.json').exists(),'Existing paid ledger requires reconciliation; no blind retry'
 protocol=read(O/'protocol.json');assert protocol['maximum_reserved_usd']<10
 key=getpass.getpass('Ephemeral API key (hidden; memory only): ').strip()
 opener=urllib.request.build_opener(NoRedirect())
 def call(path,payload=None):
  data=json.dumps(payload,ensure_ascii=False).encode() if payload is not None else None
  req=urllib.request.Request('https://api.openai.com/v1'+path,data=data,headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'},method='POST' if data else 'GET')
  try:
   with opener.open(req,timeout=900) as r:return dict(status=r.status,request_id=r.headers.get('x-request-id'),body=json.loads(r.read()))
  except urllib.error.HTTPError as e:return dict(status=e.code,error_body=e.read().decode(errors='replace').replace(key,'[REDACTED]'))
  except Exception as e:return dict(status=None,error_type=type(e).__name__)
 auth=call('/models/gpt-6.1-sol');save('model-access.json',auth)
 if auth.get('status')!=200:
  save('generation-status.json',dict(state='model_access_failed',http_status=auth.get('status'),paid_requests=0,utc=now()))
  print('MODEL_ACCESS_FAILED',auth.get('status'),flush=True);return
 ledger=[];reserved=protocol['prior_conservative_allowance_usd']
 for batch in ['sampling','round2']:
  control=O/(batch+'-generation.json')
  save('generation-status.json',dict(state='waiting_for_batch',batch=batch,pid=os.getpid(),paid_requests=len(ledger),reserved_usd=reserved,utc=now()))
  until=time.monotonic()+6*3600
  while not control.exists():
   if (O/'finish-generation.json').exists() or time.monotonic()>until:
    save('generation-status.json',dict(state='finished_without_next_batch',paid_requests=len(ledger),reserved_usd=reserved,utc=now()));return
   time.sleep(5)
  plan=read(control)
  for row in plan['requests']:
   assert len(ledger)<protocol['generation_calls_max']
   path=O/row['file'];raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256']
   request=json.loads(raw)
   assert request['model']=='gpt-6.1-sol' and request['reasoning_effort']=='high'
   assert request['max_completion_tokens']==16000 and request['service_tier']=='default'
   assert len(raw)<=protocol['max_request_bytes']
   reserve=protocol['reserve_per_call_usd'];assert reserved+reserve<=protocol['api_cap_usd']
   reserved+=reserve;entry=dict(id=row['id'],batch=batch,request_sha256=row['sha256'],state='reserved',reserve_usd=reserve,started_utc=now());ledger.append(entry)
   save('ledger.json',ledger);save('generation-status.json',dict(state='request_running',id=row['id'],pid=os.getpid(),reserved_usd=reserved,paid_requests=len(ledger),utc=now()))
   began=time.monotonic();result=call('/chat/completions',request)
   entry.update(http_status=result.get('status'),seconds=time.monotonic()-began,finished_utc=now(),state='received' if result.get('status')==200 else 'failed')
   save('responses/'+row['id']+'.json',result)
   if result.get('status')==200:
    body=result['body'];entry['returned_model']=body.get('model');u=body['usage'];entry['usage']=u;d=u.get('prompt_tokens_details') or {}
    inp,out=u['prompt_tokens'],u['completion_tokens'];cache=d.get('cached_tokens',0);cw=d.get('cache_write_tokens',0)
    assert 0<=cache+cw<=inp
    entry['estimated_standard_usd']=((inp-cache-cw)*2+cache*.1+cw*2.5+out*10)/1e6
    entry['cost_scope']='Cache is an input subset; reasoning included in output. Invoice authoritative.'
    choice=body['choices'][0];entry['finish_reason']=choice.get('finish_reason')
    try:
     proposal=json.loads(choice['message']['content']);assert isinstance(proposal['source'],str) and isinstance(proposal['memory'],dict) and isinstance(proposal['rationale'],str)
     ast.parse(proposal['source']);p=O/'candidates'/row['id'];p.mkdir(parents=True,exist_ok=False)
     (p/'candidate.py').write_text(proposal['source']);save('candidates/'+row['id']+'/proposal.json',proposal)
     entry.update(syntax_valid=True,source_sha256=hashlib.sha256(proposal['source'].encode()).hexdigest())
    except Exception as e:entry.update(syntax_valid=False,parse_error=type(e).__name__+': '+str(e))
   save('ledger.json',ledger)
   print(json.dumps({k:entry.get(k) for k in ['id','state','seconds','estimated_standard_usd','syntax_valid']}),flush=True)
   if result.get('status')!=200:
    save('generation-status.json',dict(state='stopped_api_failure',paid_requests=len(ledger),reserved_usd=reserved,utc=now()));return
  save(batch+'-generation-complete.json',dict(state='completed',requests=len(plan['requests']),paid_requests_total=len(ledger),reserved_usd=reserved,estimated_usd=sum(x.get('estimated_standard_usd',0) for x in ledger),utc=now()))
 key=None
 save('generation-status.json',dict(state='completed',paid_requests=len(ledger),reserved_usd=reserved,estimated_usd=sum(x.get('estimated_standard_usd',0) for x in ledger),utc=now()))
if __name__=='__main__':main()
