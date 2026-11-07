"""Six capped paired candidate generations; no candidate execution, no training."""
import ast, datetime, getpass, hashlib, json, os, resource, sys, time, urllib.request, urllib.error
from pathlib import Path
R=Path('/mnt/data/joey_tr/physical-RSI')
O=R/'result/29_system2_feedback_api/20261104_v1'
F=R/'result/27_system2_offline_diagnostics/20261104_cpu_v1/followup_v2/feedback'
MODEL='gpt-6.1-sol';BASE='https://api.openai.com/v1'
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def write(name,data):
 p=O/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
def sha(b):return hashlib.sha256(b).hexdigest()
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):raise RuntimeError('API redirect refused')
def main():
 os.umask(0o077);resource.setrlimit(resource.RLIMIT_CORE,(0,0))
 if (O/'status.json').exists():raise RuntimeError('Existing batch; do not repeat calls')
 O.mkdir(parents=True,exist_ok=True)
 # Reuse audited write-only confinement, with no GPU device access in this CPU/API process.
 import importlib.util
 spec=importlib.util.spec_from_file_location('confinement',R/'result/27_system2_offline_diagnostics/20261104_cpu_v1/run_cpu_batch.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.OUT=O
 key=getpass.getpass('Ephemeral API key (input hidden; not saved): ').strip()
 if not key:raise RuntimeError('No key supplied')
 write('write-isolation.json',m.guard());os.environ['CUDA_VISIBLE_DEVICES']='';os.environ['PYTHONDONTWRITEBYTECODE']='1'
 order=['baseline','augmented','augmented','baseline','baseline','augmented'];counts={'baseline':0,'augmented':0};requests=[]
 for arm in order:
  counts[arm]+=1;p=F/(arm+'_messages.json');messages=json.loads(p.read_text())['messages']
  assert all(isinstance(x['content'],str) for x in messages)
  request={'model':MODEL,'messages':messages,'reasoning_effort':'medium','max_completion_tokens':12000,'response_format':{'type':'json_object'},'service_tier':'default','store':False}
  raw=json.dumps(request,ensure_ascii=False).encode();token_bound=len(raw)+4096
  assert token_bound<100000
  # Deliberately above verified standard rates; no cache discount needed to enforce limit.
  reserve=(token_bound*6+12000*20)/1e6
  row={'arm':arm,'replicate':counts[arm],'id':f'{arm}_{counts[arm]}','input_file':str(p),'input_sha256':sha(p.read_bytes()),'request_sha256':sha(raw),'input_token_conservative_bound':token_bound,'reserved_usd':reserve,'request':request};requests.append(row)
 worst=sum(x['reserved_usd'] for x in requests);assert worst<10
 write('protocol.json',{'created_utc':now(),'goal':'Exploratory test of candidate-generation feedback completeness; not native success','model':MODEL,'reasoning_effort':'medium','endpoint':BASE+'/chat/completions','calls_planned':6,'replicates_per_arm':3,'order':order,'treatment':'Append failed candidate source and attributed recorded failures; preserve baseline messages','fixed':['selected parent pi05','same model, reasoning, output limit, response schema','same development feedback','no manual repair code in prompt'],'limitations':['Additional context length not independently controlled','Previously used layouts are diagnostic development evidence, not heldout','Small exploratory sample; not a task-score improvement claim'],'budget_usd':10,'whole_batch_reserved_upper_usd':worst,'reserve_rates_per_million':{'input':6,'output':20},'standard_rates_per_million':{'input':2,'cached_input':.1,'output':10},'pricing_source':'https://developers.openai.com/api/docs/models/gpt-6.1-sol','no_automatic_retries':True,'tools_enabled':False,'new_native_episodes':0})
 for r in requests:write('requests/'+r['id']+'.json',r['request'])
 write('status.json',{'state':'awaiting_ephemeral_key','pid':os.getpid(),'reserved_usd':0,'model':MODEL,'updated_utc':now()})
 opener=urllib.request.build_opener(NoRedirect())
 def call(path,payload=None):
  data=json.dumps(payload,ensure_ascii=False).encode() if payload is not None else None
  req=urllib.request.Request(BASE+path,data=data,headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'},method='POST' if data else 'GET')
  try:
   with opener.open(req,timeout=600) as res:return {'status':res.status,'request_id':res.headers.get('x-request-id'),'body':json.loads(res.read())}
  except urllib.error.HTTPError as e:
   body=e.read().decode(errors='replace').replace(key,'[REDACTED]')
   return {'status':e.code,'request_id':e.headers.get('x-request-id'),'error_body':body}
  except Exception as e:return {'status':None,'error':type(e).__name__+': '+str(e).replace(key,'[REDACTED]')}
 auth=call('/models/'+MODEL);write('model-access.json',auth)
 if auth.get('status')!=200:
  write('status.json',{'state':'blocked_model_access','pid':None,'generation_requests':0,'reserved_usd':0,'estimated_usd':0,'updated_utc':now()});print('MODEL_ACCESS_FAILED',auth.get('status'),flush=True);return
 ledger=[];reserved=0
 for r in requests:
  assert reserved+r['reserved_usd']<=10
  reserved+=r['reserved_usd'];entry={k:v for k,v in r.items() if k!='request'};entry.update(state='reserved',started_utc=now());ledger.append(entry)
  write('ledger.json',ledger);write('status.json',{'state':'running','pid':os.getpid(),'active':r['id'],'attempts':len(ledger),'reserved_usd':reserved,'updated_utc':now()})
  t=time.monotonic();result=call('/chat/completions',r['request']);elapsed=time.monotonic()-t
  # Secret never enters payload, request artifacts, response, or ledger.
  write('responses/'+r['id']+'.json',result)
  entry.update(state='received' if result.get('status')==200 else 'failed',http_status=result.get('status'),seconds=elapsed,finished_utc=now(),request_id=result.get('request_id'))
  if result.get('status')==200:
   b=result['body'];u=b.get('usage',{});entry['usage']=u
   inp=u.get('prompt_tokens',0);out=u.get('completion_tokens',0);cached=(u.get('prompt_tokens_details') or {}).get('cached_tokens',0)
   entry['estimated_standard_usd']=((inp-cached)*2+cached*.1+out*10)/1e6
   entry['cost_qualification']='Estimate from returned usage, standard pricing; account invoice authoritative. Cached input subset; reasoning included in completion.'
   choice=b['choices'][0];entry['finish_reason']=choice.get('finish_reason')
   try:
    candidate=json.loads(choice['message']['content']);assert isinstance(candidate['source'],str) and isinstance(candidate['memory'],dict) and isinstance(candidate['rationale'],str)
    ast.parse(candidate['source']);p=O/'candidates'/r['id'];p.mkdir(parents=True,exist_ok=True);(p/'candidate.py').write_text(candidate['source']);write('candidates/'+r['id']+'/proposal.json',candidate);entry['json_and_python_syntax_valid']=True;entry['source_sha256']=sha(candidate['source'].encode())
   except Exception as e:entry['json_and_python_syntax_valid']=False;entry['parse_error']=type(e).__name__+': '+str(e)
  write('ledger.json',ledger);print('REQUEST',r['id'],entry['state'],'seconds',round(elapsed,1),'reserved_usd',round(reserved,4),flush=True)
  if result.get('status') in [401,403,404] or result.get('status') is None:break
 key=None
 write('status.json',{'state':'generation_complete' if len(ledger)==6 and all(x['state']=='received' for x in ledger) else 'generation_incomplete','pid':None,'attempts':len(ledger),'reserved_usd':reserved,'estimated_standard_usd':sum(x.get('estimated_standard_usd',0) for x in ledger),'unknown_cost_requests':[x['id'] for x in ledger if 'estimated_standard_usd' not in x],'new_native_episodes':0,'candidate_execution':'not run; audit first','finished_utc':now()})
if __name__=='__main__':main()
