"""Materialize public Git LFS pointers; verify each payload before replacement."""
import concurrent.futures,hashlib,json,re,sys,time,urllib.request
from pathlib import Path
O=Path(__file__).resolve().parent
A=Path('/mnt/data/physical-RSI/assets/robodojo-complete-source')
D=O/'asset-downloads';D.mkdir(exist_ok=True)
mode=sys.argv[1]
if mode=='metadata':paths=list((A/'Assets/Object/RoboDojo').rglob('metadata.json'))
else:
    assert mode=='selected'
    roots=json.loads((O/'selected-asset-roots.json').read_text())
    paths=[]
    for name in roots:
        p=(A/name).resolve();assert p.is_relative_to(A) and p.is_dir()
        paths.extend(x for x in p.rglob('*') if x.is_file())
rows=[]
for p in sorted(set(paths)):
    if p.stat().st_size>500:continue
    b=p.read_bytes()
    if not b.startswith(b'version https://git-lfs.github.com/spec/v1'):continue
    t=b.decode();oid=re.search(r'oid sha256:([a-f0-9]{64})',t)[1];size=int(re.search(r'size (\d+)',t)[1])
    rows.append(dict(path=str(p.relative_to(A)),oid=oid,size=size,pointer=t))
stamp=str(time.time_ns());(D/(mode+'-'+stamp+'-pointers.json')).write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(dict(state='planned',mode=mode,files=len(rows),bytes=sum(x['size'] for x in rows))),flush=True)
results=[]
def save():
    p=D/(mode+'-'+stamp+'-results.json');t=p.with_suffix('.tmp');t.write_text(json.dumps(results,indent=2)+'\n');t.replace(p)
def fetch(row,url):
    assert url.startswith('https://')
    url=url.replace('https://us.aws.cdn.hf-mirror.org/','https://us.aws.cdn.hf.co/')
    path=A/row['path'];temp=D/(row['oid']+'.partial');h=hashlib.sha256();count=0
    try:
        with urllib.request.urlopen(url,timeout=90) as response,temp.open('wb') as out:
            while True:
                b=response.read(1024*1024)
                if not b:break
                out.write(b);h.update(b);count+=len(b)
        assert count==row['size'] and h.hexdigest()==row['oid'],'Payload digest mismatch'
        assert path.read_text()==row['pointer'],'Original pointer changed'
        temp.replace(path)
        return dict(path=row['path'],sha256=row['oid'],bytes=count,state='verified')
    except Exception as e:
        return dict(path=row['path'],state='failed',error_type=type(e).__name__)
for start in range(0,len(rows),100):
    batch=rows[start:start+100]
    payload=dict(operation='download',transfers=['basic'],objects=[dict(oid=r['oid'],size=r['size']) for r in batch])
    request=urllib.request.Request('https://hf-mirror.com/datasets/RoboDojo-Benchmark/RoboDojo.git/info/lfs/objects/batch',data=json.dumps(payload).encode(),headers={'Content-Type':'application/vnd.git-lfs+json','Accept':'application/vnd.git-lfs+json'})
    with urllib.request.urlopen(request,timeout=90) as response:answer=json.load(response)
    objects={r['oid']:r for r in answer['objects']}
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        jobs=[]
        for row in batch:
            obj=objects[row['oid']]
            if 'actions' not in obj:results.append(dict(path=row['path'],state='no_download_action'))
            else:jobs.append(pool.submit(fetch,row,obj['actions']['download']['href']))
        for job in concurrent.futures.as_completed(jobs):results.append(job.result());save()
    print(json.dumps(dict(mode=mode,completed=len(results),verified=sum(x['state']=='verified' for x in results),planned=len(rows))),flush=True)
save()
if any(r['state']!='verified' for r in results):raise RuntimeError('Some public assets remain unavailable; see sanitized results')
