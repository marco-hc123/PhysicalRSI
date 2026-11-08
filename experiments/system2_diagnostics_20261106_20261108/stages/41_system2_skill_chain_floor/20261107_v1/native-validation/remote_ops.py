import sys,shlex,subprocess,json,base64,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parent/'rgb_supplement_20261105'))
from remote import LAB,CLOUD
L='/mnt/data/joey_tr/physical-RSI/result/41_system2_skill_chain_floor/20261107_v1'
C='/mnt/data/physical-RSI/result/44_skill_chain_floor_20261107'
PYTHON='/mnt/data/physical-RSI/models/skill-assets/implementations/openpi/.venv/bin/python'
def call(host,code,sudo=False,payload=None,timeout=80):
 p=subprocess.run(host+[('sudo -n ' if sudo else '')+'python3 -B -c '+shlex.quote(code)],input=payload,capture_output=True,text=True,timeout=timeout)
 if p.returncode:raise RuntimeError(p.stderr[-4000:])
 return p.stdout

def upload(host,root,paths,sudo=False):
 rows=[dict(path=str(p.relative_to(H)),content=base64.b64encode(p.read_bytes()).decode(),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths]
 return call(host,f'''import json,base64,hashlib,sys
from pathlib import Path
r=Path({root!r});r.mkdir(parents=True,exist_ok=True)
for row in json.load(sys.stdin):
 p=r/row['path'];assert p.resolve().is_relative_to(r.resolve());b=base64.b64decode(row['content']);assert hashlib.sha256(b).hexdigest()==row['sha256']
 if p.exists():assert p.read_bytes()==b, 'Would overwrite existing '+str(p)
 else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
print(json.dumps(dict(files=len(json.loads('[]')))))''',sudo,json.dumps(rows))
