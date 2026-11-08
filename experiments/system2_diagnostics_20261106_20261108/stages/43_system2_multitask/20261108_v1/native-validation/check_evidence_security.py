"""Content scan for credential-shaped strings; never prints matching content."""
import datetime,hashlib,json,re
from pathlib import Path
O=Path(__file__).resolve().parent
patterns={
 'project_api_key':re.compile(rb'sk-proj-[A-Za-z0-9_-]{32,}'),
 'workspace_api_key':re.compile(rb'sk-ws-[A-Za-z0-9._-]{24,}'),
 'private_key':re.compile(rb'-----BEGIN (?:OPENSSH |RSA |EC )?PRIVATE KEY-----'),
 'literal_bearer':re.compile(rb'Bearer [A-Za-z0-9_-]{32,}')
}
extensions={'.py','.json','.jsonl','.txt','.log','.md','.yaml','.yml','.csv','.sh','.toml','.ini','.cfg'}
files=0;total=0;findings=[]
for p in sorted(O.rglob('*')):
 if not p.is_file() or p.is_symlink() or p.suffix not in extensions or p.name=='redaction-scan.json':continue
 if '__pycache__' in p.parts:continue
 found=set();tail=b''
 with p.open('rb') as f:
  while True:
   b=f.read(1048576)
   if not b:break
   total+=len(b);s=tail+b
   for name,regex in patterns.items():
    if regex.search(s):found.add(name)
   tail=s[-512:]
 files+=1
 if found:findings.append(dict(path=str(p.relative_to(O)),classes=sorted(found)))
out=dict(state='passed' if not findings else 'blocked',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files_scanned=files,bytes_scanned=total,findings=findings,scope='Credential-shaped strings in project text evidence only; no contents or secrets printed. Does not inspect binary videos, weights, or external files.')
(O/'redaction-scan.json').write_text(json.dumps(out,indent=2)+'\n')
assert not findings,[(x['path'],x['classes']) for x in findings]
print(json.dumps({k:v for k,v in out.items() if k!='findings'}))
