"""Complete one preserved public part using range transport and whole-part SHA."""
from pathlib import Path
import concurrent.futures
import datetime
import hashlib
import json
import math
import shutil
import subprocess
import time

R=Path('/mnt/data/physical-RSI')
A=R/'models/official-v4'
O=R/'result/31_rgb_supplement_20261105/resource-download-weights'
manifest=json.loads((A/'assets.json').read_text())
part=next(p for a in manifest['assets'] for p in a['parts'] if p['name']=='pi05-weights.tar.part007')
source=A/'.transport-repairs'/(part['name']+'.fresh-query.partial')
destination=A/'.downloads'/part['name']
work=A/'.transport-repairs/final-tail';work.mkdir(exist_ok=True)

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as stream:
        for block in iter(lambda:stream.read(8*1024*1024),b''):h.update(block)
    return h.hexdigest()

if destination.exists():
    assert destination.stat().st_size==part['size'] and sha(destination)==part['sha256']
    print('Canonical final part already verified');raise SystemExit(0)

prefix=source.stat().st_size
assert prefix==980972977
remaining=part['size']-prefix
chunk=math.ceil(remaining/8)
started=time.monotonic()

def one(i):
    start=prefix+i*chunk;end=min(part['size']-1,start+chunk-1)
    target=work/('tail-'+str(i)+'.bin')
    if target.exists() and target.stat().st_size==end-start+1:
        return dict(index=i,start=start,end=end,bytes=target.stat().st_size,cached=True,ok=True)
    t=time.monotonic()
    c=subprocess.run(['curl','-fL','--proto','=https','--proto-redir','=https','--connect-timeout','10',
        '--max-time','180','--speed-time','45','--speed-limit','16384','--range',str(start)+'-'+str(end),
        '-sS','-o',str(target),'-w','%{http_code}','https://ghfast.top/'+part['url']],capture_output=True,text=True)
    ok=c.returncode==0 and c.stdout=='206' and target.stat().st_size==end-start+1
    row=dict(index=i,start=start,end=end,bytes=target.stat().st_size if target.exists() else 0,exit_code=c.returncode,http_code=c.stdout,elapsed_s=time.monotonic()-t,ok=ok)
    (work/('tail-'+str(i)+'.json')).write_text(json.dumps(row,indent=2))
    return row

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    rows=list(pool.map(one,range(8)))
report=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),part=part['name'],prefix_bytes=prefix,remaining_bytes=remaining,ranges=rows,elapsed_s=time.monotonic()-started,verified=False)
if all(x['ok'] for x in rows):
    assembled=work/'assembled.tar.part007'
    shutil.copyfile(source,assembled)
    with assembled.open('ab') as stream:
        for i in range(8):
            with (work/('tail-'+str(i)+'.bin')).open('rb') as tail:shutil.copyfileobj(tail,stream)
    assert assembled.stat().st_size==part['size']
    report['actual_sha256']=sha(assembled)
    assert report['actual_sha256']==part['sha256'],'Reassembled public part failed whole-part SHA; all evidence preserved'
    report['verified']=True
    if destination.exists():assert sha(destination)==part['sha256']
    else:assembled.rename(destination)
(O/'targeted-final-tail.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='ranges'}),flush=True)
assert report['verified'],'Incomplete tail ranges; preserve prefix and pieces for bounded resume'
