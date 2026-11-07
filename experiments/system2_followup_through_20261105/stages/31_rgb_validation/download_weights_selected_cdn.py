"""Resume the two pinned official checkpoints; verify every release part."""
from pathlib import Path
import concurrent.futures
import datetime
import fcntl
import hashlib
import json
import os
import socket
import subprocess
import time

R = Path('/mnt/data/physical-RSI')
A = R/'models/official-v4'
D = A/'.downloads'
CDN_IP = os.environ['PHYSICALRSI_ASSET_CDN_IP']
assert CDN_IP in {x[4][0] for x in socket.getaddrinfo('release-assets.githubusercontent.com',443,socket.AF_INET,socket.SOCK_STREAM)}, 'Selected CDN address must be in current official DNS results'
O = R/'result/31_rgb_supplement_20261105/resource-download-weights'
O.mkdir(parents=True, exist_ok=True)
lock = (O/'download.lock').open('a')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
raw = (A/'assets.json').read_bytes()
assert hashlib.sha256(raw).hexdigest() == '0eed83202427dc6b4c75cde613246f8f6e606cac6c8da3bd71ebc6798d6963d2'
parts = [dict(p,asset=asset['name']) for asset in json.loads(raw)['assets']
         if asset['name'] in ['pi05-weights','sparse-memory-weights'] for p in asset['parts']]
assert len(parts) == 24
results = {}
cached_valid = set()
started = time.monotonic()

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):
            h.update(b)
    return h.hexdigest()

for existing_part in parts:
    existing_path=D/existing_part['name']
    if existing_path.exists() and existing_path.stat().st_size==existing_part['size'] and sha(existing_path)==existing_part['sha256']:
        cached_valid.add(existing_part['name'])

def get(part):
    dst=D/part['name']
    tmp=D/(part['name']+'.partial')
    if dst.exists():
        valid=dst.stat().st_size==part['size'] and sha(dst)==part['sha256']
        if not valid:
            return {'name':part['name'],'ok':False,'reason':'existing_verified_filename_mismatch'}
        return {'name':part['name'],'ok':True,'cached':True,'bytes':dst.stat().st_size}
    attempts=[]
    for attempt in range(1,4):
        links=json.loads((A/'.resolved_download_urls.json').read_text())
        link=links.get(part['name'])
        if not link or link['expires_at'] < time.time()+60:
            return {'name':part['name'],'ok':False,'reason':'fresh_official_redirect_required','attempts':attempts}
        assert link['original_url']==part['url']
        if tmp.exists() and tmp.stat().st_size>part['size']:
            return {'name':part['name'],'ok':False,'reason':'partial_larger_than_manifest','attempts':attempts}
        before=tmp.stat().st_size if tmp.exists() else 0
        t=time.monotonic()
        with (O/(part['name']+'.log')).open('a') as log:
            proc=subprocess.run([
                'curl','-4','--http1.1','--config','-','--resolve','release-assets.githubusercontent.com:443:'+CDN_IP,'--proto','=https',
                '--fail','--silent','--show-error','--connect-timeout','15',
                '--max-time','1200','--speed-time','120','--speed-limit','16384',
                '--continue-at','-','--output',str(tmp),
                '--write-out','HTTP %{http_code} bytes %{size_download} rate %{speed_download}\n'],
                input='url = "'+link['url']+'"\n',text=True,stdout=log,stderr=subprocess.STDOUT)
        after=tmp.stat().st_size if tmp.exists() else 0
        attempts.append({'attempt':attempt,'curl_exit':proc.returncode,'bytes_before':before,
                         'bytes_after':after,'elapsed_s':time.monotonic()-t})
        if after==part['size']:
            if sha(tmp)!=part['sha256']:
                return {'name':part['name'],'ok':False,'reason':'sha256_mismatch','attempts':attempts}
            tmp.replace(dst)
            return {'name':part['name'],'ok':True,'bytes':after,'attempts':attempts}
        if proc.returncode not in [5,6,7,18,22,28,35,52,55,56]:
            break
    return {'name':part['name'],'ok':False,'reason':'bounded_attempts_exhausted',
            'bytes':tmp.stat().st_size if tmp.exists() else 0,'attempts':attempts}

def status(state):
    sizes={}
    for part in parts:
        sizes[part['name']]=min(part['size'],max(
            (D/part['name']).stat().st_size if (D/part['name']).exists() else 0,
            (D/(part['name']+'.partial')).stat().st_size if (D/(part['name']+'.partial')).exists() else 0))
    value={'state':state,'pid':os.getpid(),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'elapsed_s':time.monotonic()-started,'bytes_present':sum(sizes.values()),
           'total_bytes':sum(p['size'] for p in parts),'part_bytes':sizes,
           'verified_parts':sum(p['name'] in cached_valid or results.get(p['name'],{}).get('ok',False) for p in parts),'total_parts':len(parts),
           'results':list(results.values()),'api_calls':0,'model_versions_changed':False,'official_dns_ip_selected':CDN_IP,'system_dns_changed':False}
    temp=O/'status.tmp';temp.write_text(json.dumps(value,indent=2));temp.replace(O/'status.json')

with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
    futures={pool.submit(get,p):p for p in parts}
    while futures:
        done,_=concurrent.futures.wait(futures,timeout=10,return_when=concurrent.futures.FIRST_COMPLETED)
        for future in done:
            part=futures.pop(future)
            try:row=future.result()
            except Exception as exc:row={'name':part['name'],'ok':False,'reason':type(exc).__name__}
            results[part['name']]=row
            print(json.dumps(row),flush=True)
        status('downloading')
status('verified_complete' if all(x['ok'] for x in results.values()) else 'needs_review')
