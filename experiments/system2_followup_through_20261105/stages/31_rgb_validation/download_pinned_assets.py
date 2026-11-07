from pathlib import Path
import concurrent.futures,hashlib,json,subprocess,os,time,datetime,fcntl,threading
R=Path('/mnt/data/physical-RSI');A=R/'models/official-v4';O=R/'result/31_rgb_supplement_20261105/resource-download'
O.mkdir(parents=True,exist_ok=True);D=A/'.downloads';D.mkdir(exist_ok=True)
lock=(O/'download.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
raw=(A/'assets.json').read_bytes();assert hashlib.sha256(raw).hexdigest()=='0eed83202427dc6b4c75cde613246f8f6e606cac6c8da3bd71ebc6798d6963d2'
parts=[p for a in json.loads(raw)['assets'] for p in a['parts']]
results={};guard=threading.Lock();started=time.time()
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def get(p):
 dst=D/p['name'];tmp=D/(p['name']+'.partial')
 if dst.exists() and dst.stat().st_size==p['size'] and sha(dst)==p['sha256']:
  return {'name':p['name'],'ok':True,'cached':True}
 links=json.loads((A/'.resolved_download_urls.json').read_text());link=links.get(p['name'])
 if not link or link['expires_at']<time.time()+60:return {'name':p['name'],'ok':False,'reason':'redirect_missing_or_expired'}
 assert link['original_url']==p['url']
 with (O/(p['name']+'.log')).open('a') as f:
  proc=subprocess.run(['curl','-4','--http1.1','--config','-','--proto','=https','--fail','--silent','--show-error','--connect-timeout','15','--max-time','1800','--speed-time','90','--speed-limit','32768','--continue-at','-','--output',str(tmp),'--write-out','HTTP %{http_code} bytes %{size_download} rate %{speed_download}\n'],input='url = "'+link['url']+'"\n',text=True,stdout=f,stderr=subprocess.STDOUT)
 good=tmp.exists() and tmp.stat().st_size==p['size'] and sha(tmp)==p['sha256']
 if good:tmp.replace(dst)
 return {'name':p['name'],'ok':good,'curl_exit':proc.returncode,'bytes':tmp.stat().st_size if tmp.exists() else dst.stat().st_size if dst.exists() else 0}
def status(state):
 b=sum(min(p['size'],max((D/p['name']).stat().st_size if (D/p['name']).exists() else 0,(D/(p['name']+'.partial')).stat().st_size if (D/(p['name']+'.partial')).exists() else 0)) for p in parts)
 v={'state':state,'pid':os.getpid(),'updated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'elapsed_s':time.time()-started,'bytes_present':b,'total_bytes':sum(p['size'] for p in parts),'verified_parts':sum(x['ok'] for x in results.values()),'total_parts':len(parts),'results':list(results.values()),'api_calls':0}
 t=O/'status.tmp';t.write_text(json.dumps(v,indent=2));t.replace(O/'status.json')
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 fs={pool.submit(get,p):p for p in parts}
 status('downloading')
 while fs:
  done,_=concurrent.futures.wait(fs,timeout=10,return_when=concurrent.futures.FIRST_COMPLETED)
  for f in done:
   p=fs.pop(f)
   try:row=f.result()
   except Exception as e:row={'name':p['name'],'ok':False,'error_type':type(e).__name__}
   results[p['name']]=row;print(json.dumps(row),flush=True)
  status('downloading')
status('verified_complete' if all(x['ok'] for x in results.values()) else 'needs_review')
