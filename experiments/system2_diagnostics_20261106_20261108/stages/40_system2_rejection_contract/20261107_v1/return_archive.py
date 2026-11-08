"""Verified execution-host -> local pipe -> lab migration, never outside project."""
import datetime
import json
from pathlib import Path
import shlex
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'rgb_supplement_20261105'))
from remote import CLOUD,LAB
HERE=Path(__file__).resolve().parent
C='/mnt/data/physical-RSI/result/43_rejection_contract_20261107'
L='/mnt/data/joey_tr/physical-RSI/result/40_system2_rejection_contract/20261107_v1'
D=L+'/native-validation'
def call(host,script,sudo=False,timeout=60):
    p=subprocess.run(host+[('sudo -n ' if sudo else '')+'python3 -B -c '+shlex.quote(script)],capture_output=True,text=True,timeout=timeout)
    if p.returncode:raise RuntimeError(p.stderr[-2000:])
    return json.loads(p.stdout)
source=call(CLOUD,f'''from pathlib import Path
import json,hashlib
r=Path({C!r});p=r/'migration/source-manifest.json';m=json.loads(p.read_text());print(json.dumps(dict(manifest_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),files=m['file_count'],logical_bytes=m['logical_bytes'])))''',True)
call(LAB,f'''from pathlib import Path
import json
d=Path({D!r});s=Path({(D+'.incoming')!r});assert not d.exists();assert not s.exists(),'Partial transfer requires resume audit';s.mkdir();print(json.dumps({{'staging':str(s)}}))''')
record=dict(state='transferring',started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source=C,destination=D,route='cloud -> local SSH pipe -> lab',**source)
(HERE/'return-status.json').write_text(json.dumps(record,indent=2)+'\n')
subprocess.run([sys.executable,str(HERE/'batch_archive.py')],check=True,timeout=3600)
print((HERE/'return-status.json').read_text())
