"""Public release transport with mandatory pinned official SHA256 checks.

Only public weight URLs are sent to the transport; no credentials or private
project content. Preserves old direct-download partials and failed attempts.
"""
from pathlib import Path
import concurrent.futures
import datetime
import fcntl
import hashlib
import json
import os
import subprocess
import time

R=Path('/mnt/data/physical-RSI')
A=R/'models/official-v4'
D=A/'.downloads'
T=A/'.transport-downloads'
T.mkdir(exist_ok=True)
O=R/'result/31_rgb_supplement_20261105/resource-download-weights'
LOCK=(O/'download.lock').open('a');fcntl.flock(LOCK,fcntl.LOCK_EX|fcntl.LOCK_NB)
raw=(A/'assets.json').read_bytes()
assert hashlib.sha256(raw).hexdigest()=='0eed83202427dc6b4c75cde613246f8f6e606cac6c8da3bd71ebc6798d6963d2'
parts=[p for a in json.loads(raw)['assets'] if a['name'] in ['pi05-weights','sparse-memory-weights'] for p in a['parts']]
assert len(parts)==24
started=time.monotonic();results={};cached=set()

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()

for p in parts:
    f=D/p['name']
    if f.exists():
        assert f.stat().st_size==p['size'] and sha(f)==p['sha256'],'Existing verified part mismatch'
        cached.add(p['name'])

def get(p):
    dst=D/p['name']
    if p['name'] in cached:return dict(name=p['name'],ok=True,cached=True,bytes=p['size'])
    tmp=T/(p['name']+'.partial');attempts=[]
    for i in range(1,4):
        before=tmp.stat().st_size if tmp.exists() else 0
        assert before<=p['size']
        if before==p['size']:
            if sha(tmp)==p['sha256']:
                tmp.replace(dst);return dict(name=p['name'],ok=True,bytes=p['size'],attempts=attempts)
            return dict(name=p['name'],ok=False,reason='sha256_mismatch',attempts=attempts)
        t=time.monotonic()
        with (O/(p['name']+'.transport.log')).open('a') as log:
            proc=subprocess.run(['curl','-4','-L','--proto','=https','--proto-redir','=https','--fail','-sS',
                '--connect-timeout','15','--max-time','1200','--speed-time','90','--speed-limit','32768',
                '--continue-at','-','--output',str(tmp),'https://gh-proxy.com/'+p['url']],stdout=log,stderr=subprocess.STDOUT)
        after=tmp.stat().st_size if tmp.exists() else 0
        attempts.append(dict(attempt=i,curl_exit=proc.returncode,bytes_before=before,bytes_after=after,elapsed_s=time.monotonic()-t))
        if after==p['size']:
            digest=sha(tmp)
            if digest!=p['sha256']:return dict(name=p['name'],ok=False,reason='sha256_mismatch',actual_sha256=digest,attempts=attempts)
            tmp.replace(dst)
            return dict(name=p['name'],ok=True,bytes=p['size'],sha256=digest,attempts=attempts,transport='https://gh-proxy.com/',original_url=p['url'])
        if proc.returncode==33 and before:
            # Server did not support resume. Preserve bytes under a unique name.
            tmp.rename(T/(p['name']+'.saved-'+str(time.time_ns())))
        elif proc.returncode not in [5,6,7,18,22,28,35,52,55,56]:break
    return dict(name=p['name'],ok=False,reason='bounded_attempts_exhausted',attempts=attempts)

def status(state):
    sizes={}
    for p in parts:
        f=D/p['name'];partial=T/(p['name']+'.partial')
        # Old direct-download prefixes are excluded from this route's progress.
        sizes[p['name']]=min(p['size'],max(f.stat().st_size if f.exists() else 0,partial.stat().st_size if partial.exists() else 0))
    data=dict(state=state,pid=os.getpid(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              elapsed_s=time.monotonic()-started,bytes_present=sum(sizes.values()),total_bytes=sum(p['size'] for p in parts),
              part_bytes=sizes,verified_parts=sum(p['name'] in cached or results.get(p['name'],{}).get('ok',False) for p in parts),
              total_parts=len(parts),results=list(results.values()),transport='https://gh-proxy.com/',
              trust_root='previously verified official v4 manifest; each part mandatory size and SHA256',
              old_direct_partials_preserved=True,credentials_sent=False,api_calls=0,model_versions_changed=False)
    temp=O/'status.tmp';temp.write_text(json.dumps(data,indent=2));temp.replace(O/'status.json')

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    futures={pool.submit(get,p):p for p in parts}
    while futures:
        done,_=concurrent.futures.wait(futures,timeout=10,return_when=concurrent.futures.FIRST_COMPLETED)
        for future in done:
            p=futures.pop(future)
            try:row=future.result()
            except Exception as exc:row=dict(name=p['name'],ok=False,reason=type(exc).__name__)
            results[p['name']]=row;print(json.dumps(row),flush=True)
        status('downloading')
status('verified_complete' if all(x['ok'] for x in results.values()) else 'needs_review')
